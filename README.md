# DefectMaster Bot

Telegram-бот для автоматического выявления строительных дефектов по фотографиям с использованием AI (Google Gemini) и генерацией отчетов в Google Таблицах.

## Возможности

- Анализ фотографий строительных объектов с помощью Google Gemini AI
- Выявление дефектов с привязкой к нормам РФ (СНиП, ГОСТ, СП)
- Автоматическое заполнение Google Таблиц с результатами
- Загрузка фотографий на Google Drive
- Система балансов и платежей через Tinkoff
- Контекстная привязка дефектов к объектам

## Стек технологий

- **Python 3.10+**
- **aiogram 3.x** - асинхронный фреймворк для Telegram Bot API
- **SQLite** - локальная база данных
- **Google Gemini 1.5 Flash** - AI для анализа изображений
- **Google Sheets API** - создание и заполнение отчетов
- **Google Drive API** - хранение фотографий
- **Tinkoff API** - обработка платежей

## Установка и настройка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd Stroykontrol_mvp_01
```

### 2. Установка зависимостей

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. Настройка Telegram Bot

1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен бота
3. Сохраните токен - он понадобится для `.env`

### 4. Настройка Google Cloud

#### 4.1. Создание проекта Google Cloud

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект
3. Включите следующие API:
   - Google Sheets API
   - Google Drive API

#### 4.2. Создание Service Account

1. В Google Cloud Console перейдите в **IAM & Admin** → **Service Accounts**
2. Нажмите **Create Service Account**
3. Заполните данные:
   - Name: `defectmaster-bot`
   - Description: `Service account for DefectMaster Bot`
4. Нажмите **Create and Continue**
5. Grant access: **Editor** (или более ограниченные права)
6. Нажмите **Done**
7. Нажмите на созданный аккаунт → **Keys** → **Add Key** → **Create new key**
8. Выберите **JSON** и скачайте файл
9. Сохраните файл как `service-account.json` в корне проекта
10. **ВАЖНО:** Скопируйте email сервисного аккаунта (например, `defectmaster-bot@project-id.iam.gserviceaccount.com`) - он понадобится на следующем шаге

#### 4.3. Создание папки для фото в Google Drive

**ВАЖНО:** Сервисные аккаунты не имеют собственного хранилища, поэтому нужно создать папку в обычном Google Drive:

1. Откройте [Google Drive](https://drive.google.com)
2. Создайте новую папку (например, "DefectMaster Photos")
3. Нажмите правой кнопкой на папку → **Поделиться** (Share)
4. Добавьте email сервисного аккаунта из шага 4.2.10
5. Дайте права **Редактор** (Editor)
6. Нажмите **Отправить**
7. Откройте папку и скопируйте ID из URL:
   - URL будет вида: `https://drive.google.com/drive/folders/1a2B3c4D5e6F7g8H9i0J`
   - Folder ID: `1a2B3c4D5e6F7g8H9i0J`
8. Сохраните этот ID - он понадобится для `.env`

#### 4.4. Получение Google Gemini API Key

