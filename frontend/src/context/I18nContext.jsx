import React, { createContext, useState, useContext, useEffect } from 'react';

const I18nContext = createContext();

const dictionaries = {
  ru: {
    marketing_top: "СЭКОНОМЬТЕ 5 ЧАСОВ РУЧНОГО ПОИСКА • ЗАГРУЗИТЕ ЛАТИНИЦУ — ПОЛУЧИТЕ ИДЕАЛЬНОЕ КИРИЛЛИЧЕСКОЕ СООТВЕТСТВИЕ МГНОВЕННО",
    title_main: "Подбор кириллических шрифтов",
    empty_subtitle: "Загрузите скриншот с латинским текстом в панели слева, и нейросеть подберёт похожие кириллические шрифты из базы",
    btn_recognize: "Найти шрифты",
    btn_login: "Войти",
    btn_register: "Регистрация",
    btn_upgrade: "PRO",
    limit_reached: "Лимит исчерпан",
    limit_anonymous: "АНОНИМНЫЙ: {used}/5",
    limit_registered: "БАЛАНС: {balance}",
    upload_hint: "Перетащите изображение или нажмите для выбора",
    preview_text_label: "Текст превью",
    letter_spacing: "Межбуквенное расстояние",
    word_spacing: "Расстояние между словами",
    category_all: "Все",
    category_serif: "С засечками",
    category_sans: "Без засечек",
    category_script: "Рукописные",
    category_display: "Акцидентные",
    category_mono: "Моноширинные",
    category_unknown: "Другие",
    pricing_title: "Тарифы и лимиты",
    currency: "₽",

    // Navigation
    nav_match: "MATCH",
    nav_generator: "GENERATOR",
    nav_library: "LIBRARY",

    // Sidebar
    ai_font_engine: "AI FONT ENGINE",
    toolbox_title: "TOOLBOX",
    tab_upload: "Загрузка",
    tab_preview: "Превью",
    tab_segments: "Сегменты",
    tab_layout: "Параметры",
    upgrade_to_pro: "UPGRADE TO PRO",

    // Results
    results: "Результаты",
    match_results: "Результаты подбора",
    scale: "Масштаб",
    ml_model_synced: "ML МОДЕЛЬ СИНХР.",
    structural_match: "СОВПАДЕНИЕ",

    // Footer status
    status_bar_connected: "СТАТУС: ПОДКЛЮЧЕНО",
    status_bar_offline: "СТАТУС: ОТКЛЮЧЕНО",
    status_bar_latency: "ЗАДЕРЖКА: 24MS",
    status_bar_api: "API: АКТИВЕН",

    // Upload
    brand_subtitle: "Поиск кириллических аналогов",
    upload_section_title: "Загрузите изображение",
    drop_reference_font: "Загрузите референс",
    drop_reference_hint: "SVG, TTF, OTF или Изображение",
    demonstration_text: "Текст для демонстрации",
    btn_find_matches: "Найти аналоги",
    searching: "Поиск...",
    segmentation: "Сегментация",
    detected_glyphs: "ОБНАРУЖЕННЫЕ ГЛИФЫ",
    n_found: "{count} НАЙДЕНО",
    typography_settings: "Настройки типографики",
    api_settings: "Настройки API",
    api_settings_hint: "Укажите адрес вашего бэкенда (напр., от Cloudflare Tunnel)",
    fonts_status_format: "{count} шрифтов • {device}",
    status_online: "Подключено",
    status_offline: "Нет связи",
    btn_show_more: "Показать ещё 5",
    no_fonts_in_category: "Шрифтов в категории «{category}» не найдено",
    alt_uploaded_image: "Загруженное изображение",
    delete_title: "Удалить",
    download_btn: "СКАЧАТЬ",
    download_title: "Скачать шрифт",
    alt_preview: "Превью {name}",
    symbols_placeholder: "Символы появятся после распознавания",
    alt_char: "Символ {index}",
    placeholder_preview: "Например: Привет, мир!",
    placeholder_email: "Эл. почта",
    placeholder_password: "Пароль",

    // Promo
    promo_title: "ИЮНЬ 50%",
    promo_text: "Скидка за подписку на 1 год",
    claim_promo: "ЗАБРАТЬ",

    // Pricing
    pkg_20_title: "20 подборов",
    pkg_20_desc: "Разовый пакет",
    pkg_100_title: "100 подборов",
    pkg_100_desc: "Лучшая цена за подбор",
    pkg_week_title: "1 неделя Pro",
    pkg_week_desc: "Безлимитный доступ",
    pkg_month_title: "1 месяц Pro",
    pkg_month_desc: "Безлимитный доступ",
    pkg_year_title: "1 год Pro",
    pkg_year_desc: "Безлимитный доступ",
    buy_with: "Оплатить через {gateway}",
    gateway_ru: "ЮKassa / МИР",
    gateway_en: "Crypto / MoonPay",
    payment_success: "Оплата прошла успешно! Баланс/подписка обновлены.",
    payment_failed: "Ошибка оплаты",

    // Auth
    auth_switch_to_login: "Уже есть аккаунт? Войти",
    auth_switch_to_register: "Нет аккаунта? Зарегистрироваться",

    // Additional
    of: "из",
    loading_analyzing: "Нейросеть анализирует изображение...",

    // Errors
    "Backend недоступен": "Сервер недоступен",
    "Ошибка обновления превью": "Ошибка обновления превью",
    "Ошибка скачивания": "Не удалось скачать шрифт",
    "Ошибка получения категорий": "Не удалось получить категории шрифтов",
    "HFR Engine не загружен": "Модель ИИ еще запускается, пожалуйста, подождите",
    "Символы не найдены на изображении. Попробуйте другое.": "Символы не найдены на изображении. Попробуйте другое.",
    "err_server_error_status": "Ошибка сервера: {status}",
    "err_processing_failed_details": "Ошибка обработки: {details}",
    "Email already registered": "Этот email уже зарегистрирован",
    "Incorrect email or password": "Неверный email или пароль",
    "err_login_failed": "Не удалось войти в аккаунт",
    "err_register_failed": "Не удалось зарегистрироваться",
  },
  en: {
    marketing_top: "SAVE 5 HOURS OF MANUAL SEARCH • UPLOAD LATIN — GET THE PERFECT CYRILLIC MATCH INSTANTLY",
    title_main: "Cyrillic Font Matcher",
    empty_subtitle: "Upload a screenshot with Latin text in the left panel, and the neural network will find similar Cyrillic fonts from the database",
    btn_recognize: "Find Fonts",
    btn_login: "Log in",
    btn_register: "Sign up",
    btn_upgrade: "PRO",
    limit_reached: "Limit reached",
    limit_anonymous: "ANONYMOUS: {used}/5",
    limit_registered: "BALANCE: {balance}",
    upload_hint: "Drag & drop image or click to select",
    preview_text_label: "Preview text",
    letter_spacing: "Letter Spacing",
    word_spacing: "Word Spacing",
    category_all: "All",
    category_serif: "Serif",
    category_sans: "Sans Serif",
    category_script: "Script",
    category_display: "Display",
    category_mono: "Monospace",
    category_unknown: "Other",
    pricing_title: "Pricing & Limits",
    currency: "$",

    // Navigation
    nav_match: "MATCH",
    nav_generator: "GENERATOR",
    nav_library: "LIBRARY",

    // Sidebar
    ai_font_engine: "AI FONT ENGINE",
    toolbox_title: "TOOLBOX",
    tab_upload: "Upload",
    tab_preview: "Preview",
    tab_segments: "Segments",
    tab_layout: "Layout",
    upgrade_to_pro: "UPGRADE TO PRO",

    // Results
    results: "Results",
    match_results: "Match Results",
    scale: "Scale",
    ml_model_synced: "ML MODEL SYNCED",
    structural_match: "STRUCTURAL MATCH",

    // Footer status
    status_bar_connected: "STATUS: CONNECTED",
    status_bar_offline: "STATUS: OFFLINE",
    status_bar_latency: "LATENCY: 24MS",
    status_bar_api: "API: ACTIVE",

    // Upload
    brand_subtitle: "Search Cyrillic analogues by Latin sample",
    upload_section_title: "Upload image",
    drop_reference_font: "Drop Reference Font",
    drop_reference_hint: "SVG, TTF, OTF or Image",
    demonstration_text: "Demonstration text",
    btn_find_matches: "Find matches",
    searching: "Searching...",
    segmentation: "Segmentation",
    detected_glyphs: "DETECTED GLYPHS",
    n_found: "{count} FOUND",
    typography_settings: "Typography settings",
    api_settings: "API Settings",
    api_settings_hint: "Specify your backend URL (e.g., from Cloudflare Tunnel)",
    fonts_status_format: "{count} fonts • {device}",
    status_online: "Connected",
    status_offline: "No connection",
    btn_show_more: "Show 5 more",
    no_fonts_in_category: "No fonts found in category '{category}'",
    alt_uploaded_image: "Uploaded image",
    delete_title: "Delete",
    download_btn: "DOWNLOAD",
    download_title: "Download font",
    alt_preview: "Preview {name}",
    symbols_placeholder: "Symbols will appear after recognition",
    alt_char: "Character {index}",
    placeholder_preview: "e.g., Hello, world!",
    placeholder_email: "Email",
    placeholder_password: "Password",

    // Promo
    promo_title: "JUNE 50%",
    promo_text: "Discount for 1-year subscription",
    claim_promo: "CLAIM",

    // Pricing
    pkg_20_title: "20 Searches",
    pkg_20_desc: "Pay as you go",
    pkg_100_title: "100 Searches",
    pkg_100_desc: "Best value per search",
    pkg_week_title: "1 Week Pro",
    pkg_week_desc: "Unlimited access",
    pkg_month_title: "1 Month Pro",
    pkg_month_desc: "Unlimited access",
    pkg_year_title: "1 Year Pro",
    pkg_year_desc: "Unlimited access",
    buy_with: "Buy with {gateway}",
    gateway_ru: "YooKassa / MIR",
    gateway_en: "Crypto / MoonPay",
    payment_success: "Payment successful! Balance/subscription updated.",
    payment_failed: "Payment failed",

    // Auth
    auth_switch_to_login: "Already have an account? Log in",
    auth_switch_to_register: "Need an account? Sign up",

    // Additional
    of: "of",
    loading_analyzing: "The neural network is analyzing the image...",

    // Errors
    "Backend недоступен": "Server is unavailable",
    "Ошибка обновления превью": "Error updating font preview",
    "Ошибка скачивания": "Failed to download font file",
    "Ошибка получения категорий": "Failed to fetch font categories",
    "HFR Engine не загружен": "AI model is still starting up, please wait",
    "Символы не найдены на изображении. Попробуйте другое.": "No characters found on the image. Please try another one.",
    "err_server_error_status": "Server error: {status}",
    "err_processing_failed_details": "Processing error: {details}",
    "Email already registered": "This email is already registered",
    "Incorrect email or password": "Incorrect email or password",
    "err_login_failed": "Failed to log in",
    "err_register_failed": "Failed to register",
  }
};

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(() => {
    return localStorage.getItem('hfr_lang') || 'ru';
  });

  useEffect(() => {
    localStorage.setItem('hfr_lang', lang);
  }, [lang]);

  const t = (key, params = {}) => {
    let str = dictionaries[lang][key] || key;
    Object.keys(params).forEach(k => {
      str = str.replace(`{${k}}`, params[k]);
    });
    return str;
  };

  const toggleLang = () => {
    setLang(prev => prev === 'ru' ? 'en' : 'ru');
  };

  return (
    <I18nContext.Provider value={{ lang, setLang, toggleLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
