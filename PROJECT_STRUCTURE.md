# Структура проекта DefectMaster Bot

```
Stroykontrol_mvp_01/
│
├── 📁 bot/                          # Основной пакет бота
│   ├── __init__.py
│   │
│   ├── 📁 database/                 # Модуль базы данных
│   │   ├── __init__.py
│   │   └── models.py                # SQLite модели (users, payments, history)
│   │
│   ├── 📁 handlers/                 # Обработчики команд и сообщений
│   │   ├── __init__.py
│   │   ├── common.py                # /start, /help, /balance, /table
│   │   ├── photo.py                 # Обработка фотографий
│   │   └── payments.py              # Обработка платежей
│   │
│   ├── 📁 services/                 # Внешние сервисы
│   │   ├── __init__.py
│   │   ├── ai_service.py            # Google Gemini интеграция
│   │   ├── google_service.py        # Google Sheets + Drive API
│   │   └── payment_service.py       # Tinkoff Merchant API
│   │
│   └── 📁 utils/                    # Утилиты (зарезервировано)
│       └── __init__.py
│
├── 📄 config.py                     # Конфигурация приложения
├── 📄 main.py                       # Точка входа в приложение
│
├── 📋 requirements.txt              # Python зависимости
├── 📋 .env.example                  # Шаблон переменных окружения
├── 📋 .gitignore                    # Игнорируемые файлы Git
│
├── 📖 README.md                     # Основная документация
├── 📖 QUICKSTART.md                 # Быстрый старт за 10 минут
├── 📖 DEPLOYMENT.md                 # Подробный деплой на сервер
├── 📖 EXAMPLES.md                   # Примеры использования
├── 📖 CHANGELOG.md                  # История изменений
├── 📖 PROJECT_STRUCTURE.md          # Этот файл
├── 📖 LICENSE                       # MIT лицензия
│
├── 🔧 test_setup.py                 # Скрипт проверки настроек
│
├── 🚀 setup.sh                      # Установка на Linux/Mac
├── 🚀 setup.bat                     # Установка на Windows
├── 🚀 start.sh                      # Запуск на Linux/Mac
├── 🚀 start.bat                     # Запуск на Windows
│
├── 🐳 Dockerfile                    # Docker образ
├── 🐳 docker-compose.yml            # Docker Compose конфигурация
│
└── 🔧 defectmaster-bot.service      # systemd service файл
```

## Описание модулей

### 🤖 bot/

Основной пакет бота, содержащий всю бизнес-логику.

#### database/

**models.py** - Модели базы данных SQLite:
- `Database` - класс для работы с БД
- Таблицы: `users`, `payments`, `analysis_history`
- Асинхронные методы для CRUD операций

#### handlers/

**common.py** - Обработчики основных команд:
- `/start` - Регистрация, создание таблицы, приветствие
- `/new` - Установка нового контекста объекта
- `/balance` - Показ баланса и пакетов оплаты
- `/table` - Получение ссылки на Google Таблицу
- `/help` - Справка по использованию

**photo.py** - Обработка фотографий:
- Прием фото от пользователя
- Проверка баланса и контекста
- Отправка фото в AI для анализа
- Загрузка фото на Google Drive
- Запись результатов в Google Sheets
- Форматирование ответа пользователю

**payments.py** - Обработка платежей:
- Callback на кнопки покупки пакетов
- Создание платежа через Tinkoff API
- Генерация ссылки на оплату

#### services/

**ai_service.py** - Интеграция с Google Gemini:
- Класс `AIService` для работы с AI
- Системный промпт для инженера стройнадзора
- Анализ фото на релевантность
- Выявление дефектов с привязкой к нормам РФ
- Форматирование результатов для Telegram

**google_service.py** - Google Sheets/Drive:
- Класс `GoogleService` для работы с Google APIs
- Создание персональных таблиц пользователей
- Форматирование заголовков таблицы
- Загрузка фото на Google Drive
- Добавление строк с результатами анализа

**payment_service.py** - Tinkoff платежи:
- Класс `PaymentService` для Tinkoff API
- Инициализация платежей
- Генерация токенов безопасности
- Проверка статуса платежей
- Валидация уведомлений (webhooks)

### 📄 Корневые файлы

**config.py** - Центральная конфигурация:
- Загрузка переменных окружения
- Константы (цены, заголовки таблиц)
- Настройки сервисов