1. Перейдите в [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Нажмите **Create API Key**
3. Скопируйте ключ - он понадобится для `.env`

### 5. Настройка Tinkoff (опционально для тестирования)

1. Зарегистрируйтесь в [Tinkoff Merchant](https://www.tinkoff.ru/business/internet-acquiring/)
2. Получите:
   - Terminal Key
   - Secret Key
3. Для тестирования используйте тестовые ключи из документации Tinkoff

### 6. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните все значения в `.env`:

```env
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Google AI (Gemini)
GOOGLE_API_KEY=AIzaSy...

# Google Service Account
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json

# Google Drive Folder ID (из шага 4.3)
GOOGLE_DRIVE_FOLDER_ID=1a2B3c4D5e6F7g8H9i0J

# Tinkoff Payments
TINKOFF_TERMINAL_KEY=your_terminal_key
TINKOFF_SECRET_KEY=your_secret_key

# Admin IDs
ADMIN_IDS=123456789

# Database
DATABASE_PATH=bot.db

# Free credits
FREE_CREDITS=5
```

### 7. Запуск бота

#### Локальный запуск (для тестирования)

```bash
python main.py
```

#### Запуск на сервере (production)

##### Вариант 1: systemd (рекомендуется для Linux)

Создайте файл `/etc/systemd/system/defectmaster-bot.service`:

```ini
[Unit]
Description=DefectMaster Telegram Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/Stroykontrol_mvp_01
ExecStart=/path/to/Stroykontrol_mvp_01/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Запустите сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable defectmaster-bot
sudo systemctl start defectmaster-bot
sudo systemctl status defectmaster-bot
```

##### Вариант 2: screen (простой способ)

```bash
screen -S defectmaster
python main.py
# Нажмите Ctrl+A, затем D для отключения
```

Подключиться обратно:
```bash
screen -r defectmaster
```

##### Вариант 3: Docker (опционально)

Создайте `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Запустите:

```bash
docker build -t defectmaster-bot .
docker run -d --name defectmaster-bot --restart always \
  --env-file .env \
  -v $(pwd)/bot.db:/app/bot.db \
  -v $(pwd)/service-account.json:/app/service-account.json \
  defectmaster-bot
```

## Структура проекта

```
Stroykontrol_mvp_01/
├── bot/
│   ├── database/
│   │   ├── __init__.py
│   │   └── models.py          # Модели БД
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── common.py          # Команды /start, /help и т.д.
│   │   ├── photo.py           # Обработка фото
│   │   └── payments.py        # Обработка платежей
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py      # Google Gemini интеграция
│   │   ├── google_service.py  # Google Sheets/Drive
│   │   └── payment_service.py # Tinkoff платежи
│   └── utils/
│       └── __init__.py
├── .env                       # Переменные окружения (не в git)
├── .env.example               # Шаблон .env
├── .gitignore
├── config.py                  # Конфигурация
├── main.py                    # Точка входа
├── requirements.txt           # Зависимости
├── service-account.json       # Google credentials (не в git)
└── README.md
```

## Использование

### Команды бота

- `/start` - Регистрация и создание персональной таблицы
- `/new` - Установить новый объект/контекст
- `/balance` - Проверить баланс и купить кредиты
- `/table` - Получить ссылку на таблицу отчетов
- `/help` - Справка

### Процесс работы

1. Пользователь отправляет `/start`
2. Бот создает Google Таблицу и дает 5 бесплатных анализов
3. Пользователь устанавливает контекст (например, "ЖК Пионер, 5 этаж")
4. Пользователь присылает фото стройки
5. AI анализирует фото и находит дефекты
6. Результаты записываются в Google Таблицу
7. Пользователь получает краткий отчет в чате

## Тестирование

### Тест AI анализа

Отправьте фото:
- ✅ Строительный объект с дефектами → должно найти дефекты и записать в таблицу
- ❌ Фото кота/еды → должно ответить шуткой, не списать баланс

### Тест интеграций

1. **Google Sheets**: проверьте создание таблицы при `/start`
2. **Google Drive**: проверьте наличие фото по ссылке в таблице
3. **Tinkoff**: протестируйте платеж (в тестовом режиме)

## Мониторинг и логи

Логи бота:

```bash
# systemd
sudo journalctl -u defectmaster-bot -f

# screen
screen -r defectmaster
```

## Безопасность

- Никогда не коммитьте `.env` и `service-account.json`
- Используйте переменные окружения для всех секретов
- Ограничьте права Service Account минимально необходимыми
- Регулярно обновляйте зависимости: `pip install --upgrade -r requirements.txt`

## Поддержка

При возникновении проблем:

1. Проверьте логи бота
2. Убедитесь, что все API ключи валидны
3. Проверьте права Service Account в Google Cloud
4. Проверьте баланс API квот в Google AI Studio

## Лицензия

MIT License

## Авторы

DefectMaster Bot - AI-powered construction supervision assistant
