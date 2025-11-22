"""
Configuration module for DefectMaster Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Version
BOT_VERSION = "1.4.5"

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Google AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini AI Models Configuration
# GEMINI_FAST_MODEL: Быстрая модель для первичной проверки релевантности фото
# GEMINI_ANALYSIS_MODEL: Точная модель для детального анализа дефектов
GEMINI_FAST_MODEL = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash")
GEMINI_ANALYSIS_MODEL = os.getenv("GEMINI_ANALYSIS_MODEL", "gemini-2.5-pro")

# Google Service Account
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service-account.json")

# Google Drive - папка для загрузки фото
# Создайте папку в Google Drive и поделитесь с email сервисного аккаунта
# Скопируйте ID папки из URL: https://drive.google.com/drive/folders/FOLDER_ID
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

# Google Drive - папка для таблиц (используем ту же папку что и для фото)
GOOGLE_SHEETS_FOLDER_ID = os.getenv("GOOGLE_SHEETS_FOLDER_ID") or GOOGLE_DRIVE_FOLDER_ID

# Google Workspace Shared Drive ID
# Для работы с Google Workspace Shared Drive
GOOGLE_SHARED_DRIVE_ID = os.getenv("GOOGLE_SHARED_DRIVE_ID")

# Google Docs - документ с настройками AI (модели и промпты)
# Создайте Google Doc с настройками и поделитесь с сервисным аккаунтом
# Скопируйте ID документа из URL: https://docs.google.com/document/d/DOCUMENT_ID/edit
GOOGLE_SETTINGS_DOC_ID = os.getenv("GOOGLE_SETTINGS_DOC_ID")

# Photo Storage - локальное хранение фотографий
# Фото сохраняются на сервере и раздаются через Nginx
PHOTO_STORAGE_PATH = os.getenv("PHOTO_STORAGE_PATH", "photos")
PHOTO_BASE_URL = os.getenv("PHOTO_BASE_URL", "https://teamplan.ru/photos")

# Tinkoff
TINKOFF_TERMINAL_KEY = os.getenv("TINKOFF_TERMINAL_KEY")
TINKOFF_SECRET_KEY = os.getenv("TINKOFF_SECRET_KEY")

# Admin
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot.db")

# Credits
FREE_CREDITS = int(os.getenv("FREE_CREDITS", "5"))

# Referral System
# REFERRAL_BONUS_INVITER - бонус пригласителю (начисляется при первом релевантном анализе приглашенного)
# REFERRAL_BONUS_INVITED - бонус приглашенному (начисляется сразу при регистрации)
REFERRAL_BONUS_INVITER = int(os.getenv("REFERRAL_BONUS_INVITER", "5"))
REFERRAL_BONUS_INVITED = int(os.getenv("REFERRAL_BONUS_INVITED", "5"))

# Pricing (in rubles)
PRICING = {
    "small": {"credits": 20, "price": 199},
    "medium": {"credits": 50, "price": 399},
    "large": {"credits": 100, "price": 699}
}

# Google Sheets
SPREADSHEET_TEMPLATE_NAME = "СтройКонтроль"
SHEET_HEADERS = [
    "Дата и Время",
    "Объект / Контекст",
    "Наименование дефекта",
    "Местонахождение",
    "Критичность",
    "Вероятная причина",
    "Нарушение (СНиП/ГОСТ)",
    "Рекомендация",
    "Экспертное заключение",
    "Фото"
]
