@echo off
REM Stop Telegram Bot
REM Location: C:\Users\hharp\OneDrive\Desktop\Agent Factory\scripts\stop_telegram_bot.bat

echo ============================================================
echo Stopping Agent Factory Telegram Bot
echo ============================================================
echo.

REM Find Python processes that might be the bot
echo Searching for Telegram bot processes...
echo.

REM Show Python processes with their PIDs
tasklist | findstr python.exe

echo.
echo ============================================================
echo MANUAL STOP REQUIRED
echo ============================================================
echo.
echo Find the bot PID from the list above and run:
echo   taskkill /PID [pid] /F
echo.
echo Example:
echo   taskkill /PID 12345 /F
echo.
echo The bot should be the Python process using ~18-20MB memory
echo.

pause
