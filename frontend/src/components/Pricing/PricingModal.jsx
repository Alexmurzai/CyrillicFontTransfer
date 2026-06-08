import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import './PricingModal.css';

export default function PricingModal() {
  const { user, showPricingModal, setShowPricingModal } = useAuth();
  const { lang, t } = useI18n();
  const [loading, setLoading] = useState(false);

  if (!showPricingModal) return null;

  const packages = [
    { id: "pack_20", title: "20 Searches", desc: "Pay as you go", price_rub: 290, price_usd: 3 },
    { id: "pack_100", title: "100 Searches", desc: "Best for occasional use", price_rub: 990, price_usd: 10 },
    { id: "sub_week", title: "1 Week Pro", desc: "Unlimited", price_rub: 1490, price_usd: 15 },
    { id: "sub_month", title: "1 Month Pro", desc: "Unlimited", price_rub: 3990, price_usd: 40 },
    { id: "sub_year", title: "1 Year Pro", desc: "Unlimited", price_rub: 29000, price_usd: 300 },
  ];

  const handleBuy = async (pkg) => {
    setLoading(true);
    const gateway = lang === 'ru' ? 'yookassa' : 'cryptomus';
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/payments/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user?.id || 1, // fallback for mock
          package_id: pkg.id,
          gateway
        })
      });
      const data = await res.json();
      
      // Simulate success for demo purposes
      if (data.payment_url) {
        await fetch(`http://127.0.0.1:8000/api/payments/mock-webhook?user_id=${user?.id || 1}&package_id=${pkg.id}`, { method: 'POST' });
        alert('Payment successful! Balance/subscription updated.');
        window.location.reload();
      }
    } catch (e) {
      alert("Payment failed");
    } finally {
      setLoading(false);
      setShowPricingModal(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={() => setShowPricingModal(false)}>
      <div className="modal-content pricing-modal" onClick={e => e.stopPropagation()}>
        <h2>{t('pricing_title')}</h2>
        
        <div className="pricing-grid">
          {packages.map(pkg => (
            <div key={pkg.id} className="pricing-card">
              <h3>{pkg.title}</h3>
              <p className="desc">{pkg.desc}</p>
              <div className="price">
                {t('currency')} {lang === 'ru' ? pkg.price_rub : pkg.price_usd}
              </div>
              <button 
                className="btn-primary" 
                onClick={() => handleBuy(pkg)}
                disabled={loading}
              >
                Buy with {lang === 'ru' ? 'MIR/YooKassa' : 'Crypto/MoonPay'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
