# Портфолио — matalin-portfolio.ru

Сайт-портфолио frontend-разработчика и создателя Telegram-ассистентов.
Тёмная тема, адаптив от 320 px, серверный рендеринг, строгая CSP без
`unsafe-inline`, админ-панель для управления кейсами и заявками.

## Стек

- **Python 3.11+ / Flask 3.1** — серверный рендеринг, маршруты, формы.
- **Jinja2** — шаблоны (семантическая вёрстка, H1–H3).
- **Ванильный CSS + JS** — без сборщиков и фреймворков: минимальный вес и
  отсутствие инлайнового кода (требование CSP).
- **JSON-хранилище** (`data/`) — состояние кейсов и заявки; запись атомарная.
- **Pillow** — только для генерации изображений (`scripts/make_images.py`).

## Быстрый старт

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env        # Windows
# cp .env.example .env         # Linux/macOS

python run.py
```

- Сайт: http://127.0.0.1:5000
- Админка: http://127.0.0.1:5000/admin/login

При первом запуске генерируется пароль администратора — он печатается в консоль
и сохраняется в `data/admin_secret.txt`. Перенесите его в `.env` как
`ADMIN_PASSWORD` и удалите файл. Ключ подписи сессий (`SECRET_KEY`) хранится
отдельно — в `data/secret_key.txt`, он создаётся автоматически.

## Структура проекта

```
.
├── run.py                  # запуск dev-сервера
├── requirements.txt
├── .env.example            # шаблон переменных окружения
├── app/
│   ├── __init__.py         # фабрика приложения, заголовки, логирование, ошибки
│   ├── config.py           # конфигурация и контакты (ЗАМЕНИТЬ placeholder'ы)
│   ├── content.py          # ВЕСЬ контент: тексты, кейсы, галереи, стек
│   ├── security.py         # CSP, санитизация, валидация, CSRF, rate limit
│   ├── storage.py          # JSON-хранилище (кейсы, заявки)
│   ├── seo.py              # JSON-LD (Person, WebSite, CreativeWork)
│   ├── views.py            # публичные маршруты + форма
│   ├── admin.py            # админ-панель
│   ├── templates/          # base, index, project, 404, error, admin/*
│   └── static/
│       ├── css/styles.css  # дизайн-система
│       ├── js/head.js      # признак JS (до отрисовки)
│       ├── js/main.js      # анимации, меню, галерея, форма
│       └── img/            # обложки (.webp + .png + .avif), favicon, og-cover
├── scripts/
│   ├── backup.py           # ежедневный бэкап data/ + .env (tar.gz)
│   └── make_images.py      # генерация изображений кейсов
├── deploy/
│   ├── nginx.conf          # HTTPS, 301, заголовки, кэш, сжатие
│   └── matalin-portfolio.service  # systemd + gunicorn
├── tests/test_app.py       # 27 тестов: маршруты, безопасность, форма, админка
├── data/                   # рантайм: cases.json, messages.json (не в git)
├── logs/                   # access.log, errors.log (не в git)
└── backups/                # резервные копии (не в git)
```

## Что заменить перед публикацией

Все placeholder'ы собраны в двух местах:

1. **`.env`** (по образцу `.env.example`): `TELEGRAM_USERNAME`,
   `TELEGRAM_DISPLAY`, `EMAIL`, `GITHUB_URL`, `SECRET_KEY`, `ADMIN_PASSWORD`.
2. **`app/config.py`**: `SITE_NAME` — имя владельца в H1.
3. **`app/content.py`**: тексты первого экрана, «Обо мне», кейсы, ссылки на
   GitHub-репозитории (`github="..."`), контент кейсов.

Изображения перегенерируются командой `python scripts/make_images.py`.

## Требования ТЗ — где реализовано

### Адаптивность
| Требование | Реализация |
|---|---|
| Брейкпоинты 320 / 375 / 425 / 768 / 1024 / 1280 / 1440+ | `app/static/css/styles.css` — **mobile-first** (улучшение по сравнению с Desktop First из ТЗ), медиазапросы 768 / 1024 / 1280 / 1440 |
| Паддинги 16 / 24–32 / 40–64 px | `--gutter`: 16 → 24 (@768) → 40 (@1024) → 48 (@1280) → 64 (@1440) |
| Сетка 12 колонок / 1 колонка | `.hero__grid`, `.about__grid`, `.contacts__grid`, `.project-*` — `repeat(12, 1fr)` на десктопе |
| H1 52→32, H2 36→24, body 18→16, line-height 1.5→1.6–1.7 | `clamp()` + медиазапросы в разделах «Типографика» |
| Вертикальные паддинги 120→64 px, gutter 32→16 px | `--section-y`, `--gutter` |
| Тач-таргеты ≥ 48×48 | `.btn`, `.nav__link`, `.burger`, `.gallery__btn`, чекбоксы |
| Кейсы 2×3 / 1 колонка | `.cases__grid` (2 кол. на 1024, 3 кол. на 1440) |
| Первый экран 100vh, 2 колонки, порядок текст → кнопки → визуал | `.hero` / `.hero__grid` |
| Галерея: сетка на десктопе, слайдер со свайпом на мобильном | `.gallery` + `scroll-snap-type: x mandatory` |
| `prefers-reduced-motion` | `@media (prefers-reduced-motion: reduce)` в CSS и проверка в `main.js` |

### SEO и производительность
- `<title>`, `<meta name="description">`, canonical, Open Graph, Twitter Card.
- Иерархия H1–H3, семантические теги (`header`, `main`, `section`, `article`,
  `figure`, `nav`, `footer`).
- `/sitemap.xml` и `/robots.txt` генерируются на лету; скрытые кейсы в sitemap
  не попадают.
- JSON-LD: `Person`, `WebSite`, `CreativeWork` — отдаётся с хэшем в CSP.
- Изображения: WebP + AVIF + PNG-fallback через `<picture>`, `loading="lazy"`,
  `decoding="async"`, явные `width`/`height` (нет сдвигов макета).
- Статика кэшируется на год (`immutable`), HTML — `must-revalidate`.
- Шрифты системные — нет внешних запросов, ничего не блокирует рендер.

### Безопасность
- `Strict-Transport-Security`, `Content-Security-Policy` (без `unsafe-inline`),
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`,
  `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`,
  `Cross-Origin-*` — `app/security.py`.
