# PROJECT_STATE: dailypriceup

## Overview
`dailypriceup` is an automated workflow that fetches real estate (apartment) transaction data from a Korean public API, processes it to find specific trends (e.g., general price updates, new lows), generates YouTube Shorts videos (with images and background music), and uploads them automatically to YouTube.

## Directory Structure
- `scripts/`: Contains the core logic scripts (Python & Bash).
- `data/`: Contains the SQLite database (`apt_trades.db`), generated images/videos, BGM files, and execution logs (`cron.log`).

## Core Workflows
The main entry point is `scripts/run_daily_priceup.sh` which executes the pipeline:
1. **`daily_price_check.py`**: Fetches apartment trades from `apis.data.go.kr`, updates the SQLite DB, generates PNG images (e.g., top10, rate), and produces a video (`daily_shorts_final.mp4`).
2. **`daily_price_check_new_low.py`**: A variant focusing on "new low" or bottom 10 trades, generating `daily_shorts_final_low.mp4`.
3. **`upload_youtube_low.py` & `upload_youtube.py`**: Uploads the generated videos to YouTube using the YouTube Data API.

## Recent States & Issues (from `cron.log`)
- **Success:** The pipeline is currently successfully completing all tasks, including generating videos and uploading to YouTube (recent videos: lzWCd4OWTYU, dAq2wLw1aKk on Aug 6).
- **Warnings / Tech Debt:**
  - **Python 3.9 EOL:** Multiple warnings from `google.api_core`, `google.auth`, and `google.oauth2` indicating that Python 3.9 is past EOL and not supported. A Python upgrade (>= 3.10) is recommended.
  - **OpenSSL Mismatch:** `urllib3` is emitting a `NotOpenSSLWarning` because it only supports OpenSSL 1.1.1+, but the `ssl` module is compiled with 'LibreSSL 2.8.3' (standard on macOS older setups/default python).
