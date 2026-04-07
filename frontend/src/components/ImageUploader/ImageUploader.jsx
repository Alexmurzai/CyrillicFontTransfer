import { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, X, Clipboard } from 'lucide-react';
import './ImageUploader.css';

export default function ImageUploader({ onImageSelect, disabled }) {
  const [dragover, setDragover] = useState(false);
  const [preview, setPreview] = useState(null);
  const inputRef = useRef(null);

  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) return;
    setPreview(URL.createObjectURL(file));
    onImageSelect?.(file);
  }, [onImageSelect]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragover(false);
    const file = e.dataTransfer?.files?.[0];
    handleFile(file);
  }, [handleFile]);

  const handlePaste = useCallback((e) => {
    const items = e.clipboardData?.items;
    if (!items || disabled) return;
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        handleFile(item.getAsFile());
        break;
      }
    }
  }, [handleFile, disabled]);

  // Global paste support
  useEffect(() => {
    const onGlobalPaste = (e) => {
      // Only capture global paste if we don't have a preview yet
      if (!preview) handlePaste(e);
    };
    window.addEventListener('paste', onGlobalPaste);
    return () => window.removeEventListener('paste', onGlobalPaste);
  }, [handlePaste, preview]);

  const handleChange = useCallback((e) => {
    handleFile(e.target.files?.[0]);
  }, [handleFile]);

  const handleRemove = useCallback((e) => {
    e.stopPropagation();
    setPreview(null);
    onImageSelect?.(null);
    if (inputRef.current) inputRef.current.value = '';
  }, [onImageSelect]);

  const className = [
    'uploader',
    dragover && 'uploader--dragover',
    preview && 'uploader--has-image',
  ].filter(Boolean).join(' ');

  return (
    <div
      className={className}
      onClick={() => !preview && inputRef.current?.click()}
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
      onDragLeave={() => setDragover(false)}
      onPaste={handlePaste}
      tabIndex={0}
      id="image-uploader"
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="uploader__input"
        onChange={handleChange}
        disabled={disabled}
      />

      {preview ? (
        <>
          <img src={preview} alt="Загруженное изображение" className="uploader__preview" />
          <button className="uploader__remove" onClick={handleRemove} title="Удалить">
            <X size={14} strokeWidth={2} />
          </button>
        </>
      ) : (
        <>
        <div className="uploader__empty">
          <div className="uploader__icons">
            <Upload size={28} strokeWidth={1.2} className="uploader__icon" />
            <div className="uploader__icon-divider" />
            <Clipboard size={22} strokeWidth={1.2} className="uploader__icon uploader__icon--small" />
          </div>
          <span className="uploader__text">
            Перетащите изображение или нажмите для выбора
          </span>
          <div className="uploader__actions">
            <span className="uploader__badge uploader__badge--click">File</span>
            <span className="uploader__badge uploader__badge--paste">Ctrl+V</span>
          </div>
        </div>
        </>
      )}
    </div>
  );
}
