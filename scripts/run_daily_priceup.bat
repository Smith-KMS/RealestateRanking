@echo off
rem ---------------------------------------------------------------------------
:: dailypriceup execution script (Windows Batch)
rem ---------------------------------------------------------------------------

:: Move to the project root directory relative to this script's folder (scripts\..)
cd /d "%~dp0.."

:: Execute Python scripts using the virtual environment
.venv\Scripts\python.exe scripts\daily_price_check.py >> data\cron.log 2>&1
.venv\Scripts\python.exe scripts\upload_youtube.py >> data\cron.log 2>&1

.venv\Scripts\python.exe scripts\daily_price_check_new_low.py >> data\cron.log 2>&1
.venv\Scripts\python.exe scripts\upload_youtube_low.py >> data\cron.log 2>&1

:: Log completion time
echo Cron job completed at %date% %time% >> data\cron.log
