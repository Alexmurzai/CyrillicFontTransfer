/**
 * HFR API Client
 * Все запросы к FastAPI backend.
 */

const STORAGE_KEY = 'hfr_api_url';

/**
 * Получить текущий API URL.
 * Приоритет: localStorage → env variable → пустая строка (same-origin proxy)
 */
export function getApiUrl() {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored.replace(/\/+$/, '');
  }
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) return envUrl.replace(/\/+$/, '');
  return '';
}

/**
 * Сохранить API URL в localStorage.
 */
export function setApiUrl(url) {
  if (typeof window !== 'undefined') {
    if (url) {
      localStorage.setItem(STORAGE_KEY, url.replace(/\/+$/, ''));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }
}

/**
 * Проверка здоровья сервиса.
 */
export async function checkHealth() {
  const base = getApiUrl();
  const res = await fetch(`${base}/api/health`, { signal: AbortSignal.timeout(5000) });
  if (!res.ok) throw new Error('Backend недоступен');
  return res.json();
}

/**
 * Распознавание шрифта по изображению.
 */
export async function recognizeFont(imageFile, options = {}, signal) {
  const {
    topK = 50,
    previewText = 'АБВГДЕabc',
    letterSpacing = 0,
    wordSpacing = 20,
    category = 'all',
  } = options;

  const formData = new FormData();
  formData.append('file', imageFile);

  const params = new URLSearchParams({
    top_k: topK,
    preview_text: previewText,
    letter_spacing: letterSpacing,
    word_spacing: wordSpacing,
    category,
  });

  const base = getApiUrl();
  const res = await fetch(`${base}/api/recognize?${params}`, {
    method: 'POST',
    body: formData,
    signal,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Ошибка сервера: ${res.status}`);
  }

  return res.json();
}

/**
 * Batch-обновление превью.
 */
export async function updatePreviews(fontPaths, options = {}, signal) {
  const {
    text = 'АБВГДЕabc',
    letterSpacing = 0,
    wordSpacing = 20,
  } = options;

  const params = new URLSearchParams({
    font_paths: fontPaths.join(','),
    text,
    letter_spacing: letterSpacing,
    word_spacing: wordSpacing,
  });

  const base = getApiUrl();
  const res = await fetch(`${base}/api/update-previews?${params}`, { signal });

  if (!res.ok) throw new Error('Ошибка обновления превью');
  return res.json();
}

/**
 * Скачивание шрифта по ID.
 */
export async function downloadFont(fontId, fontName) {
  const base = getApiUrl();
  const res = await fetch(`${base}/api/font/download/${fontId}`);

  if (!res.ok) throw new Error('Ошибка скачивания');

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fontName || 'font.ttf';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Статистика категорий.
 */
export async function getCategories() {
  const base = getApiUrl();
  const res = await fetch(`${base}/api/categories`);
  if (!res.ok) throw new Error('Ошибка получения категорий');
  return res.json();
}
