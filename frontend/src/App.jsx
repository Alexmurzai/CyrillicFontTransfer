import { useState, useCallback } from 'react';
import { Type } from 'lucide-react';
import Sidebar from './components/Sidebar/Sidebar';
import FontFeed from './components/FontFeed/FontFeed';
import { useRecognition } from './hooks/useRecognition';
import './App.css';

export default function App() {
  const {
    matches,
    charImages,
    total,
    visibleCount,
    health,
    isLoading,
    isUpdating,
    error,
    recognize,
    showMore,
    updatePreview,
  } = useRecognition();

  const [activeCategory, setActiveCategory] = useState('all');

  // Запуск поиска
  const handleRecognize = useCallback((imageFile, options) => {
    setActiveCategory(options.category || 'all');
    recognize(imageFile, {
      topK: 50,
      previewText: options.previewText,
      letterSpacing: options.letterSpacing,
      wordSpacing: options.wordSpacing,
      category: options.category || 'all',
    });
  }, [recognize]);

  // Обновление превью при изменении настроек
  const handlePreviewUpdate = useCallback((opts) => {
    updatePreview(opts);
  }, [updatePreview]);

  const hasResults = matches.length > 0;

  return (
    <div className="app">
      {/* Loading overlay */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner" />
          <span className="loading-text">Нейросеть анализирует изображение...</span>
        </div>
      )}

      {/* Left: Sidebar */}
      <Sidebar
        onRecognize={handleRecognize}
        onPreviewUpdate={handlePreviewUpdate}
        charImages={charImages}
        isLoading={isLoading}
        error={error}
        health={health}
      />

      {/* Right: Feed */}
      <main className="feed" id="feed">
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
            <Type size={80} strokeWidth={0.5} className="empty-state__icon" />
            <h1 className="empty-state__title">Cyrillic Font Finder</h1>
            <p className="empty-state__text">
              Загрузите скриншот с латинским текстом в панели слева,
              и нейросеть подберёт похожие кириллические шрифты из базы
              в {health?.fonts_count?.toLocaleString() || '4 880'} шрифтов.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
