import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import { getApiUrl } from '../../api/hfr';
import './PricingModal.css';

export default function PricingModal() {
  const { user, showPricingModal, setShowPricingModal } = useAuth();
  const { lang, t } = useI18n();
  
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [selectedPkg, setSelectedPkg] = useState(null);
  const [network, setNetwork] = useState('usdt_trc20');
  const [depositAddress, setDepositAddress] = useState('');
  const [paymentAmount, setPaymentAmount] = useState(0);
  const [txid, setTxid] = useState('');

  if (!showPricingModal) return null;

  const packages = [
    { id: "pack_20", title_key: "pkg_20_title", desc_key: "pkg_20_desc", price_rub: 290, price_usd: 3 },
    { id: "pack_100", title_key: "pkg_100_title", desc_key: "pkg_100_desc", price_rub: 990, price_usd: 10 },
    { id: "sub_week", title_key: "pkg_week_title", desc_key: "pkg_week_desc", price_rub: 1490, price_usd: 15 },
    { id: "sub_month", title_key: "pkg_month_title", desc_key: "pkg_month_desc", price_rub: 3990, price_usd: 40 },
    { id: "sub_year", title_key: "pkg_year_title", desc_key: "pkg_year_desc", price_rub: 29000, price_usd: 300 },
  ];

  const handleCreateIntent = async (pkg) => {
    setLoading(true);
    const apiBase = getApiUrl();
    try {
      const res = await fetch(`${apiBase}/api/payments/create`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Bypass-Tunnel-Reminder': 'true',
          'X-Pinggy-No-Screen': 'true'
        },
        body: JSON.stringify({
          user_id: user?.id || 1,
          package_id: pkg.id,
          gateway: 'htx',
          network: network
        })
      });
      const data = await res.json();
      
      if (data.status === 'pending' && data.deposit_address) {
        setDepositAddress(data.deposit_address);
        setPaymentAmount(data.amount);
        setSelectedPkg(pkg);
        setStep(2);
      } else {
        alert(data.detail || t('payment_failed'));
      }
    } catch (e) {
      alert(t('payment_failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!txid.trim()) {
      alert('Please enter a Transaction Hash (TxID)');
      return;
    }
    setLoading(true);
    const apiBase = getApiUrl();
    try {
      const res = await fetch(`${apiBase}/api/payments/verify`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Bypass-Tunnel-Reminder': 'true',
          'X-Pinggy-No-Screen': 'true'
        },
        body: JSON.stringify({
          user_id: user?.id || 1,
          package_id: selectedPkg.id,
          txid: txid.trim(),
          network: network
        })
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        alert(t('payment_success'));
        window.location.reload();
      } else {
        alert(data.detail || t('payment_failed'));
      }
    } catch (e) {
      alert(t('payment_failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={() => { setShowPricingModal(false); setStep(1); }}>
      <div className="modal-content pricing-modal" onClick={e => e.stopPropagation()}>
        
        {step === 1 && (
          <>
            <h2>{t('pricing_title')}</h2>
            <div style={{marginBottom: '1rem'}}>
              <label style={{marginRight: '1rem'}}>Select Crypto Network:</label>
              <select value={network} onChange={(e) => setNetwork(e.target.value)} style={{padding: '0.5rem', borderRadius: '4px'}}>
                <option value="usdt_trc20">USDT (TRC20)</option>
                <option value="usdt_erc20">USDT (ERC20)</option>
                <option value="usdt_bep20">USDT (BEP20)</option>
              </select>
            </div>
            
            <div className="pricing-grid">
              {packages.map(pkg => (
                <div key={pkg.id} className="pricing-card">
                  <h3>{t(pkg.title_key)}</h3>
                  <p className="desc">{t(pkg.desc_key)}</p>
                  <div className="price">
                    {t('currency')} {lang === 'ru' ? pkg.price_rub : pkg.price_usd} (≈ {pkg.price_usd} USDT)
                  </div>
                  <button 
                    className="btn-primary" 
                    onClick={() => handleCreateIntent(pkg)}
                    disabled={loading}
                  >
                    Buy with HTX Crypto
                  </button>
                </div>
              ))}
            </div>
          </>
        )}

        {step === 2 && (
          <div className="payment-step2">
            <h2>Complete Payment via Crypto</h2>
            <p>Please send exactly <strong>{paymentAmount} USDT</strong> via <strong>{network.toUpperCase()}</strong> network to the address below:</p>
            <div style={{background: '#222', padding: '1rem', borderRadius: '8px', wordBreak: 'break-all', margin: '1rem 0', userSelect: 'all'}}>
              {depositAddress}
            </div>
            <p style={{fontSize: '0.9rem', color: '#999', marginBottom: '1rem'}}>
              After you send the funds, paste your Transaction Hash (TxID) below so we can verify the payment on the HTX exchange.
            </p>
            <input 
              type="text" 
              placeholder="Paste TxID (e.g. 0x... or T...)" 
              value={txid}
              onChange={(e) => setTxid(e.target.value)}
              style={{width: '100%', padding: '0.8rem', marginBottom: '1rem', background: '#333', color: '#fff', border: '1px solid #444', borderRadius: '4px'}}
            />
            <div style={{display: 'flex', gap: '1rem'}}>
              <button 
                className="btn-primary" 
                onClick={handleVerify}
                disabled={loading || !txid.trim()}
                style={{flex: 1}}
              >
                {loading ? 'Verifying...' : 'Verify Payment'}
              </button>
              <button 
                className="btn-secondary" 
                onClick={() => setStep(1)}
                disabled={loading}
                style={{flex: 1}}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
