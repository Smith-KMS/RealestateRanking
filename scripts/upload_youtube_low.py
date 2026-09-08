import os
import sys
import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# 1. 스코프 및 인증 관련 경로 설정
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
client_secret_file = 'C:/Users/kwonm/workspace/RealestateRanking/scripts/client_secret.json'
token_file = 'C:/Users/kwonm/workspace/RealestateRanking/scripts/token.json'
video_file = 'C:/Users/kwonm/workspace/RealestateRanking/data/daily_shorts_final_low.mp4'

def authenticate():
    creds = None
    # 이전에 저장된 토큰이 있으면 불러오기
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
    # 유효한 크리덴셜이 없거나 만료되었을 경우 새로 발급
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(client_secret_file):
                print(f"Error: {client_secret_file} 파일이 없습니다.")
                print("Google Cloud Console에서 YouTube Data API v3 데스크톱 앱용 OAuth 2.0 클라이언트 ID를 생성하고 다운로드하여 저장해 주세요.")
                sys.exit(1)
            # Mac에서 직접 브라우저를 띄워 사용자 인증 진행
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # 다음 실행을 위해 토큰 저장
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
            
    return creds

def upload_video():
    creds = authenticate()
    youtube = build('youtube', 'v3', credentials=creds)

    today_str = datetime.date.today().strftime("%Y년 %m월 %d일")
    title = f"({today_str}) 서울/경기 아파트 신저가 랭킹 TOP10 #Shorts"
    
    # 영상 설명 (배경음악 저작권 표기 포함)
    description = f"""오늘의 서울/경기 아파트 실거래가 랭킹입니다!
- 최저가 거래 아파트 TOP 10
- 신저가 하락률 TOP 10
- 신저가 최저가 거래 TOP 10

#부동산 #아파트실거래가 #신저가 #강남아파트 #Shorts #부동산전망

🎵 Music
Music: Tech Live by Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0 License
http://creativecommons.org/licenses/by/4.0/"""

    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': ['부동산', '아파트', '실거래가', '강남', '서초', '송파', '신저가', 'shorts'],
            'categoryId': '22'  # 22 = People & Blogs
        },
        'status': {
            # 우선은 비공개(private)로 업로드 테스트. 이상 없으면 'public'으로 변경 가능.
            'privacyStatus': 'public', 
            'selfDeclaredMadeForKids': False
        }
    }

    print("Uploading video to YouTube...")
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype='video/mp4')
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%")

    print("=== Upload Complete! ===")
    print(f"Video ID: {response['id']}")
    print(f"URL: https://youtu.be/{response['id']}")

if __name__ == '__main__':
    upload_video()
