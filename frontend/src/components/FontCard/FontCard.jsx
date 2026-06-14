import { useState, useEffect } from 'react';
import { Download } from 'lucide-react';
import { downloadFont, getApiUrl } from '../../api/hfr';
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

  const [isFontLoaded, setIsFontLoaded] = useState(false);

  useEffect(() => {
    if (id === undefined || id === null) return;

    const fontNameFamily = `font-family-match-${id}`;

    // Check if the font has already been added to document.fonts
    let alreadyExists = false;
    document.fonts.forEach((face) => {
      if (face.family === fontNameFamily) {
        alreadyExists = true;
      }
    });

    if (alreadyExists) {
      setIsFontLoaded(true);
      return;
    }

    const apiBase = getApiUrl();
    const fontUrl = `${apiBase}/api/font/download/${id}`;
    let isMounted = true;

    fetch(fontUrl, {
      headers: {
        'Bypass-Tunnel-Reminder': 'true'
      }
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.arrayBuffer();
      })
      .then((buffer) => {
        if (!isMounted) return;
        const fontFace = new FontFace(fontNameFamily, buffer);
        return fontFace.load();
      })
      .then((loadedFace) => {
        if (!loadedFace || !isMounted) return;
        document.fonts.add(loadedFace);
        setIsFontLoaded(true);
      })
      .catch((err) => {
        console.warn(`Failed to fetch and load font face ${font_name} from ${fontUrl}:`, err);
      });

    return () => {
      isMounted = false;
    };
  }, [id, font_name]);

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
          <h3 
            className="font-card__name" 
            title={font_name}
            style={{ fontFamily: isFontLoaded ? `'font-family-match-${id}', var(--font-headline), sans-serif` : 'inherit' }}
          >
            {font_name}
          </h3>
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
