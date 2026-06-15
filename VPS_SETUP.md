# Инструкция по развертыванию MOCT (HFR) на VPS и настройке домена

Эта инструкция поможет вам перенести проект с локального ПК на постоянный сервер (VPS/VDS) с собственным доменом, доступным по всему миру.

---

## Шаг 1. Регистрация домена и настройка DNS (Cloudflare)

Чтобы сайт открывался по красивому адресу и был защищен:
1. **Зарегистрируйте домен:** Используйте любого регистратора (например, [Reg.ru](https://www.reg.ru/), [Ru-Center](https://www.nic.ru/) в РФ или [Porkbun](https://porkbun.com/), [Namecheap](https://www.namecheap.com/) за рубежом).
2. **Создайте аккаунт на Cloudflare:** Зайдите на [cloudflare.com](https://www.cloudflare.com/) (сервис полностью бесплатен для личного использования).
3. **Свяжите домен с Cloudflare:**
   * Добавьте ваш домен в панель Cloudflare.
   * Скопируйте предоставленные Cloudflare NS-сервера (обычно это `*.ns.cloudflare.com`).
   * В личном кабинете регистратора домена замените стандартные DNS-серверы на сервера Cloudflare.
   * Настройка вступит в силу в течение 2–24 часов.

---

## Шаг 2. Покупка VPS/VDS сервера

Для комфортной работы ML-модели на процессоре (CPU) рекомендуется сервер со следующими характеристиками:
* **Характеристики:** 4 vCPU, 8 GB RAM, 40+ GB SSD (например, Ubuntu 22.04 LTS).
* **Рекомендуемые хостинги:**
  * **С оплатой картами РФ:** [Timeweb Cloud](https://timeweb.cloud/), [Selectel](https://selectel.ru/), [RuVDS](https://ruvds.com/).
  * **С оплатой зарубежными картами/криптой:** [PQ.hosting](https://pq.hosting/) (отличный выбор, серверы в разных странах, доступные цены), [Hetzner](https://www.hetzner.com/).

---

## Шаг 3. Копирование файлов и запуск бэкенда на сервере

1. **Подключитесь к VPS по SSH:**
   Используйте терминал (PowerShell / Git Bash) или программу **PuTTY**:
   ```bash
   ssh root@IP_ВАШЕГО_СЕРВЕРА
   ```
2. **Перенесите файлы проекта:**
   Используйте программу **WinSCP** или **FileZilla** для копирования папки `CyrillicFontTransfer` с вашего ПК в папку `/var/www/CyrillicFontTransfer` на сервере.
   
   **Что нужно обязательно скопировать:**
   * Код бэкенда (`backend/`)
   * Базу векторов FAISS (`data/font_signatures.faiss` и `data/font_metadata.json`)
   * Файлы баз данных (`data/users.db`, `data/hfr_stats.db`)
   * Файл весов нейросети (`models/hfr_model_best.pth`)
   * Файл `requirements.txt`
   * Скрипт развертывания `scripts/deploy.sh`

3. **Запустите скрипт автоматической настройки:**
   На сервере в терминале выполните команды:
   ```bash
   cd /var/www/CyrillicFontTransfer
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```
   Этот скрипт установит Python, настроит виртуальное окружение, загрузит оптимизированную под CPU версию PyTorch и запустит бэкенд как фоновую службу Systemd.

---

## Шаг 4. Настройка SSL (HTTPS) через Certbot

Для защиты данных и корректной работы платежных систем сайт должен работать по HTTPS:
1. В панели Cloudflare в разделе **DNS -> Records** добавьте запись типа **A**:
   * Name: `@` (или ваш поддомен, например `api`)
   * Value: IP-адрес вашего VPS.
   * Proxy status: *Proxied* (оранжевое облако).
2. На сервере в терминале установите SSL-сертификат Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d ВАШ_ДОМЕН.ru
   ```
   *(Укажите свой email и согласитесь на перенаправление трафика на HTTPS).*

---

## Шаг 5. Деплой и настройка фронтенда

У вас есть два отличных варианта размещения фронтенда:

### Вариант А. На серверах GitHub Pages (Бесплатно)
1. В коде фронтенда в файле **[vite.config.js](file:///d:/applications/CyrillicFontTransfer/frontend/vite.config.js)** настройте прокси-домен бэкенда.
2. Соберите проект локально: `npm run build`.
3. Закоммитьте изменения в Git и запушьте в репозиторий. GitHub Actions соберет и обновит страницу.
4. В настройках репозитория GitHub в разделе **Settings -> Pages** привяжите ваш домен (например, `font-transfer.ru`), а в Cloudflare направьте запись A на IP-адреса GitHub Pages.

### Вариант Б. На вашем собственном VPS (Всё в одном месте)
Скрипт `deploy.sh` уже установил веб-сервер Nginx. Вы можете настроить его так, чтобы он раздавал и фронтенд, и бэкенд на одном сервере.

---

## Шаг 6. SEO-оптимизация и индексация в поисковиках

Чтобы сайт находили в Google и Яндекс:
1. **Зарегистрируйтесь в панелях веб-мастеров:**
   * Добавьте сайт в [Google Search Console](https://search.google.com/search-console).
   * Добавьте сайт в [Яндекс.Вебмастер](https://webmaster.yandex.ru/).
2. **Загрузите файлы индексации:**
   * В корневой каталог фронтенда уже добавлены оптимизированные файлы **[sitemap.xml](file:///d:/applications/CyrillicFontTransfer/frontend/public/sitemap.xml)** и **[robots.txt](file:///d:/applications/CyrillicFontTransfer/frontend/public/robots.txt)**.
   * Отправьте ссылку на `sitemap.xml` в панели веб-мастеров Google и Яндекс для быстрой индексации.
