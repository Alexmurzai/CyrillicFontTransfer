import { useI18n } from '../../context/I18nContext';
import './SegmentationGallery.css';

export default function SegmentationGallery({ images = [] }) {
  const { t } = useI18n();

  if (images.length === 0) {
    return <div className="seg-gallery__empty">{t('symbols_placeholder')}</div>;
  }

  return (
    <div className="seg-gallery" id="segmentation-gallery">
      {images.map((src, i) => (
        <div className="seg-gallery__item fade-in" key={i} style={{ animationDelay: `${i * 50}ms` }}>
          <img src={src} alt={t('alt_char', { index: i + 1 })} />
        </div>
      ))}
    </div>
  );
}
