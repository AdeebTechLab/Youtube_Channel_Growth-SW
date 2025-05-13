@echo off
echo ===== YouTube Growth Tool Launcher =====
echo.

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt

:: Install Playwright browsers if needed
echo Installing Playwright browsers...
python -m playwright install chromium

:: Run the application
echo.
echo Starting application...
python main_ui.py

:: Keep the window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while running the application.
    pause
)
