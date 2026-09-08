import requests
import xml.etree.ElementTree as ET
import urllib3
import sqlite3
import datetime
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import subprocess
import json
import shutil

def get_ffmpeg_path():
    path = shutil.which("ffmpeg")
    if path:
        return path
    winget_dir = "C:/Users/kwonm/AppData/Local/Microsoft/WinGet/Packages"
    if os.path.exists(winget_dir):
        for root, dirs, files in os.walk(winget_dir):
            if "ffmpeg.exe" in files:
                return os.path.join(root, "ffmpeg.exe").replace("\\", "/")
    return "ffmpeg"


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Config
api_key = "095266ca1cc9b437a6d4fab0f424668948b76a8a7981b5260d6e6ffaf48886d3"
url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
headers = {'User-Agent': 'Mozilla/5.0'}
db_path = "C:/Users/kwonm/workspace/RealestateRanking/data/apt_trades.db"
data_path = "C:/Users/kwonm/workspace/RealestateRanking/data/daily_lists"

regions = {
    "종로구": "11110", "중구": "11140", "용산구": "11170", "성동구": "11200",
    "광진구": "11215", "동대문구": "11230", "중랑구": "11260", "성북구": "11290",
    "강북구": "11305", "도봉구": "11320", "노원구": "11350", "은평구": "11380",
    "서대문구": "11410", "마포구": "11440", "양천구": "11470", "강서구": "11500",
    "구로구": "11530", "금천구": "11545", "영등포구": "11560", "동작구": "11590",
    "관악구": "11620", "서초구": "11650", "강남구": "11680", "송파구": "11710",
    "강동구": "11740", "분당구": "41135"
}

def format_price(amount):
    uk = amount // 10000
    man = amount % 10000
    if uk > 0 and man > 0: return f"{uk}억 {man}만"
    elif uk > 0: return f"{uk}억"
    else: return f"{man}만"

def get_font(size):
    for f in ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc", "malgun.ttf"]:
        try: return ImageFont.truetype(f, size)
        except: pass
    return ImageFont.load_default()

def wrap_text_by_char(draw, text, font, max_width, max_lines=2):
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
        
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last_line = lines[-1]
        while len(last_line) > 1:
            last_line = last_line[:-1]
            t = last_line + ".."
            bbox = draw.textbbox((0, 0), t, font=font)
            if bbox[2] - bbox[0] <= max_width:
                lines[-1] = t
                break
    return lines

# 1. Target months
today = datetime.date.today()
this_month = today.replace(day=1)
last_month = this_month - datetime.timedelta(days=1)
target_months = [last_month.strftime("%Y%m"), today.strftime("%Y%m")]

# 2. Existing IDs
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT id FROM trades")
existing_ids = {row[0] for row in cur.fetchall()}

new_trades = []
all_trades = []

today_new_trade_filename = f"new_trade_{today.strftime('%Y_%m_%d')}.json"
today_new_trade_load_path = os.path.join(data_path, today_new_trade_filename)

if not os.path.exists(today_new_trade_load_path):
    print("Fetching latest data from API...")
    for deal_ymd in target_months:
        for region_name, lawd_cd in regions.items():
            params = {'serviceKey': api_key, 'LAWD_CD': lawd_cd, 'DEAL_YMD': deal_ymd, 'numOfRows': '2000', 'pageNo': '1'}
            try:
                res = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
                if res.status_code == 200:
                    root = ET.fromstring(res.content)
                    for item in root.findall('.//item'):
                        try:
                            apt_nm = item.findtext('aptNm', '').strip()
                            deal_amount_str = item.findtext('dealAmount', '0').replace(',', '').strip()
                            deal_amount = int(deal_amount_str)
                            exclu_use_ar = float(item.findtext('excluUseAr', '0'))
                            floor = int(item.findtext('floor', '0'))
                            deal_day = int(item.findtext('dealDay', '0'))
                            jibun = item.findtext('jibun', '').strip()
                            umd_nm = item.findtext('umdNm', '').strip()
                            build_year = int(item.findtext('buildYear', '0') or '0')
                            
                            unique_id = f"{lawd_cd}_{deal_ymd}_{deal_day}_{apt_nm}_{exclu_use_ar}_{floor}_{deal_amount}"
                            all_trades.append({
                                'id': unique_id, 'region_name': region_name, 'lawd_cd': lawd_cd,
                                'deal_ymd': deal_ymd, 'apt_name': apt_nm, 'exclu_use_ar': exclu_use_ar,
                                'deal_amount': deal_amount, 'floor': floor, 'deal_day': deal_day,
                                'jibun': jibun, 'umd_nm': umd_nm, 'build_year': build_year
                            })
                            if unique_id not in existing_ids:
                                new_trades.append({
                                    'id': unique_id, 'region_name': region_name, 'lawd_cd': lawd_cd,
                                    'deal_ymd': deal_ymd, 'apt_name': apt_nm, 'exclu_use_ar': exclu_use_ar,
                                    'deal_amount': deal_amount, 'floor': floor, 'deal_day': deal_day,
                                    'jibun': jibun, 'umd_nm': umd_nm, 'build_year': build_year
                                })
                        except: pass
            except: pass
