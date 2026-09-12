import argparse
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    # videos().update()(공개상태 전환 등)에 필요 — 2026-09-10 재인증으로 추가.
    "https://www.googleapis.com/auth/youtube",
]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRET_PATH = os.path.join(BASE_DIR, "credentials", "client_secret.json")
TOKEN_PATH = os.path.join(BASE_DIR, "credentials", "token.json")


def get_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_PATH):
                raise SystemExit(
                    f"client_secret.json이 없습니다: {CLIENT_SECRET_PATH}\n"
                    "Google Cloud Console에서 다운로드한 OAuth 클라이언트 JSON을 이 경로에 저장하세요."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return creds


def upload(video_path, title, description, privacy="private", made_for_kids=False, tags=None, thumbnail=None):
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  업로드 중... {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"완료: https://youtube.com/shorts/{video_id}")

    # 썸네일을 안 정해주면 유튜브가 영상 중간 아무 프레임(대개 자막 문장이 중간에 끊긴 broll
    # 카드)을 자동으로 골라서 썸네일이 이상하게 나옴(2026-09-12 사용자 피드백으로 발견) —
    # 오프닝 훅 프레임(가장 임팩트 있는 첫 문구 카드)을 명시적으로 지정.
    if thumbnail and os.path.exists(thumbnail):
        try:
            youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail)).execute()
            print(f"  썸네일 설정 완료: {thumbnail}")
        except Exception as e:
            print(f"  썸네일 설정 실패(건너뜀): {e}")

    return video_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    ap.add_argument("--tags", default="")
    ap.add_argument("--thumbnail", default=None)
    args = ap.parse_args()

    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    upload(args.video, args.title, args.description, args.privacy, tags=tags, thumbnail=args.thumbnail)


if __name__ == "__main__":
    main()
