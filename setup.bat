@echo off
echo DefectMaster Bot - Setup Script (Windows)
echo ==========================================
echo.

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo Error: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Create .env if not exists
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file and fill in your API keys!
)

echo.
echo ==========================================
echo Setup completed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Place service-account.json in the project root
echo 3. Run: start.bat
echo.
pause
