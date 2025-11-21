"""
Setup test script for DefectMaster Bot
Tests all integrations before deployment
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR] {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[WARNING] {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.END}")

async def test_env():
    """Test environment variables"""
    print_info("Testing environment variables...")

    load_dotenv()

    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GOOGLE_API_KEY',
        'GOOGLE_SERVICE_ACCOUNT_FILE',
    ]

    optional_vars = [
        'TINKOFF_TERMINAL_KEY',
        'TINKOFF_SECRET_KEY',
    ]

    all_good = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var} is set")
        else:
            print_error(f"{var} is not set (REQUIRED)")
            all_good = False

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print_success(f"{var} is set")
        else:
            print_warning(f"{var} is not set (optional)")

    return all_good

async def test_google_service_account():
    """Test Google Service Account file"""
    print_info("\nTesting Google Service Account...")

    import json
    from google.oauth2 import service_account

    service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account.json')

    try:
        if not os.path.exists(service_account_file):
            print_error(f"Service account file not found: {service_account_file}")
            return False

        with open(service_account_file) as f:
            data = json.load(f)

        print_success(f"Service account file found: {service_account_file}")
        print_info(f"  Project ID: {data.get('project_id')}")
        print_info(f"  Client Email: {data.get('client_email')}")

        # Try to load credentials
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        print_success("Credentials loaded successfully")

        return True

    except Exception as e:
        print_error(f"Service account error: {e}")
        return False

async def test_google_gemini():
    """Test Google Gemini API"""
    print_info("\nTesting Google Gemini API...")

    try:
        import google.generativeai as genai

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print_error("GOOGLE_API_KEY not set")
            return False

        genai.configure(api_key=api_key)

        # Try to list models
        models = genai.list_models()
        print_success("Google Gemini API is accessible")

        # Check if gemini-1.5-flash is available
        flash_available = any('gemini-1.5-flash' in m.name for m in models)
        if flash_available:
            print_success("gemini-1.5-flash model is available")
        else:
            print_warning("gemini-1.5-flash model not found, but other models are available")

        return True

    except Exception as e:
        print_error(f"Google Gemini API error: {e}")
        return False

async def test_telegram_bot():
    """Test Telegram Bot token"""
    print_info("\nTesting Telegram Bot API...")

    try:
        from aiogram import Bot

        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print_error("TELEGRAM_BOT_TOKEN not set")
            return False

        bot = Bot(token=token)

        # Get bot info
        me = await bot.get_me()
        print_success(f"Bot is accessible: @{me.username}")
        print_info(f"  Bot ID: {me.id}")
        print_info(f"  Bot Name: {me.first_name}")

        await bot.session.close()
        return True

    except Exception as e:
        print_error(f"Telegram Bot API error: {e}")
        return False

async def test_google_sheets_api():
    """Test Google Sheets API access"""
    print_info("\nTesting Google Sheets API...")

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        service_account_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account.json')

        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

        service = build('sheets', 'v4', credentials=credentials)

        # Try to create a test spreadsheet
        spreadsheet = {
            'properties': {
                'title': 'DefectMaster Test Spreadsheet'
            }
        }

        result = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = result['spreadsheetId']

        print_success("Google Sheets API is working")
        print_info(f"  Test spreadsheet created: {spreadsheet_id}")
        print_warning("  Please delete the test spreadsheet manually if needed")

        return True

    except Exception as e:
        print_error(f"Google Sheets API error: {e}")
        return False

async def test_database():
    """Test database initialization"""
    print_info("\nTesting database...")

    try:
        import aiosqlite

        db_path = os.getenv('DATABASE_PATH', 'bot.db')

        # Try to connect and create tables
        async with aiosqlite.connect(db_path) as db:
            await db.execute("SELECT 1")

        print_success("Database is accessible")

        # Test database models
        from bot.database.models import db as database
        await database.init_db()

        print_success("Database tables created successfully")

        return True

    except Exception as e:
        print_error(f"Database error: {e}")
        return False

async def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}DefectMaster Bot - Setup Test{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

    tests = [
        ("Environment Variables", test_env),
        ("Google Service Account", test_google_service_account),
        ("Google Gemini API", test_google_gemini),
        ("Telegram Bot API", test_telegram_bot),
        ("Google Sheets API", test_google_sheets_api),
        ("Database", test_database),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Unexpected error in {name}: {e}")
            results.append((name, False))

    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Test Summary{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")

    print(f"\n{Colors.BLUE}Total: {passed}/{total} tests passed{Colors.END}\n")

    if passed == total:
        print_success("All tests passed! Bot is ready for deployment.")
        return 0
    else:
        print_error("Some tests failed. Please fix the issues before deployment.")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
