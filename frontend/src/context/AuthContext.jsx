import React, { createContext, useState, useContext, useEffect } from 'react';
import fpPromise from '@fingerprintjs/fingerprintjs';
import { getApiUrl } from '../api/hfr';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('hfr_token'));
  const [user, setUser] = useState(null);
  const [fingerprint, setFingerprint] = useState(null);
  const [anonymousUsage, setAnonymousUsage] = useState(() => {
    return parseInt(localStorage.getItem('hfr_anon_usage') || '0', 10);
  });
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showPricingModal, setShowPricingModal] = useState(false);

  // Initialize fingerprint
  useEffect(() => {
    const initFingerprint = async () => {
      const fp = await fpPromise.load();
      const result = await fp.get();
      setFingerprint(result.visitorId);
    };
    initFingerprint();
  }, []);

  // Fetch user if token exists
  useEffect(() => {
    if (token) {
      localStorage.setItem('hfr_token', token);
      const apiBase = getApiUrl();
      fetch(`${apiBase}/api/auth/me?token=${token}`)
        .then(res => {
          if (!res.ok) throw new Error('Invalid token');
          return res.json();
        })
        .then(data => setUser(data))
        .catch(() => logout());
    } else {
      localStorage.removeItem('hfr_token');
      setUser(null);
    }
  }, [token]);

  const login = async (email, password) => {
    const apiBase = getApiUrl();
    const res = await fetch(`${apiBase}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) throw new Error('Login failed');
    const data = await res.json();
    setToken(data.access_token);
    setUser({ balance: data.balance, subscription_end: data.subscription_end });
  };

  const register = async (email, password) => {
    const apiBase = getApiUrl();
    const res = await fetch(`${apiBase}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) throw new Error('Registration failed');
    const data = await res.json();
    setToken(data.access_token);
    setUser({ balance: data.balance, subscription_end: data.subscription_end });
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const incrementAnonymousUsage = () => {
    const newVal = anonymousUsage + 1;
    setAnonymousUsage(newVal);
    localStorage.setItem('hfr_anon_usage', newVal.toString());
  };

  const decrementBalance = () => {
    if (user && user.balance > 0) {
      setUser(prev => ({ ...prev, balance: prev.balance - 1 }));
    }
  };

  return (
    <AuthContext.Provider value={{
      token, user, fingerprint, anonymousUsage,
      login, register, logout, 
      incrementAnonymousUsage, decrementBalance,
      showAuthModal, setShowAuthModal,
      showPricingModal, setShowPricingModal
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
