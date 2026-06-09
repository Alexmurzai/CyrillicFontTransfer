import { useState, useCallback, useRef, useEffect } from 'react';
import { Settings, Search } from 'lucide-react';
import { getApiUrl, setApiUrl } from '../../api/hfr';
import { useI18n } from '../../context/I18nContext';
import ImageUploader from '../ImageUploader/ImageUploader';
import SegmentationGallery from '../SegmentationGallery/SegmentationGallery';
import Slider from '../Slider/Slider';
import './Sidebar.css';

export default function Sidebar({
  onRecognize,
  onPreviewUpdate,
  charImages,
  isLoading,
  error,
  health,
}) {
  const { t } = useI18n();
  const [imageFile, setImageFile] = useState(null);
  const [previewText, setPreviewText] = useState('АБВГДЕabc');
  const [letterSpacing, setLetterSpacing] = useState(0);
  const [wordSpacing, setWordSpacing] = useState(20);
  const [category, setCategory] = useState('all');
  const [apiUrl, setApiUrlState] = useState(getApiUrl());
  const [showSettings, setShowSettings] = useState(false);
  const prevSettingsRef = useRef(null);

  // Опции для поиска
  const getOptions = useCallback(() => ({
    previewText,
    letterSpacing,
    wordSpacing,
    category,
  }), [previewText, letterSpacing, wordSpacing, category]);

  // Поиск
  const handleSearch = useCallback(() => {
    if (!imageFile || isLoading) return;
    onRecognize?.(imageFile, getOptions());
  }, [imageFile, isLoading, onRecognize, getOptions]);

  // Смена API URL
  const handleApiUrlChange = (val) => {
    setApiUrlState(val);
    setApiUrl(val);
  };

  // Реагируем на изменения настроек превью (debounced через hook)
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

  // Enter для запуска поиска
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') handleSearch();
  }, [handleSearch]);

  const isOnline = health?.engine_loaded === true;

  return (
    <aside className="sidebar" id="sidebar">
      {/* Brand */}
      <div className="brand">
        <span className="brand__name">HFR</span>
        <span className="brand__version">v2.1</span>
      </div>
      <p className="brand__sub">{t('brand_subtitle')}</p>

      {/* Upload */}
      <div className="sidebar__section">
        <span className="section-label">{t('upload_section_title')}</span>
        <ImageUploader onImageSelect={setImageFile} disabled={isLoading} />
      </div>

      {/* Preview text */}
      <div className="sidebar__section">
        <span className="section-label">{t('demonstration_text')}</span>
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
      {error && <div className="error-msg">{error}</div>}

      {/* Segmentation */}
      <div className="sidebar__section">
        <span className="section-label">{t('segmentation')}</span>
        <SegmentationGallery images={charImages} />
      </div>

      {/* Spacing sliders */}
      <div className="sidebar__section">
        <span className="section-label">{t('typography_settings')}</span>
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

      <div className="divider" />

      {/* API Settings */}
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
              placeholder="https://hfr-alex-font.loca.lt"
            />
          </div>
        )}
      </div>

      <div className="divider" />

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
