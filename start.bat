@echo off
echo Starting DefectMaster Bot...
echo.

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate.bat
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo Error: .env file not found!
    echo Please copy .env.example to .env and fill in the values
    pause
    exit /b 1
)

REM Run the bot
python main.py

pause