real_update_data = True
print(f"Found {len(all_trades)} records from data base.")
print(f"Found {len(new_trades)} newly updated records.")

if all_trades:
    filename = f"all_trade_{today.strftime('%Y_%m_%d')}.json"
    out_path = os.path.join(data_path, filename)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_trades, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        print(f"Saved {len(all_trades)} all trades to {out_path}")
        print(f"Failed to save all trades to JSON: {e}")
    

if new_trades:
    out_path = today_new_trade_load_path

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(new_trades, f, ensure_ascii=False, indent=2, default=str)
        print(f"Saved {len(new_trades)} new trades to {out_path}")
    except Exception as e:
        print(f"Failed to save new trades to JSON: {e}")
else:
    real_update_data = False
    try:
        load_path = today_new_trade_load_path

        if os.path.exists(load_path):
            with open(load_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                new_trades = loaded
                print(f"Loaded {len(new_trades)} records from {load_path}")
            else:
                print(f"Unexpected format in {load_path}, expected a list.")
        else:
            print(f"No file found at {load_path}; no new_trades to process.")
    except Exception as e:
        print(f"Error loading new_trades from JSON: {e}")

# 3. Evaluate ATH
ath_list = []
two_years_ago_date = today.replace(year=today.year - 2)
two_years_ago = two_years_ago_date.strftime('%Y-%m-%d')
for t in new_trades:
    cur.execute('''
        SELECT deal_amount, deal_year, deal_month, deal_day 
        FROM trades 
        WHERE lawd_cd=? AND apt_name=? AND abs(exclu_use_ar - ?) < 0.1 
        AND printf('%04d-%02d-%02d', deal_year, deal_month, deal_day) >= ?
        ORDER BY deal_amount ASC LIMIT 1
    ''', (t['lawd_cd'], t['apt_name'], t['exclu_use_ar'], two_years_ago))
    old_record = cur.fetchone()
    
    if old_record:
        old_low = old_record[0]
        if t['deal_amount'] < old_low:
            rate = (t['deal_amount'] - old_low) / old_low * 100
            t['old_low'] = old_low
            t['old_date'] = f"{old_record[1]}.{old_record[2]:02d}.{old_record[3]:02d}"
            t['new_date'] = f"{t['deal_ymd'][:4]}.{t['deal_ymd'][4:6]}.{t['deal_day']:02d}"
            t['rate'] = rate
            ath_list.append(t)

if ath_list:
    filename = f"low_ath_list_{today.strftime('%Y_%m_%d')}.json"
    out_path = os.path.join(data_path, filename)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(ath_list, f, ensure_ascii=False, indent=2, default=str)
        print(f"Saved {len(ath_list)} ATH records to {out_path}")
    except Exception as e:
        print(f"Failed to save ATH records to JSON: {e}")
else:
    filename = f"low_ath_list_{today.strftime('%Y_%m_%d')}.json"
    load_path = os.path.join(data_path, filename)
    try:
        if os.path.exists(load_path):
            with open(load_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                ath_list = loaded
                print(f"Loaded {len(ath_list)} ATH records from {load_path}")
            else:
                print(f"Unexpected format in {load_path}, expected a list.")
        else:
            print(f"No ATH file found at {load_path}; no ATH records to process.")
    except Exception as e:
        print(f"Error loading ATH records from JSON: {e}")

# 4. Update DB
count_inserted = 0
if real_update_data:
    for t in new_trades:
        try:
            cur.execute('''
                INSERT OR IGNORE INTO trades 
                (id, region_name, lawd_cd, deal_ymd, apt_name, jibun, exclu_use_ar, 
                deal_amount, deal_year, deal_month, deal_day, floor, build_year, umd_nm)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (t['id'], t['region_name'], t['lawd_cd'], t['deal_ymd'], t['apt_name'], 
                t['jibun'], t['exclu_use_ar'], t['deal_amount'], int(t['deal_ymd'][:4]), 
                int(t['deal_ymd'][4:6]), t['deal_day'], t['floor'], t['build_year'], t['umd_nm']))
            count_inserted += 1
        except: pass
    print(f"Inserted {count_inserted} records into DB. Found {len(ath_list)} ATH records.")
conn.commit()
conn.close()


# 5 & 6. Ranking & Generate Image Function
def generate_ranking_image(top_data, title, out_filename):
    w, h = 1080, 1920
    img = Image.new('RGB', (w, h), color=(20, 20, 28))
    draw = ImageDraw.Draw(img)

    font_title = get_font(65)
    font_sub = get_font(40)
    font_col = get_font(30)
    font_rank = get_font(45)
    font_row = get_font(35)
    font_date = get_font(26)

    def draw_c(text, x, y, font, color):
        bbox = draw.textbbox((0, 0), str(text), font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x - tw/2, y - th/2), str(text), font=font, fill=color)

    # Header
    draw_c(title, w/2, 170, font_title, (255, 215, 0))
    draw_c(f"({today.strftime('%Y년 %m월 %d일')} 업데이트, 전용 면적, 최근 2년)", w/2, 270, font_sub, (200, 200, 200))

    # Table Headers
    cols = [(70, "순위"), (310, "아파트 (지역)"), (610, "신규거래(일자)"), (820, "이전최저(일자)"), (990, "하락률")]
    y_start = 380
    draw.line([(40, y_start-30), (w-40, y_start-30)], fill=(100, 100, 150), width=3)
    for cx, cname in cols:
        draw_c(cname, cx, y_start, font_col, (150, 180, 255))
    draw.line([(40, y_start+30), (w-40, y_start+30)], fill=(100, 100, 150), width=3)

    # Rows
    y = y_start + 85
    row_h = 135
    if not top_data:
        draw_c("신저가 거래 없음", w/2, y + 200, font_title, (180, 180, 180))
    for i, item in enumerate(top_data, 1):
        color = (255, 100, 100) if i <= 3 else (255, 255, 255)
        
        # Rank
        draw_c(f"{i}", cols[0][0], y, font_rank, color)
        
        # Apt & Region
        apt_str = f"{item['apt_name']} ({int(item['exclu_use_ar']/3.3)}평)"
        reg_str = f"{item['region_name']} {item['umd_nm']}"
        apt_lines = wrap_text_by_char(draw, apt_str, font_row, 340, 2)
        
        if len(apt_lines) == 1:
            draw_c(apt_lines[0], cols[1][0], y - 20, font_row, (255, 255, 255))
            draw_c(reg_str, cols[1][0], y + 25, font_date, (180, 180, 180))
        else:
            draw_c(apt_lines[0], cols[1][0], y - 35, font_row, (255, 255, 255))
            draw_c(apt_lines[1], cols[1][0], y + 5, font_row, (255, 255, 255))
            draw_c(reg_str, cols[1][0], y + 45, font_date, (180, 180, 180))
        
        # New Deal
        draw_c(format_price(item['deal_amount']), cols[2][0], y - 20, font_row, (255, 215, 0))
        draw_c(item['new_date'], cols[2][0], y + 25, font_date, (150, 150, 150))
        
        # Old Deal
        draw_c(format_price(item['old_low']), cols[3][0], y - 20, font_row, (200, 200, 200))
        draw_c(item['old_date'], cols[3][0], y + 25, font_date, (120, 120, 120))
        
        # Rate
        draw_c(f"+{item['rate']:.1f}%", cols[4][0], y, font_row, (100, 255, 100))
        draw.line([(40, y + 65), (w-40, y + 65)], fill=(50, 50, 70), width=1)
        y += row_h

    img.save(out_filename)
    print(f"Image saved to {out_filename}")

# Ranking 1: 하락률 기준 (Rate - Descending)
ath_list_sorted_rate = sorted(ath_list, key=lambda x: x['rate'], reverse=False)
generate_ranking_image(ath_list_sorted_rate[:10], "오늘의 신저가 하락률 TOP10", "C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_rate_low.png")

# Ranking 2: 거래 금액 기준 (Amount - Descending)
ath_list_sorted_highest = sorted(ath_list, key=lambda x: x['deal_amount'], reverse=True)
generate_ranking_image(ath_list_sorted_highest[:10], "오늘의 신저가 거래금 상위 TOP10", "C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_amount_low.png")

# Ranking 3: 거래 금액 작은 순 기준 (Amount - Ascending)
ath_list_sorted_lowest = sorted(ath_list, key=lambda x: x['deal_amount'], reverse=False)
generate_ranking_image(ath_list_sorted_lowest[:10], "오늘의 신저가 거래금 하위 10", "C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_lowest_low.png")


# 7. Generate Final Video
def generate_general_ranking_image(top_data, title, out_filename):
    w, h = 1080, 1920
    img = Image.new('RGB', (w, h), color=(20, 20, 28))
    draw = ImageDraw.Draw(img)

    font_title = get_font(65)
    font_sub = get_font(40)
    font_col = get_font(30)
    font_rank = get_font(45)
    font_row = get_font(35)
    font_date = get_font(26)

    def draw_c(text, x, y, font, color):
        bbox = draw.textbbox((0, 0), str(text), font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((x - tw/2, y - th/2), str(text), font=font, fill=color)

    # Header
    draw_c(title, w/2, 170, font_title, (255, 215, 0))
    draw_c(f"({today.strftime('%Y년 %m월 %d일')} 업데이트, 전용 면적)", w/2, 270, font_sub, (200, 200, 200))

    # Table Headers
    cols = [(60, "순위"), (300, "아파트 (지역)"), (580, "층수 (면적)"), (780, "거래금액"), (980, "거래일자")]
    y_start = 380
    draw.line([(40, y_start-30), (w-40, y_start-30)], fill=(100, 100, 150), width=3)
    for cx, cname in cols:
        draw_c(cname, cx, y_start, font_col, (150, 180, 255))
    draw.line([(40, y_start+30), (w-40, y_start+30)], fill=(100, 100, 150), width=3)

    # Rows
    y = y_start + 85
    row_h = 135
    if not top_data:
        draw_c("거래 내역 없음", w/2, y + 200, font_title, (180, 180, 180))
    for i, item in enumerate(top_data, 1):
        color = (255, 100, 100) if i <= 3 else (255, 255, 255)
        
        # Rank
        draw_c(f"{i}", cols[0][0], y, font_rank, color)
        
        # Apt & Region
        apt_str = f"{item['apt_name']}"
        reg_str = f"{item['region_name']} {item['umd_nm']}"
        apt_lines = wrap_text_by_char(draw, apt_str, font_row, 340, 2)
        
        if len(apt_lines) == 1:
            draw_c(apt_lines[0], cols[1][0], y - 20, font_row, (255, 255, 255))
            draw_c(reg_str, cols[1][0], y + 25, font_date, (180, 180, 180))
        else:
            draw_c(apt_lines[0], cols[1][0], y - 35, font_row, (255, 255, 255))
            draw_c(apt_lines[1], cols[1][0], y + 5, font_row, (255, 255, 255))
            draw_c(reg_str, cols[1][0], y + 45, font_date, (180, 180, 180))
        
        # Floor & Area
        draw_c(f"{item['floor']}층", cols[2][0], y - 20, font_row, (255, 255, 255))
        draw_c(f"{int(item['exclu_use_ar']/3.3)}평", cols[2][0], y + 25, font_date, (180, 180, 180))
        
        # New Deal
        draw_c(format_price(item['deal_amount']), cols[3][0], y, font_row, (255, 215, 0))
        
        # Date
        draw_c(f"{item['deal_ymd'][:4]}.{item['deal_ymd'][4:6]}.{item['deal_day']:02d}", cols[4][0], y, font_row, (200, 200, 200))
        
        draw.line([(40, y + 65), (w-40, y + 65)], fill=(50, 50, 70), width=1)
        y += row_h

    img.save(out_filename)
    print(f"Image saved to {out_filename}")



# Determine BGM based on the day of the week
weekday = datetime.date.today().weekday()
bgm_map = {
    0: "TechLive.mp3",
    1: "Tuesday.mp3",
    2: "Wednesday.mp3",
    3: "Thursday.mp3",
    4: "Friday.mp3",
    5: "Saturday.mp3",
    6: "Sunday.mp3"
}
bgm_filename = bgm_map.get(weekday, "TechLive.mp3")
bgm_path = f"C:/Users/kwonm/workspace/RealestateRanking/data/{bgm_filename}"
print(f"Today is {datetime.date.today().strftime('%A')}, using BGM: {bgm_filename}")


# 항상 오늘 전체 실거래 bottom10 추가
new_trades_sorted = sorted(new_trades, key=lambda x: x['deal_amount'], reverse=False)
generate_general_ranking_image(new_trades_sorted[:10], "오늘의 실거래 저가 순위 10", "C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_bottom10.png")

print("Generating 16-second Shorts video (including Bottom 10)...")
ffmpeg_cmd = [
    get_ffmpeg_path(), "-y",
    "-loop", "1", "-t", "4", "-i", "C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_bottom10.png",
    "-loop", "1", "-t", "4", "-i", "C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_amount_low.png",
    "-loop", "1", "-t", "4", "-i", "C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_rate_low.png",
    "-loop", "1", "-t", "4", "-i", "C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_lowest_low.png",
    "-i", bgm_path,
    "-filter_complex", "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[v];[4:a]afade=t=out:st=14:d=2[a]",
    "-map", "[v]", "-map", "[a]",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
    "-c:a", "aac", "-b:a", "192k", "-shortest",
    "C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_final_low.mp4"
]

subprocess.run(ffmpeg_cmd, capture_output=True)
print("Video generation complete: daily_shorts_final_low.mp4")