**main.py** - Точка входа:
- Инициализация бота и диспетчера
- Регистрация роутеров
- Настройка команд бота
- Запуск polling

## Поток данных

```
┌─────────────┐
│ Пользователь│
└──────┬──────┘
       │ Отправляет фото
       ▼
┌─────────────────┐
│  Telegram Bot   │
│   (aiogram)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  photo.py       │─────▶│  Database    │
│  (handler)      │      │  (SQLite)    │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│  ai_service.py  │─────▶ Google Gemini API
│  (AI анализ)    │       (Анализ изображения)
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│ google_service  │─────▶│ Google Drive │
│                 │      │ (Фото)       │
│                 │      └──────────────┘
│                 │
│                 │─────▶┌──────────────┐
│                 │      │Google Sheets │
└─────────────────┘      │ (Отчеты)     │
                         └──────────────┘
```

## Зависимости

### Python пакеты (requirements.txt)

```
aiogram==3.13.1                  # Telegram Bot Framework
aiosqlite==0.20.0                # Асинхронный SQLite
python-dotenv==1.0.1             # Переменные окружения
google-generativeai==0.8.3       # Google Gemini AI
google-auth==2.35.0              # Google аутентификация
google-auth-oauthlib==1.2.1      # OAuth для Google
google-auth-httplib2==0.2.0      # HTTP для Google
google-api-python-client==2.149.0 # Google API клиент
Pillow==10.4.0                   # Обработка изображений
aiohttp==3.10.5                  # Асинхронный HTTP
aiofiles==24.1.0                 # Асинхронная работа с файлами
```

### Внешние сервисы

1. **Telegram Bot API** - Интерфейс бота
2. **Google Gemini API** - AI анализ
3. **Google Sheets API** - Создание отчетов
4. **Google Drive API** - Хранение фото
5. **Tinkoff Merchant API** - Платежи

## Переменные окружения (.env)

```env
# Обязательные
TELEGRAM_BOT_TOKEN          # Токен Telegram бота
GOOGLE_API_KEY              # Ключ Google Gemini
GOOGLE_SERVICE_ACCOUNT_FILE # Путь к service-account.json

# Опциональные
TINKOFF_TERMINAL_KEY        # Терминал Tinkoff
TINKOFF_SECRET_KEY          # Секретный ключ Tinkoff
ADMIN_IDS                   # ID администраторов
DATABASE_PATH               # Путь к БД (по умолчанию: bot.db)
FREE_CREDITS                # Бесплатных анализов (по умолчанию: 5)
```

## Безопасность

### Файлы с секретами (НЕ коммитить!)

- `.env` - переменные окружения
- `service-account.json` - Google credentials
- `bot.db` - база данных с пользователями

### .gitignore защищает

- Все `*.db` файлы
- `.env`
- `service-account.json`
- `__pycache__/` и `*.pyc`
- Virtual environment (`venv/`)

## Расширение функционала

### Добавление новой команды

1. Создать обработчик в `bot/handlers/`
2. Зарегистрировать роутер в `main.py`
3. Добавить команду в `bot.set_my_commands()`

### Добавление нового сервиса

1. Создать класс в `bot/services/`
2. Инициализировать в конце файла: `service_name = ServiceClass()`
3. Импортировать в нужные handlers

### Изменение AI промпта

Редактировать `SYSTEM_PROMPT` в `bot/services/ai_service.py`

### Изменение структуры таблицы

Редактировать `SHEET_HEADERS` в `config.py`

## Мониторинг и логи

### Где смотреть логи

**Локально:**
```bash
python main.py  # Логи в stdout
```

**systemd:**
```bash
sudo journalctl -u defectmaster-bot -f
```

**Docker:**
```bash
docker-compose logs -f
```

### Что логируется

- Запуск/остановка бота
- Ошибки API
- Создание пользователей
- Анализ фотографий
- Платежи

## Производительность

### Оптимизации

- Асинхронная архитектура (aiogram + aiosqlite)
- Кэширование результатов (по желанию)
- Прямые ссылки на фото (Google Drive)
- Batch операции с БД

### Масштабирование

- Horizontal scaling: запуск нескольких инстансов
- Database: миграция на PostgreSQL
- Cache: добавление Redis
- Load balancer: nginx upstream

## Лицензия

MIT License - см. [LICENSE](LICENSE)

---

*Последнее обновление: 2025-11-20*
