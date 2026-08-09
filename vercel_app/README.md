# 📱 EDIT Mobile — Vercel Edition

Мобильный веб-пульт ИИ-ассистента **EDIT / MARK** с режимом наушников.
Заточен под загрузку на **Vercel** (чистая статика + serverless Python).

## 🌟 Что внутри

- 🎛 **Главный пульт** — кнопки быстрых команд, текстовый ввод, статус
- 🎧 **Режим наушников** — push-to-talk, индикатор голоса, статус BT
- 🔐 **Лёгкий PIN-вход** (без OpenCV — Vercel не тянет тяжёлые ML-библиотеки)
- 📡 **API** на Vercel Functions (`/api/...`):
  - `GET  /api/health` — проверка статуса
  - `POST /api/command` — отправка команды ассистенту
  - `GET  /api/queue`  — очередь команд (для синхронизации с ПК)
  - `GET  /api/headphones/status` — статус режима наушников
  - `POST /api/headphones/toggle` — вкл/выкл режим
  - `GET  /api/headphones/log`   — последние события

## 🚀 Деплой на Vercel

### Вариант 1: Через Git (рекомендую)
1. Залей папку `vercel_app/` в отдельный GitHub-репозиторий (например `edit-mobile`)
2. Зайди на https://vercel.com → **Add New Project** → импортируй репо
3. Vercel сам найдёт `vercel.json` и настроит Python-функции
4. Жми **Deploy** — через ~30 секунд получишь URL вида `https://edit-mobile.vercel.app`

### Вариант 2: Через CLI
```bash
cd vercel_app
npm i -g vercel
vercel login
vercel --prod
```

### Вариант 3: Drag & Drop
1. Зайди на https://vercel.com/new
2. Перетащи папку `vercel_app/` в окно браузера
3. Готово

## 🔧 Настройка

После деплоя открой сайт на телефоне:
- Введи PIN (по умолчанию `1234` — смени в `api/auth.py`)
- Выбери режим **🎧 Наушники** для push-to-talk
- Кнопка «📡 Подключить ПК» — введи адрес твоего ПК (например `http://192.168.1.10:8000`),
  и сайт будет проксировать команды на твой MARK-сервер

## ⚠️ Ограничения Vercel

- ❌ **Нет OpenCV / FaceID** (бинарники слишком большие для serverless)
- ❌ **Нет WebSocket на постоянку** (используется long-polling)
- ❌ **Нет доступа к локалке** (команды уходят в очередь на сервере)
- ✅ **Есть HTTPS из коробки** (важно для микрофона в браузере)

## 📂 Структура

```
vercel_app/
├── vercel.json              # конфиг Vercel
├── README.md                # этот файл
├── requirements.txt
├── _lib/                    # общие хелперы (НЕ endpoint'ы)
│   └── shared.py
├── public/                  # статика (HTML/CSS/JS)
│   ├── index.html           # главный пульт
│   ├── headphones.html      # режим наушников
│   ├── pin.html             # экран ввода PIN
│   ├── css/style.css
│   ├── js/{api,app,headphones}.js
│   ├── manifest.webmanifest # PWA
│   └── icons/
└── api/                     # Vercel Serverless Functions (Python)
    ├── health.py
    ├── command.py
    ├── queue.py
    ├── auth.py
    └── headphones/
        ├── status.py
        ├── toggle.py
        └── log.py
```

> ⚠️ **Важно:** общие модули лежат в `_lib/` (за пределами `api/`), потому что
> Vercel пытается собрать **любой** `.py` в `api/` как endpoint. Если положить
> хелпер в `api/_shared.py` — будет ошибка
> `Could not find a top-level "handler" in "api/_shared.py"`.

## 🔒 Безопасность

- PIN хранится в `api/auth.py` (замени `1234` на свой)
- Токены сессий — простые UUID, сохраняются в `localStorage`
- В продакшене добавь переменные окружения в Vercel Dashboard

## 💡 Идеи для развития

- Добавить WebRTC для голоса прямо в браузере
- Telegram-бот как мост между Vercel и локальным ПК
- Webhook на n8n / Make для автоматизаций

---

**Сделано как отдельная выгрузка из MARK L (ai22) на Vercel.**
