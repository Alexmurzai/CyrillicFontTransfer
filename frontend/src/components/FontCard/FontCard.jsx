import { Download } from 'lucide-react';
import { downloadFont } from '../../api/hfr';
import './FontCard.css';

const CATEGORY_LABELS = {
  serif: 'Serif',
  sans: 'Sans',
  script: 'Script',
  display: 'Display',
  mono: 'Mono',
  unknown: '—',
};

function getScoreClass(pct) {
  if (pct >= 70) return 'font-card__score--high';
  if (pct >= 40) return 'font-card__score--mid';
  return 'font-card__score--low';
}

function shortenPath(fullPath) {
  // Показываем только последние 2 сегмента
  const parts = fullPath.replace(/\\/g, '/').split('/');
  return parts.length > 2 ? '…/' + parts.slice(-2).join('/') : fullPath;
}

export default function FontCard({ match, rank, scale = 1, style }) {
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
      {/* Preview */}
      <div className="font-card__preview">
        {preview_base64 ? (
          <img
            src={preview_base64}
            alt={`Превью ${font_name}`}
            loading="lazy"
            style={{ transform: `scale(${scale})` }}
          />
        ) : (
          <div className="skeleton" style={{ width: '80%', height: 40 }} />
        )}
      </div>

      {/* Meta */}
      <div className="font-card__meta">
        <div className="font-card__top-row">
          <div className="font-card__info">
            <span className="font-card__rank">#{rank}</span>
            <span className="font-card__name" title={font_name}>{font_name}</span>
          </div>
          <div className="font-card__badges">
            <span className={`font-card__category font-card__category--${font_category}`}>
              {CATEGORY_LABELS[font_category] || font_category}
            </span>
            <span className={`font-card__score ${getScoreClass(similarity_pct)}`}>
              {similarity_pct.toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="font-card__bottom-row">
          <span className="font-card__path" title={font_path}>
            {shortenPath(font_path)}
          </span>
          <button className="font-card__download" onClick={handleDownload} title="Скачать шрифт">
            <Download size={13} strokeWidth={1.8} />
            Скачать
          </button>
        </div>
      </div>
    </div>
  );
}
