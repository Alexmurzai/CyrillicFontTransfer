import { useState, useRef, useCallback } from 'react';
import { Upload, X } from 'lucide-react';
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
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        handleFile(item.getAsFile());
        break;
      }
    }
  }, [handleFile]);

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
          <Upload size={28} strokeWidth={1.2} className="uploader__icon" />
          <span className="uploader__text">
            Перетащите изображение или нажмите для выбора
          </span>
          <span className="uploader__hint">
            Ctrl+V — вставка из буфера обмена
          </span>
        </>
      )}
    </div>
  );
}
