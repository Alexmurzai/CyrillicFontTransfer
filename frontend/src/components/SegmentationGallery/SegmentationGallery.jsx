import './SegmentationGallery.css';

export default function SegmentationGallery({ images = [] }) {
  if (images.length === 0) {
    return <div className="seg-gallery__empty">Символы появятся после распознавания</div>;
  }

  return (
    <div className="seg-gallery" id="segmentation-gallery">
      {images.map((src, i) => (
        <div className="seg-gallery__item fade-in" key={i} style={{ animationDelay: `${i * 50}ms` }}>
          <img src={src} alt={`Символ ${i + 1}`} />
        </div>
      ))}
    </div>
  );
}
