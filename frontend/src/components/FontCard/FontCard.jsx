import { Download } from 'lucide-react';
import { downloadFont } from '../../api/hfr';
import { useI18n } from '../../context/I18nContext';
import './FontCard.css';

function getScoreClass(pct) {
  if (pct >= 70) return 'font-card__score--high';
  if (pct >= 40) return 'font-card__score--mid';
  return 'font-card__score--low';
}

function shortenPath(fullPath) {
  const parts = fullPath.replace(/\\/g, '/').split('/');
  return parts.length > 2 ? '…/' + parts.slice(-2).join('/') : fullPath;
}

export default function FontCard({ match, rank, scale = 1, style }) {
  const { t } = useI18n();
  const {
    id,
    font_name,
    similarity_pct,
    preview_base64,
    font_path,
    font_category,
  } = match;

  const handleDownload = async (e) => {
    e.stopPropagation();
    try {
      await downloadFont(id, font_name);
    } catch (err) {
      console.error('Download error:', err);
    }
  };

  return (
    <div className="font-card fade-in" style={style} id={`font-card-${rank}`}>
      {/* Header: Name + Score + Download */}
      <div className="font-card__header">
        <div className="font-card__info">
          <h3 className="font-card__name" title={font_name}>{font_name}</h3>
          <div className="font-card__score-line">
            <span className="font-card__rank">#{rank}</span>
            <span className={`font-card__category font-card__category--${font_category}`}>
              {t('category_' + (font_category || 'unknown'))}
            </span>
            <span className={`font-card__score ${getScoreClass(similarity_pct)}`}>
              {similarity_pct.toFixed(1)}% {t('structural_match')}
            </span>
          </div>
        </div>
        <button className="font-card__download" onClick={handleDownload} title={t('download_title')}>
          <Download size={16} strokeWidth={2} />
          {t('download_btn')}
        </button>
      </div>

      {/* Preview */}
      <div className="font-card__preview">
        {preview_base64 ? (
          <img
            src={preview_base64}
            alt={t('alt_preview', { name: font_name })}
            loading="lazy"
            style={{ transform: `scale(${scale})` }}
          />
        ) : (
          <div className="skeleton" style={{ width: '80%', height: 60 }} />
        )}
      </div>

      {/* Path */}
      <div className="font-card__path-row">
        <span className="font-card__path" title={font_path}>
          {shortenPath(font_path)}
        </span>
      </div>
    </div>
  );
}
