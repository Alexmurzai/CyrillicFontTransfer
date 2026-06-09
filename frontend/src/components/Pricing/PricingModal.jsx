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
    { id: "pack_20", title_key: "pkg_20_title", desc_key: "pkg_20_desc", price_rub: 290, price_usd: 3 },
    { id: "pack_100", title_key: "pkg_100_title", desc_key: "pkg_100_desc", price_rub: 990, price_usd: 10 },
    { id: "sub_week", title_key: "pkg_week_title", desc_key: "pkg_week_desc", price_rub: 1490, price_usd: 15 },
    { id: "sub_month", title_key: "pkg_month_title", desc_key: "pkg_month_desc", price_rub: 3990, price_usd: 40 },
    { id: "sub_year", title_key: "pkg_year_title", desc_key: "pkg_year_desc", price_rub: 29000, price_usd: 300 },
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
        alert(t('payment_success'));
        window.location.reload();
      }
    } catch (e) {
      alert(t('payment_failed'));
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
              <h3>{t(pkg.title_key)}</h3>
              <p className="desc">{t(pkg.desc_key)}</p>
              <div className="price">
                {t('currency')} {lang === 'ru' ? pkg.price_rub : pkg.price_usd}
              </div>
              <button 
                className="btn-primary" 
                onClick={() => handleBuy(pkg)}
                disabled={loading}
              >
                {t('buy_with', { gateway: lang === 'ru' ? t('gateway_ru') : t('gateway_en') })}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
