@echo off
REM Start Telegram Bot with PID Management

echo ============================================================
echo Starting Agent Factory Telegram Bot
echo ============================================================

cd /d "C:\Users\hharp\OneDrive\Desktop\Agent Factory"

REM Check if bot is already running via health endpoint
curl -s http://localhost:9876/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [WARNING] Bot already running
    pause
    exit /b 1
)

echo [OK] Starting bot...
start /B poetry run python -m agent_factory.integrations.telegram

timeout /t 3 /nobreak >nul

curl -s http://localhost:9876/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Bot started
) else (
    echo [ERROR] Bot failed to start
)

pause
