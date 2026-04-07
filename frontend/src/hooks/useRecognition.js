import { useState, useRef, useCallback, useEffect } from 'react';
import { recognizeFont, updatePreviews, checkHealth } from '../api/hfr';

/**
 * Custom hook для управления состоянием распознавания шрифтов.
 */
export function useRecognition() {
  // Результаты
  const [matches, setMatches] = useState([]);
  const [charImages, setCharImages] = useState([]);
  const [total, setTotal] = useState(0);
  const [visibleCount, setVisibleCount] = useState(5);

  // UI состояния
  const [isLoading, setIsLoading] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState(null);

  // Backend health
  const [health, setHealth] = useState(null);

  // Abort controller для отмены запросов
  const abortRef = useRef(null);
  const debounceRef = useRef(null);

  // Проверка здоровья backend
  const checkBackend = useCallback(async () => {
    try {
      const h = await checkHealth();
      setHealth(h);
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, [checkBackend]);

  // Основной поиск
  const recognize = useCallback(async (imageFile, options) => {
    // Отменить предыдущий запрос
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);
    setMatches([]);
    setCharImages([]);
    setVisibleCount(5);

    try {
      const data = await recognizeFont(imageFile, options, controller.signal);
      setCharImages(data.char_images || []);
      setMatches(data.matches || []);
      setTotal(data.total || 0);
      setVisibleCount(Math.min(5, (data.matches || []).length));
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Показать ещё
  const showMore = useCallback(() => {
    setVisibleCount(prev => Math.min(prev + 5, matches.length));
  }, [matches.length]);

  // Обновление превью (debounced)
  const updatePreview = useCallback((options) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      if (matches.length === 0) return;

      // Отменить предыдущий update-запрос
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setIsUpdating(true);

      try {
        const visibleMatches = matches.slice(0, visibleCount);
        const paths = visibleMatches.map(m => m.font_path);

        const data = await updatePreviews(paths, options, controller.signal);

        // Обновляем только base64 превью в существующих матчах
        setMatches(prev =>
          prev.map(m => ({
            ...m,
            preview_base64: data.previews[m.font_path] || m.preview_base64,
          }))
        );
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.warn('Preview update failed:', err);
        }
      } finally {
        setIsUpdating(false);
      }
    }, 300);
  }, [matches, visibleCount]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return {
    // Data
    matches,
    charImages,
    total,
    visibleCount,
    health,

    // UI
    isLoading,
    isUpdating,
    error,

    // Actions
    recognize,
    showMore,
    updatePreview,
    checkBackend,
  };
}
