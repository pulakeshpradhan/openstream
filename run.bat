@echo off
setlocal
cd /d %~dp0

:: Check if python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

:: Option: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating Virtual Environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate

:: Check if requirements are installed
if exist "requirements.txt" (
    echo [INFO] Updating Dependencies...
    pip install -r requirements.txt
)

:: Launch the Streamlit App
echo [1] Standard Mode (Service Account/ADC)
echo [2] OAuth Mode (User Login)
set /p choice="Select version to run [1 or 2]: "

if "%choice%"=="2" (
    echo [INFO] Launching OAuth-specific Version...
    streamlit run streamlit_oauth_app.py
) else (
    echo [INFO] Launching Standard Version...
    streamlit run app.py
)

:: Keep the window open if the app crashes
if %errorlevel% neq 0 (
    echo [ERROR] Application failed to start.
    pause
)

endlocal
