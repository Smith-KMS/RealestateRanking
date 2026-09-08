import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
secret = 'C:/Users/kwonm/workspace/RealestateRanking/scripts/client_secret.json'
token = 'C:/Users/kwonm/workspace/RealestateRanking/scripts/token.json'

# open_browser=False로 설정하여 URL만 출력하고 대기
flow = InstalledAppFlow.from_client_secrets_file(secret, SCOPES)
creds = flow.run_local_server(port=8080, open_browser=False)

with open(token, 'w') as f:
    f.write(creds.to_json())

print("SUCCESS: Token saved!")
