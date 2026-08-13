#!/bin/bash
# ---------------------------------------------------------------------------
# dailypriceup execution script
# ---------------------------------------------------------------------------

cd /Users/smithkwon/.openclaw/workspace/dailypriceup

# Activate Python 3.11 virtual environment to fix Python EOL and SSL warnings
source venv/bin/activate

# Execute the main script
python scripts/daily_price_check.py >> data/cron.log 2>&1
python scripts/upload_youtube.py >> data/cron.log 2>&1

python scripts/daily_price_check_new_low.py >> data/cron.log 2>&1
python scripts/upload_youtube_low.py >> data/cron.log 2>&1

echo "Cron job completed at $(date)" >> data/cron.log
