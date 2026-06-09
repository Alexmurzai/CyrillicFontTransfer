import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useI18n } from '../../context/I18nContext';
import './AuthModal.css';

export default function AuthModal() {
  const { login, register, showAuthModal, setShowAuthModal } = useAuth();
  const { t } = useI18n();
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!showAuthModal) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password);
      } else {
        await login(email, password);
      }
      setShowAuthModal(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={() => setShowAuthModal(false)}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>{isRegister ? t('btn_register') : t('btn_login')}</h2>
        {error && <div className="modal-error">{error}</div>}
        
        <form onSubmit={handleSubmit} className="auth-form">
          <input 
            type="email" 
            placeholder="Email" 
            value={email} 
            onChange={e => setEmail(e.target.value)} 
            required 
          />
          <input 
            type="password" 
            placeholder="Password" 
            value={password} 
            onChange={e => setPassword(e.target.value)} 
            required 
          />
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? '...' : (isRegister ? t('btn_register') : t('btn_login'))}
          </button>
        </form>
        
        <div className="modal-switch">
          <button type="button" onClick={() => setIsRegister(!isRegister)} className="btn-text">
            {isRegister ? t('auth_switch_to_login') : t('auth_switch_to_register')}
          </button>
        </div>
      </div>
    </div>
  );
}
