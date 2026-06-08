import React, { createContext, useState, useContext, useEffect } from 'react';

const I18nContext = createContext();

const dictionaries = {
  ru: {
    marketing_top: "Сэкономьте 5 часов ручного поиска при адаптации вашего бренда на кириллические рынки. Загрузите латиницу — получите идеальное кириллическое соответствие мгновенно.",
    title_main: "Cyrillic Font Finder",
    empty_subtitle: "Загрузите скриншот с латинским текстом в панели слева, и нейросеть подберёт похожие кириллические шрифты из базы",
    btn_recognize: "Найти шрифты",
    btn_login: "Войти",
    btn_register: "Регистрация",
    btn_upgrade: "Улучшить тариф",
    limit_reached: "Лимит исчерпан",
    limit_anonymous: "Анонимный доступ: {used}/2 подборов",
    limit_registered: "Баланс: {balance} подборов",
    upload_hint: "Перетащите изображение или кликните",
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
    upload_hint: "Drag & drop image or click",
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
