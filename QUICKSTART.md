# Быстрый старт DefectMaster Bot

Минимальная инструкция для запуска бота за 10 минут.

## Шаг 1: Установка зависимостей

```bash
# Клонировать репозиторий
git clone <repo-url> defectmaster-bot
cd defectmaster-bot

# Создать виртуальное окружение
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
```

## Шаг 2: Получение токенов и ключей

### Telegram Bot Token
1. Открыть [@BotFather](https://t.me/BotFather)
2. Отправить `/newbot`
3. Следовать инструкциям
4. Скопировать токен

### Google Gemini API Key
1. Открыть [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Нажать "Create API Key"
3. Скопировать ключ

### Google Service Account
1. Открыть [Google Cloud Console](https://console.cloud.google.com/)
2. Создать новый проект
3. Включить APIs:
   - Google Sheets API
   - Google Drive API
4. Создать Service Account:
   - IAM & Admin → Service Accounts → Create
   - Role: Editor
   - Keys → Add Key → Create new key → JSON
5. Скачать JSON файл и сохранить как `service-account.json`

## Шаг 3: Настройка конфигурации

```bash
# Создать .env
cp .env.example .env

# Открыть в редакторе
nano .env  # или любой другой редактор
```

Заполнить минимум:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
```

## Шаг 4: Тестирование

```bash
# Запустить тесты
python test_setup.py
```

Все тесты должны пройти успешно (зеленые галочки).

## Шаг 5: Запуск бота

```bash
# Активировать окружение (если не активно)
source venv/bin/activate

# Запустить бота
python main.py
```

## Шаг 6: Проверка работы

1. Найти бота в Telegram по username
2. Отправить `/start`
3. Получить приветствие и ссылку на Google Таблицу
4. Установить контекст (например: "Тестовый объект")
5. Отправить фото строительного объекта
6. Получить анализ дефектов

## Остановка бота

```
Ctrl+C
```

## Развертывание на сервере

Для продакшн развертывания см. [DEPLOYMENT.md](DEPLOYMENT.md)

Основные способы:
- **systemd** (Linux) - рекомендуется
- **Docker** - удобно для изоляции
- **screen** - для быстрого тестирования

## Устранение проблем

### Бот не отвечает
- Проверьте токен Telegram
- Проверьте логи: `tail -f main.log`

### Ошибка Google Sheets
- Проверьте service-account.json
- Убедитесь, что APIs включены в Google Cloud

### Ошибка Gemini API
- Проверьте GOOGLE_API_KEY
- Проверьте квоты в Google AI Studio

## Дополнительная информация

- [README.md](README.md) - Полная документация
- [DEPLOYMENT.md](DEPLOYMENT.md) - Инструкция по развертыванию
- [test_setup.py](test_setup.py) - Скрипт тестирования

## Поддержка

Если возникли проблемы:
1. Запустите `python test_setup.py`
2. Проверьте логи бота
3. Убедитесь, что все токены валидны
