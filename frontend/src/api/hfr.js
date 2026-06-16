/**
 * HFR API Client
 * Все запросы к FastAPI backend.
 */

const STORAGE_KEY = 'hfr_api_url';
const DEFAULT_API_URL = '';

/**
 * Получить текущий API URL.
 * Приоритет: localStorage → env variable → пустая строка (same-origin proxy)
 */
export function getApiUrl() {
  if (typeof window !== 'undefined') {
    // Check search and hash for api_url
    let queryApiUrl = null;
    const searchParams = new URLSearchParams(window.location.search);
    if (searchParams.has('api_url')) {
      queryApiUrl = searchParams.get('api_url');
    } else {
      const hashParts = window.location.hash.split('?');
      if (hashParts.length > 1) {
        const hashParams = new URLSearchParams(hashParts[1]);
        if (hashParams.has('api_url')) {
          queryApiUrl = hashParams.get('api_url');
        }
      }
    }

    if (queryApiUrl) {
      localStorage.setItem(STORAGE_KEY, queryApiUrl.replace(/\/+$/, ''));
      // Clean query parameter from URL
      try {
        const cleanSearch = window.location.search.replace(/[?&]api_url=[^&]*/, '').replace(/^&/, '?').replace(/\?$/, '');
        const cleanHash = window.location.hash.replace(/[?&]api_url=[^&]*/, '').replace(/^&/, '?').replace(/\?$/, '');
        const newUrl = window.location.pathname + cleanSearch + cleanHash;
        window.history.replaceState({}, '', newUrl);
      } catch (e) {
        console.error('Failed to clean URL', e);
      }
      return queryApiUrl.replace(/\/+$/, '');
    }

    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored.replace(/\/+$/, '');
  }
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) return envUrl.replace(/\/+$/, '');

  // Если запущено локально, автоматически переключаемся на локальный бэкенд
  if (typeof window !== 'undefined' && 
      (window.location.hostname === 'localhost' || 
       window.location.hostname === '127.0.0.1' || 
       window.location.hostname.startsWith('192.168.'))) {
    return 'http://localhost:8000';
  }

  return DEFAULT_API_URL;
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
  const res = await fetch(`${base}/api/health`, { 
    signal: AbortSignal.timeout(5000),
    headers: { 'Bypass-Tunnel-Reminder': 'true', 'X-Pinggy-No-Screen': 'true' }
  });
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
    token = null,
    fingerprint = 'unknown',
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

  const headers = { 'Bypass-Tunnel-Reminder': 'true', 'X-Pinggy-No-Screen': 'true', 'X-Fingerprint': fingerprint };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const base = getApiUrl();
  const res = await fetch(`${base}/api/recognize?${params}`, {
    method: 'POST',
    body: formData,
    headers,
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
  const res = await fetch(`${base}/api/update-previews?${params}`, { 
    signal,
    headers: { 'Bypass-Tunnel-Reminder': 'true', 'X-Pinggy-No-Screen': 'true' }
  });

  if (!res.ok) throw new Error('Ошибка обновления превью');
  return res.json();
}

/**
 * Скачивание шрифта по ID.
 */
export async function downloadFont(fontId, fontName) {
  const base = getApiUrl();
  const res = await fetch(`${base}/api/font/download/${fontId}`, {
    headers: { 'Bypass-Tunnel-Reminder': 'true', 'X-Pinggy-No-Screen': 'true' }
  });

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
  const res = await fetch(`${base}/api/categories`, {
    headers: { 'Bypass-Tunnel-Reminder': 'true', 'X-Pinggy-No-Screen': 'true' }
  });
  if (!res.ok) throw new Error('Ошибка получения категорий');
  return res.json();
}
