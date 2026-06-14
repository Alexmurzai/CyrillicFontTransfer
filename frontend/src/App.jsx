import { useState, useCallback, useEffect } from 'react';
import { Type, LogOut, Settings, Layers, Search } from 'lucide-react';
import Sidebar from './components/Sidebar/Sidebar';
import FontFeed from './components/FontFeed/FontFeed';
import ImageUploader from './components/ImageUploader/ImageUploader';
import SegmentationGallery from './components/SegmentationGallery/SegmentationGallery';
import Slider from './components/Slider/Slider';
import { useRecognition } from './hooks/useRecognition';
import { useI18n } from './context/I18nContext';
import { useAuth } from './context/AuthContext';
import AuthModal from './components/Auth/AuthModal';
import PricingModal from './components/Pricing/PricingModal';
import './App.css';

function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== 'undefined' ? window.innerWidth <= breakpoint : false
  );
  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const handler = (e) => setIsMobile(e.matches);
    mql.addEventListener('change', handler);
    setIsMobile(mql.matches);
    return () => mql.removeEventListener('change', handler);
  }, [breakpoint]);
  return isMobile;
}

export default function App() {
  const { t, lang, toggleLang } = useI18n();
  const {
    token, user, fingerprint, anonymousUsage,
    logout, setShowAuthModal, setShowPricingModal
  } = useAuth();

  const {
    matches, charImages, total, visibleCount, health,
    isLoading, isUpdating, error, recognize, showMore, updatePreview, clear,
  } = useRecognition();

  const [activeCategory, setActiveCategory] = useState('all');
  const isMobile = useIsMobile();

  // Mobile state
  const [mobileSheet, setMobileSheet] = useState(null); // null | 'settings' | 'segments'

  // Shared sidebar state (used both in desktop sidebar and mobile bottom sheet)
  const [imageFile, setImageFile] = useState(null);
  const [previewText, setPreviewText] = useState('АБВГДЕabc');
  const [letterSpacing, setLetterSpacing] = useState(0);
  const [wordSpacing, setWordSpacing] = useState(20);
  const [category, setCategory] = useState('all');

  const handleImageSelect = useCallback((file) => {
    setImageFile(file);
    if (!file) {
      clear();
    }
  }, [clear]);

  // Intercept limit errors
  useEffect(() => {
    if (error === 'limit_exceeded_anonymous' || error === 'limit_exceeded_registered') {
      if (!token) {
        setShowAuthModal(true);
      } else {
        setShowPricingModal(true);
      }
    }
  }, [error, token, setShowAuthModal, setShowPricingModal]);

  const getOptions = useCallback(() => ({
    previewText,
    letterSpacing,
    wordSpacing,
    category,
  }), [previewText, letterSpacing, wordSpacing, category]);

  const handleRecognize = useCallback((imgFile, options) => {
    setActiveCategory(options?.category || category || 'all');
    recognize(imgFile || imageFile, {
      ...(options || getOptions()),
      token,
      fingerprint
    });
    if (isMobile) setMobileSheet(null);
  }, [recognize, token, fingerprint, imageFile, category, getOptions, isMobile]);

  const handleMobileSearch = useCallback(() => {
    if (!imageFile || isLoading) return;
    handleRecognize(imageFile, getOptions());
  }, [imageFile, isLoading, handleRecognize, getOptions]);

  const handlePreviewUpdate = useCallback((opts) => {
    updatePreview(opts);
  }, [updatePreview]);

  const hasResults = matches.length > 0;
  const isLimitError = error === 'limit_exceeded_anonymous' || error === 'limit_exceeded_registered';
  const isOnline = health?.engine_loaded === true;
  const freeRemaining = Math.max(0, 5 - anonymousUsage);

  // Close mobile sheet on backdrop click
  const closeMobileSheet = useCallback(() => setMobileSheet(null), []);

  return (
    <div className="app-wrapper">
      <AuthModal />
      <PricingModal />

      {/* ── Header ── */}
      <header className={`app-header ${isMobile ? 'app-header--mobile' : ''}`}>
        <div className="header-brand">MOCT</div>

        {!isMobile && (
          <div className="header-title-centered">
            {t('brand_subtitle')}
          </div>
        )}

        <div className="header-actions">
          <button className="btn-lang" onClick={toggleLang}>
            {lang === 'ru' ? 'EN' : 'RU'}
          </button>

          {!token ? (
            <>
              <span className="usage-info">
                {isMobile
                  ? (freeRemaining > 0 ? t('mobile_free_tries', { remaining: freeRemaining }) : t('mobile_free_tries_used'))
                  : t('limit_anonymous', { used: anonymousUsage })
                }
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
              {!isMobile && (
                <button className="btn-upgrade" onClick={() => setShowPricingModal(true)}>
                  {t('btn_upgrade')}
                </button>
              )}
              <button className="btn-logout" onClick={logout} title="Log out">
                <LogOut size={18} />
              </button>
            </>
          )}
        </div>
      </header>

      {/* ── Desktop Sidebar ── */}
      {!isMobile && (
        <Sidebar
          onRecognize={handleRecognize}
          onPreviewUpdate={handlePreviewUpdate}
          onClear={clear}
          charImages={charImages}
          isLoading={isLoading}
          error={isLimitError ? null : error}
          health={health}
        />
      )}

      {/* ── Marquee (desktop only) ── */}
      {!isMobile && (
        <div className="top-marketing-bar">
          <div className="marquee-content">
            <span>{t('marketing_top')}</span>
            <span>{t('marketing_top')}</span>
          </div>
        </div>
      )}

      {/* ── Main Content ── */}
      <div className={`app ${isMobile ? 'app--mobile' : ''}`}>
        {/* Loading overlay */}
        {isLoading && (
          <div className="loading-overlay">
            <div className="loading-spinner" />
            <span className="loading-text">{t('loading_analyzing')}</span>
          </div>
        )}

        {/* ── Mobile: Inline Upload + Search ── */}
        {isMobile && (
          <div className={`mobile-upload-section ${hasResults ? 'mobile-upload-section--sticky' : ''}`}>
            <ImageUploader onImageSelect={handleImageSelect} disabled={isLoading} />
            {!hasResults && (
              <button
                className="mobile-search-btn"
                onClick={handleMobileSearch}
                disabled={!imageFile || isLoading}
              >
                <Search size={18} strokeWidth={2} />
                {isLoading ? t('searching') : t('btn_find_matches')}
              </button>
            )}

            {/* Error */}
            {error && !isLimitError && (
              <div className="error-msg" style={{ margin: '0 0 8px 0' }}>{error}</div>
            )}
          </div>
        )}

        {/* Feed */}
        <main className="feed" id="feed">
          {isMobile && hasResults && charImages.length > 0 && (
            <div className="mobile-feed-segments">
              <SegmentationGallery images={charImages} />
            </div>
          )}

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
              {!isMobile && <Type size={80} strokeWidth={0.5} className="empty-state__icon" />}
              <h1 className="empty-state__title">{t('title_main')}</h1>
              <p className="empty-state__text">
                {isMobile ? t('mobile_empty_subtitle') : t('empty_subtitle')}
                <br/><br/>
                {health ? t('fonts_status_format', { count: health.fonts_count, device: health.device }) : t('fonts_status_format', { count: 6231, device: 'cuda' })}
              </p>

              {/* Mobile promo inline */}
              {isMobile && (
                <div className="mobile-promo-inline">
                  <div className="mobile-promo-badge">{t('promo_title')}</div>
                  <span className="mobile-promo-text">{t('promo_text')}</span>
                  <button className="mobile-promo-btn" onClick={() => setShowPricingModal(true)}>{t('claim_promo')}</button>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* ── Mobile Bottom Navigation ── */}
      {isMobile && (
        <nav className="mobile-bottom-nav">
          <button
            className={`mobile-bottom-nav__btn ${mobileSheet === 'settings' ? 'mobile-bottom-nav__btn--active' : ''}`}
            onClick={() => setMobileSheet(mobileSheet === 'settings' ? null : 'settings')}
          >
            <Settings size={20} />
            <span>{t('mobile_settings')}</span>
          </button>
          <div className="mobile-bottom-nav__status">
            <span className={`status-dot-mini ${isOnline ? '' : 'status-dot-mini--offline'}`} />
            <span>{isOnline ? t('status_online') : t('status_offline')}</span>
          </div>
          <button
            className={`mobile-bottom-nav__btn ${mobileSheet === 'segments' ? 'mobile-bottom-nav__btn--active' : ''}`}
            onClick={() => setMobileSheet(mobileSheet === 'segments' ? null : 'segments')}
          >
            <Layers size={20} />
            <span>{t('mobile_segments')}</span>
          </button>
        </nav>
      )}

      {/* ── Mobile Bottom Sheet ── */}
      {isMobile && mobileSheet && (
        <>
          <div className="mobile-sheet-backdrop" onClick={closeMobileSheet} />
          <div className="mobile-bottom-sheet">
            <div className="mobile-sheet__handle" onClick={closeMobileSheet}>
              <div className="mobile-sheet__handle-bar" />
            </div>

            {mobileSheet === 'settings' && (
              <div className="mobile-sheet__content">
                <h3 className="mobile-sheet__title">{t('typography_settings')}</h3>

                {/* Preview text */}
                <div className="mobile-sheet__field">
                  <input
                    type="text"
                    className="text-input text-input--mobile"
                    value={previewText}
                    onChange={(e) => setPreviewText(e.target.value)}
                    placeholder={t('placeholder_preview')}
                  />
                </div>

                {/* Sliders */}
                <Slider
                  label={t('letter_spacing')}
                  value={letterSpacing}
                  min={-20}
                  max={50}
                  onChange={(v) => {
                    setLetterSpacing(v);
                    updatePreview({ text: previewText, letterSpacing: v, wordSpacing });
                  }}
                  id="mobile-letter-spacing"
                />
                <Slider
                  label={t('word_spacing')}
                  value={wordSpacing}
                  min={0}
                  max={100}
                  onChange={(v) => {
                    setWordSpacing(v);
                    updatePreview({ text: previewText, letterSpacing, wordSpacing: v });
                  }}
                  id="mobile-word-spacing"
                />

                {/* Promo */}
                <div className="mobile-sheet__promo">
                  <div className="mobile-sheet__promo-badge">{t('promo_title')}</div>
                  <span className="mobile-sheet__promo-text">{t('promo_text')}</span>
                  <button className="mobile-sheet__promo-btn" onClick={() => {
                    setShowPricingModal(true);
                    setMobileSheet(null);
                  }}>{t('claim_promo')}</button>
                </div>

                {/* Font count footer */}
                <div className="mobile-sheet__footer">
                  <span>{health ? t('fonts_status_format', { count: health.fonts_count, device: health.device }) : t('fonts_status_format', { count: 6231, device: 'cuda' })}</span>
                </div>
              </div>
            )}

            {mobileSheet === 'segments' && (
              <div className="mobile-sheet__content">
                <h3 className="mobile-sheet__title">{t('segmentation')}</h3>
                <SegmentationGallery images={charImages} />
              </div>
            )}
          </div>
        </>
      )}

      {/* ── Fixed Footer Status Bar (desktop only) ── */}
      {!isMobile && (
        <footer className="app-footer">
          <div className="footer-left">
            © 2026 MOCT AI Engine
          </div>
          <div className="footer-right">
            <span className={`footer-status ${isOnline ? 'footer-status--connected' : 'footer-status--info'}`}>
              {isOnline ? t('status_bar_connected') : t('status_bar_offline')}
            </span>
            <span className="footer-status footer-status--info">
              {t('status_bar_latency')}
            </span>
            <span className="footer-status footer-status--info">
              {t('status_bar_api')}
            </span>
          </div>
        </footer>
      )}
    </div>
  );
}
