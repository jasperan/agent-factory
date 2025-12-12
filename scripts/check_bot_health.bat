@echo off
REM Health Check Script for Telegram Bot
REM Can be scheduled via Task Scheduler to run every 5 minutes

curl -s http://localhost:9876/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    REM Bot is running
    exit /b 0
) else (
    REM Bot is down - log and optionally restart
    echo [%date% %time%] Bot health check FAILED >> C:\Users\hharp\OneDrive\Desktop\Agent Factory\bot_health.log

    REM Uncomment to auto-restart:
    REM cd /d "C:\Users\hharp\OneDrive\Desktop\Agent Factory"
    REM start /B poetry run python -m agent_factory.integrations.telegram

    exit /b 1
)