- 301-редиректы HTTP→HTTPS и www→без www — `before_request` + `deploy/nginx.conf`.
- Двойная валидация формы (клиент `main.js` + сервер `security.validate_contact`).
- Санитизация ввода: удаление HTML-тегов, управляющих и опасных символов.
- Honeypot-поле `website`, CSRF-токен, rate limit по IP.
- Запрет `eval`, `document.write`, инлайновых скриптов и `onclick`-атрибутов —
  все скрипты внешние, CSP это гарантирует.
- Админка: пароль из окружения, HttpOnly + SameSite=Strict cookie, `noindex`.
- Логирование всех 4xx/5xx в `logs/errors.log`, доступ в `logs/access.log`.

### Бэкапы и эксплуатация
```bash
python scripts/backup.py --prune 30   # бэкап data/ + .env, хранение 30 дней
```
Cron:
```
17 3 * * * cd /srv/matalin-portfolio && /usr/bin/python3 scripts/backup.py --prune 30
```

## Админ-панель

`/admin/login` → `/admin/`:

- Переключатель **«Скрыть кейс»** — кейс исчезает из публичной части, его
  страница отдаёт 404 и он пропадает из `sitemap.xml` (сценарий для NDA).
- Список заявок с формы: отметить выполненной, в архив, удалить.
- Страница «Доступ и хранилище» с путями к файлам состояния.

## Тесты

```bash
python -m unittest discover -s tests -v
```

27 тестов: главная и иерархия заголовков, страницы кейсов, 404, sitemap/robots,
заголовки безопасности, CSP-хэши JSON-LD, отсутствие инлайновых скриптов и стилей,
форма (CSRF, валидация, honeypot, XSS-санитизация, rate limit), админка (вход,
скрытие кейса, выход).

## Деплой (Linux + Nginx + gunicorn)

```bash
# 1. Код и окружение
sudo mkdir -p /srv/matalin-portfolio && cd /srv/matalin-portfolio
# ... скопировать проект ...
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2. .env для продакшена
cp .env.example .env
# APP_ENV=production, SECRET_KEY=..., ADMIN_PASSWORD=..., TRUST_PROXY_SSL=true

# 3. Сервис
sudo cp deploy/matalin-portfolio.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now matalin-portfolio

# 4. Nginx + SSL
sudo cp deploy/nginx.conf /etc/nginx/sites-available/matalin-portfolio
sudo ln -s /etc/nginx/sites-available/matalin-portfolio /etc/nginx/sites-enabled/
sudo certbot --nginx -d matalin-portfolio.ru -d www.matalin-portfolio.ru
sudo nginx -t && sudo systemctl reload nginx

# 5. Права на запись
sudo chown -R www-data:www-data data logs backups
```

Проверка: `curl -I https://matalin-portfolio.ru` — должны быть `HTTP/2 200`,
`strict-transport-security`, `content-security-policy`, `x-frame-options`.

## Лицензия

Код — свободно используйте и адаптируйте. Контент кейсов — демонстрационный,
замените его на свой.
