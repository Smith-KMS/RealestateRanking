import requests
import xml.etree.ElementTree as ET
import urllib3
import sqlite3
import time
import os
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

api_key = "095266ca1cc9b437a6d4fab0f424668948b76a8a7981b5260d6e6ffaf48886d3"
url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

# 서울 전체(25개구) + 성남시 분당구(판교 포함)
regions = {
    "종로구": "11110", "중구": "11140", "용산구": "11170", "성동구": "11200",
    "광진구": "11215", "동대문구": "11230", "중랑구": "11260", "성북구": "11290",
    "강북구": "11305", "도봉구": "11320", "노원구": "11350", "은평구": "11380",
    "서대문구": "11410", "마포구": "11440", "양천구": "11470", "강서구": "11500",
    "구로구": "11530", "금천구": "11545", "영등포구": "11560", "동작구": "11590",
    "관악구": "11620", "서초구": "11650", "강남구": "11680", "송파구": "11710",
    "강동구": "11740", "분당구": "41135"
}

db_path = "/Users/smithkwon/.openclaw/workspace/dailypriceup/data/apt_trades.db"

def init_db():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            region_name TEXT,
            lawd_cd TEXT,
            deal_ymd TEXT,
            apt_name TEXT,
            jibun TEXT,
            exclu_use_ar REAL,
            deal_amount INTEGER,
            deal_year INTEGER,
            deal_month INTEGER,
            deal_day INTEGER,
            floor INTEGER,
            build_year INTEGER,
            umd_nm TEXT
        )
    ''')
    
    # 신고가 검색을 빠르게 하기 위한 인덱스 생성
    cur.execute('CREATE INDEX IF NOT EXISTS idx_apt_ar ON trades (lawd_cd, apt_name, exclu_use_ar);')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_deal_amount ON trades (deal_amount);')
    conn.commit()
    return conn

def fetch_data(conn, start_year, end_year, start_month=1):
    cur = conn.cursor()
    
    for year in range(start_year, end_year + 1):
        s_month = start_month if year == start_year else 1
        for month in range(s_month, 13):
            deal_ymd = f"{year}{month:02d}"
            
            # 현재 2026년 6월 이후는 스킵 (미래 데이터)
            if year == 2026 and month > 6:
                continue
                
            print(f"--- {deal_ymd} 데이터 수집 시작 ---")
            
            for region_name, lawd_cd in regions.items():
                params = {
                    'serviceKey': api_key,
                    'LAWD_CD': lawd_cd,
                    'DEAL_YMD': deal_ymd,
                    'numOfRows': '2000',
                    'pageNo': '1'
                }
                
                try:
                    res = requests.get(url, params=params, headers=headers, timeout=15, verify=False)
                    if res.status_code == 200:
                        root = ET.fromstring(res.content)
                        items = root.findall('.//item')
                        
                        count = 0
                        for item in items:
                            try:
                                apt_nm = item.findtext('aptNm', '').strip()
                                jibun = item.findtext('jibun', '').strip()
                                umd_nm = item.findtext('umdNm', '').strip()
                                deal_amount_str = item.findtext('dealAmount', '0').replace(',', '').strip()
                                deal_amount = int(deal_amount_str)
                                exclu_use_ar = float(item.findtext('excluUseAr', '0'))
                                floor = int(item.findtext('floor', '0'))
                                build_year = int(item.findtext('buildYear', '0') or '0')
                                deal_day = int(item.findtext('dealDay', '0'))
                                
                                # 고유 ID 생성 (지역코드_연월_일_아파트명_전용면적_층)
                                unique_id = f"{lawd_cd}_{deal_ymd}_{deal_day}_{apt_nm}_{exclu_use_ar}_{floor}_{deal_amount}"
                                
                                cur.execute('''
                                    INSERT OR IGNORE INTO trades 
                                    (id, region_name, lawd_cd, deal_ymd, apt_name, jibun, exclu_use_ar, 
                                     deal_amount, deal_year, deal_month, deal_day, floor, build_year, umd_nm)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (unique_id, region_name, lawd_cd, deal_ymd, apt_nm, jibun, exclu_use_ar, 
                                      deal_amount, year, month, deal_day, floor, build_year, umd_nm))
                                count += 1
                            except Exception as e:
                                pass
                        
                        conn.commit()
                        print(f"[{region_name}] {count}건 저장 완료")
                    else:
                        print(f"[{region_name}] API 응답 에러: {res.status_code}")
                except Exception as e:
                    print(f"[{region_name}] 요청 실패: {e}")
                
                # API 호출 간 약간의 딜레이 (서버 차단 방지)
                time.sleep(0.3)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 fetch_history.py <start_year> <end_year>")
        sys.exit(1)
        
    start_year = int(sys.argv[1])
    end_year = int(sys.argv[2])
    
    conn = init_db()
    start_month = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    fetch_data(conn, start_year, end_year, start_month)
    conn.close()
    print("데이터 수집 완료!")
