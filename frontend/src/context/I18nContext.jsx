import React, { createContext, useState, useContext, useEffect } from 'react';

const I18nContext = createContext();

const dictionaries = {
  ru: {
    marketing_top: "Сэкономьте 5 часов ручного поиска при адаптации вашего бренда на кириллические рынки. Загрузите латиницу — получите идеальное кириллическое соответствие мгновенно.",
    title_main: "Подбор кириллических шрифтов",
    empty_subtitle: "Загрузите скриншот с латинским текстом в панели слева, и нейросеть подберёт похожие кириллические шрифты из базы",
    btn_recognize: "Найти шрифты",
    btn_login: "Войти",
    btn_register: "Регистрация",
    btn_upgrade: "Улучшить тариф",
    limit_reached: "Лимит исчерпан",
    limit_anonymous: "Анонимный доступ: {used}/2 подборов",
    limit_registered: "Баланс: {balance} подборов",
    upload_hint: "Перетащите изображение или нажмите для выбора",
    preview_text_label: "Текст превью",
    letter_spacing: "Межбуквенное расстояние",
    word_spacing: "Пробелы",
    category_all: "Все",
    category_serif: "С засечками",
    category_sans: "Без засечек",
    category_script: "Рукописные",
    category_display: "Акцидентные",
    category_mono: "Моноширинные",
    pricing_title: "Тарифы и лимиты",
    currency: "₽",
    
    // Новые переводы для полной локализации
    results: "Результаты",
    scale: "Масштаб",
    brand_subtitle: "Поиск кириллических аналогов по латинскому образцу",
    upload_section_title: "Загрузите изображение",
    demonstration_text: "Текст для демонстрации",
    btn_find_matches: "Найти аналоги",
    searching: "Поиск...",
    segmentation: "Сегментация",
    typography_settings: "Настройки типографики",
    api_settings: "Настройки API",
    api_settings_hint: "Укажите адрес вашего бэкенда (например, от Cloudflare Tunnel)",
    fonts_status_format: "{count} шрифтов • {device}",
    status_online: "Подключено",
    status_offline: "Нет связи",
    btn_show_more: "Показать ещё 5",
    no_fonts_in_category: "Шрифтов в категории «{category}» не найдено",
    alt_uploaded_image: "Загруженное изображение",
    delete_title: "Удалить",
    download_btn: "Скачать",
    download_title: "Скачать шрифт",
    alt_preview: "Превью {name}",
    symbols_placeholder: "Символы появятся после распознавания",
    alt_char: "Символ {index}",
    placeholder_preview: "Например: Привет, мир!",
    placeholder_email: "Эл. почта",
    placeholder_password: "Пароль",
    
    // Локализация пакетов цен
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
    
    // Авторизация
    auth_switch_to_login: "Уже есть аккаунт? Войти",
    auth_switch_to_register: "Нет аккаунта? Зарегистрироваться",

    // Дополнительно
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
    marketing_top: "Save 5 hours of manual search when adapting your brand to Cyrillic markets. Upload Latin - get the perfect Cyrillic match instantly.",
    title_main: "Brand Localization Tool",
    empty_subtitle: "Upload a screenshot with Latin text in the left panel, and the neural network will find similar Cyrillic fonts from the database",
    btn_recognize: "Find Fonts",
    btn_login: "Log in",
    btn_register: "Sign up",
    btn_upgrade: "Upgrade",
    limit_reached: "Limit reached",
    limit_anonymous: "Anonymous: {used}/2 searches",
    limit_registered: "Balance: {balance} searches",
    upload_hint: "Drag & drop image or click to select",
    preview_text_label: "Preview text",
    letter_spacing: "Letter spacing",
    word_spacing: "Word spacing",
    category_all: "All",
    category_serif: "Serif",
    category_sans: "Sans Serif",
    category_script: "Script",
    category_display: "Display",
    category_mono: "Monospace",
    pricing_title: "Pricing & Limits",
    currency: "$",
    
    // New translations for full localization
    results: "Results",
    scale: "Scale",
    brand_subtitle: "Search Cyrillic analogues by Latin sample",
    upload_section_title: "Upload image",
    demonstration_text: "Demonstration text",
    btn_find_matches: "Find matches",
    searching: "Searching...",
    segmentation: "Segmentation",
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
    download_btn: "Download",
    download_title: "Download font",
    alt_preview: "Preview {name}",
    symbols_placeholder: "Symbols will appear after recognition",
    alt_char: "Character {index}",
    placeholder_preview: "e.g., Hello, world!",
    placeholder_email: "Email",
    placeholder_password: "Password",
    
    // Pricing package localization
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
