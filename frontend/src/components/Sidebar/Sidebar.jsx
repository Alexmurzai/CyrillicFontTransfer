import { useState, useCallback, useRef, useEffect } from 'react';
import { Settings, Search } from 'lucide-react';
import { getApiUrl, setApiUrl } from '../../api/hfr';
import { useI18n } from '../../context/I18nContext';
import { useAuth } from '../../context/AuthContext';
import ImageUploader from '../ImageUploader/ImageUploader';
import SegmentationGallery from '../SegmentationGallery/SegmentationGallery';
import Slider from '../Slider/Slider';
import './Sidebar.css';

export default function Sidebar({
  onRecognize,
  onPreviewUpdate,
  onClear,
  charImages,
  isLoading,
  error,
  health,
}) {
  const { t } = useI18n();
  const { user } = useAuth();
  const getLocalizedError = useCallback((errStr) => {
    if (!errStr) return '';
    
    const directTranslation = t(errStr);
    if (directTranslation !== errStr) return directTranslation;
    
    if (errStr.startsWith('Ошибка сервера:')) {
      const status = errStr.split(':')[1]?.trim() || '';
      return t('err_server_error_status', { status });
    }
    
    if (errStr.startsWith('Ошибка обработки:')) {
      const details = errStr.substring('Ошибка обработки:'.length).trim();
      return t('err_processing_failed_details', { details });
    }
    
    if (errStr.includes('Backend недоступен') || errStr.includes('Failed to fetch')) {
      return t('Backend недоступен');
    }
    if (errStr.includes('Символы не найдены')) {
      return t('Символы не найдены на изображении. Попробуйте другое.');
    }
    if (errStr.includes('HFR Engine не загружен')) {
      return t('HFR Engine не загружен');
    }
    if (errStr.includes('Ошибка обновления превью')) {
      return t('Ошибка обновления превью');
    }
    if (errStr.includes('Ошибка скачивания')) {
      return t('Ошибка скачивания');
    }
    if (errStr.includes('Ошибка получения категорий')) {
      return t('Ошибка получения категорий');
    }
    
    return errStr;
  }, [t]);

  const [imageFile, setImageFile] = useState(null);
  const [previewText, setPreviewText] = useState('АБВГДЕabc');
  const [letterSpacing, setLetterSpacing] = useState(0);
  const [wordSpacing, setWordSpacing] = useState(20);
  const [category, setCategory] = useState('all');
  const [apiUrl, setApiUrlState] = useState(getApiUrl());

  const handleImageSelect = useCallback((file) => {
    setImageFile(file);
    if (!file) {
      onClear?.();
    }
  }, [onClear]);
  const [showSettings, setShowSettings] = useState(false);
  const prevSettingsRef = useRef(null);

  const getOptions = useCallback(() => ({
    previewText,
    letterSpacing,
    wordSpacing,
    category,
  }), [previewText, letterSpacing, wordSpacing, category]);

  const handleSearch = useCallback(() => {
    if (!imageFile || isLoading) return;
    onRecognize?.(imageFile, getOptions());
  }, [imageFile, isLoading, onRecognize, getOptions]);

  const handleApiUrlChange = (val) => {
    setApiUrlState(val);
    setApiUrl(val);
  };

  useEffect(() => {
    const key = `${previewText}|${letterSpacing}|${wordSpacing}`;
    if (prevSettingsRef.current && prevSettingsRef.current !== key) {
      onPreviewUpdate?.({
        text: previewText,
        letterSpacing,
        wordSpacing,
      });
    }
    prevSettingsRef.current = key;
  }, [previewText, letterSpacing, wordSpacing, onPreviewUpdate]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') handleSearch();
  }, [handleSearch]);

  const isOnline = health?.engine_loaded === true;

  return (
    <aside className="sidebar" id="sidebar">
      {/* Brand */}
      <div className="brand">
        <span className="brand__label">{t('ai_font_engine')}</span>
        <span className="brand__name">{t('toolbox_title')}</span>
        <span className="brand__version">v2.1-stable</span>
      </div>

      {/* Upload */}
      <div className="sidebar__section">
        <ImageUploader onImageSelect={handleImageSelect} disabled={isLoading} />
      </div>

      {/* Preview text */}
      <div className="sidebar__section">
        <div className="glass" style={{ padding: 'var(--sp-6)', borderRadius: 'var(--radius-xl)' }}>
          <input
            type="text"
            className="text-input"
            value={previewText}
            onChange={(e) => setPreviewText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('placeholder_preview')}
            id="preview-text-input"
          />
        </div>
      </div>

      {/* Search button */}
      <button
        className="search-btn"
        onClick={handleSearch}
        disabled={!imageFile || isLoading}
        id="search-btn"
      >
        <Search size={16} strokeWidth={2} />
        {isLoading ? t('searching') : t('btn_find_matches')}
      </button>

      {/* Error */}
      {error && <div className="error-msg">{getLocalizedError(error)}</div>}

      {/* Segmentation */}
      <div className="sidebar__section">
        <SegmentationGallery images={charImages} />
      </div>

      {/* Spacing sliders */}
      <div className="sidebar__section">
        <div className="glass" style={{ padding: 'var(--sp-6)', borderRadius: 'var(--radius-xl)' }}>
          <div className="slider-group">
            <Slider
              label={t('letter_spacing')}
              value={letterSpacing}
              min={-20}
              max={50}
              onChange={setLetterSpacing}
              id="letter-spacing-slider"
            />
            <Slider
              label={t('word_spacing')}
              value={wordSpacing}
              min={0}
              max={100}
              onChange={setWordSpacing}
              id="word-spacing-slider"
            />
          </div>
        </div>
      </div>

      {/* Promo */}
      <div className="sidebar__promo">
        <div className="sidebar__promo-info">
          <h4 className="sidebar__promo-title">{t('promo_title')}</h4>
          <p className="sidebar__promo-text">{t('promo_text')}</p>
        </div>
        <button className="sidebar__promo-btn">{t('claim_promo')}</button>
      </div>

      <div className="divider" />

      {/* API Settings */}
      {(window.location.hostname === 'localhost' || 
        window.location.hostname === '127.0.0.1' || 
        (user && (
          user.email === 'arhalexxx@gmail.com' || 
          user.email === 'test@example.com' || 
          user.email?.toLowerCase().includes('admin')
        ))) && (
        <div className="sidebar__section sidebar__section--settings">
          <button
            className={`settings-toggle ${showSettings ? 'settings-toggle--active' : ''}`}
            onClick={() => setShowSettings(!showSettings)}
            title={t('api_settings')}
          >
            <Settings size={14} />
            <span>{t('api_settings')}</span>
          </button>

          {showSettings && (
            <div className="settings-panel">
              <p className="settings-panel__hint">
                {t('api_settings_hint')}
              </p>
              <input
                type="text"
                className="text-input text-input--small"
                value={apiUrl}
                onChange={(e) => handleApiUrlChange(e.target.value)}
                placeholder="https://xxx.trycloudflare.com"
              />
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="sidebar-footer">
        <span className="sidebar-footer__text">
          {health 
            ? t('fonts_status_format', { count: health.fonts_count, device: health.device }) 
            : t('fonts_status_format', { count: 6231, device: 'cuda' })}
        </span>
        <div className="sidebar-footer__status">
          <span className={`status-dot ${isOnline ? '' : 'status-dot--offline'}`} />
          <span>{isOnline ? t('status_online') : t('status_offline')}</span>
        </div>
      </div>
    </aside>
  );
}
