import { useState, useCallback, useEffect } from 'react';
import { Type, Globe, LogOut, User as UserIcon } from 'lucide-react';
import Sidebar from './components/Sidebar/Sidebar';
import FontFeed from './components/FontFeed/FontFeed';
import { useRecognition } from './hooks/useRecognition';
import { useI18n } from './context/I18nContext';
import { useAuth } from './context/AuthContext';
import AuthModal from './components/Auth/AuthModal';
import PricingModal from './components/Pricing/PricingModal';
import './App.css';

export default function App() {
  const { t, lang, toggleLang } = useI18n();
  const { 
    token, user, fingerprint, anonymousUsage, 
    logout, setShowAuthModal, setShowPricingModal 
  } = useAuth();

  const {
    matches, charImages, total, visibleCount, health,
    isLoading, isUpdating, error, recognize, showMore, updatePreview,
  } = useRecognition();

  const [activeCategory, setActiveCategory] = useState('all');

  // Intercept limit errors
  useEffect(() => {
    if (error === 'limit_exceeded_anonymous' || error === 'limit_exceeded_registered') {
      if (!token) {
        setShowAuthModal(true); // Ask anonymous to register
      } else {
        setShowPricingModal(true); // Ask registered to upgrade
      }
    }
  }, [error, token, setShowAuthModal, setShowPricingModal]);

  const handleRecognize = useCallback((imageFile, options) => {
    setActiveCategory(options.category || 'all');
    recognize(imageFile, {
      ...options,
      token,
      fingerprint
    });
  }, [recognize, token, fingerprint]);

  const handlePreviewUpdate = useCallback((opts) => {
    updatePreview(opts);
  }, [updatePreview]);

  const hasResults = matches.length > 0;
  const isLimitError = error === 'limit_exceeded_anonymous' || error === 'limit_exceeded_registered';

  return (
    <div className="app-wrapper">
      <AuthModal />
      <PricingModal />

      {/* Top Marketing Bar */}
      <div className="top-marketing-bar">
        {t('marketing_top')}
      </div>

      {/* Header / Nav */}
      <header className="app-header">
        <div className="header-brand">
          {t('title_main')}
        </div>
        
        <div className="header-actions">
          <button className="btn-lang" onClick={toggleLang}>
            <Globe size={18} /> {lang.toUpperCase()}
          </button>
          
          {!token ? (
            <>
              <span className="usage-info">
                {t('limit_anonymous', { used: anonymousUsage })}
              </span>
              <button className="btn-login" onClick={() => setShowAuthModal(true)}>
                {t('btn_login')}
              </button>
            </>
          ) : (
            <>
              <span className="usage-info">
                {t('limit_registered', { balance: user?.balance || 0 })}
              </span>
              <button className="btn-upgrade" onClick={() => setShowPricingModal(true)}>
                {t('btn_upgrade')}
              </button>
              <button className="btn-logout" onClick={logout} title="Log out">
                <LogOut size={18} />
              </button>
            </>
          )}
        </div>
      </header>

      <div className="app">
        {/* Loading overlay */}
        {isLoading && (
          <div className="loading-overlay">
            <div className="loading-spinner" />
            <span className="loading-text">Нейросеть анализирует изображение...</span>
          </div>
        )}

        {/* Left: Sidebar */}
        <Sidebar
          onRecognize={handleRecognize}
          onPreviewUpdate={handlePreviewUpdate}
          charImages={charImages}
          isLoading={isLoading}
          error={isLimitError ? null : error}
          health={health}
        />

        {/* Right: Feed */}
        <main className="feed" id="feed">
          {hasResults ? (
            <FontFeed
              matches={matches}
              visibleCount={visibleCount}
              total={total}
              onShowMore={showMore}
              activeCategory={activeCategory}
              onCategoryChange={setActiveCategory}
            />
          ) : (
            <div className="empty-state">
              <Type size={80} strokeWidth={0.5} className="empty-state__icon" />
              <h1 className="empty-state__title">{t('title_main')}</h1>
              <p className="empty-state__text">
                {t('empty_subtitle')}
                <br/><br/>
                {health ? t('fonts_status_format', { count: health.fonts_count, device: health.device }) : t('fonts_status_format', { count: 6231, device: 'cuda' })}
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
