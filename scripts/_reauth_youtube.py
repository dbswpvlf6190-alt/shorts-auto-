import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from google_auth_oauthlib.flow import InstalledAppFlow

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRET_PATH = os.path.join(BASE_DIR, "credentials", "client_secret.json")
TOKEN_PATH = os.path.join(BASE_DIR, "credentials", "token.json")

# 기존 토큰(youtube.upload + youtube.readonly)엔 videos().update() 권한이 없어서
# 비공개→공개 전환을 프로그램으로 못 했음(2026-09-10). 전체 관리 스코프를 추가해 재인증.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube",
]

if not os.path.exists(CLIENT_SECRET_PATH):
    raise SystemExit(f"client_secret.json이 없습니다: {CLIENT_SECRET_PATH}")

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
creds = flow.run_local_server(port=0)
with open(TOKEN_PATH, "w", encoding="utf-8") as f:
    f.write(creds.to_json())
print("재인증 완료 — token.json이 넓은 스코프로 갱신됨")
