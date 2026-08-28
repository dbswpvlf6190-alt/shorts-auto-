import argparse
import json
import os
import sys
import time
import urllib.parse

import requests

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_PATH = os.path.join(BASE_DIR, "credentials", "instagram_secret.json")
TOKEN_PATH = os.path.join(BASE_DIR, "credentials", "instagram_token.json")

SCOPES = (
    "instagram_business_basic,"
    "instagram_business_manage_messages,"
    "instagram_business_manage_comments,"
    "instagram_business_content_publish,"
    "instagram_business_manage_insights"
)


def _load_secret():
    with open(SECRET_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def get_auth_url():
    secret = _load_secret()
    params = {
        "client_id": secret["app_id"],
        "redirect_uri": secret["redirect_uri"],
        "response_type": "code",
        "scope": SCOPES,
    }
    return "https://www.instagram.com/oauth/authorize?" + urllib.parse.urlencode(params)


def exchange_code(code):
    secret = _load_secret()
    fields = {
        "client_id": secret["app_id"],
        "client_secret": secret["app_secret"],
        "grant_type": "authorization_code",
        "redirect_uri": secret["redirect_uri"],
        "code": code,
    }
    resp = requests.post(
        "https://api.instagram.com/oauth/access_token",
        files={k: (None, v) for k, v in fields.items()},
    )
    if resp.status_code != 200:
        print(f"exchange failed: {resp.status_code} {resp.text}")
    resp.raise_for_status()
    short_token = resp.json()["access_token"]
    user_id = resp.json().get("user_id")

    long_resp = requests.get(
        "https://graph.instagram.com/access_token",
        params={
            "grant_type": "ig_exchange_token",
            "client_secret": secret["app_secret"],
            "access_token": short_token,
        },
    )
    long_resp.raise_for_status()
    long_data = long_resp.json()

    token_data = {
        "access_token": long_data["access_token"],
        "user_id": user_id,
        "obtained_at": time.time(),
        "expires_in": long_data.get("expires_in", 5184000),
    }
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token_data, f)
    return token_data


def _refresh_token(token_data):
    secret = _load_secret()
    resp = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={
            "grant_type": "ig_refresh_token",
            "access_token": token_data["access_token"],
        },
    )
    resp.raise_for_status()
    data = resp.json()
    token_data["access_token"] = data["access_token"]
    token_data["obtained_at"] = time.time()
    token_data["expires_in"] = data.get("expires_in", 5184000)
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token_data, f)
    return token_data


def get_token():
    if not os.path.exists(TOKEN_PATH):
        raise SystemExit(
            "저장된 토큰이 없습니다. 먼저 --get-auth-url로 인증 URL을 받고, "
            "--exchange-code CODE 로 최초 인증을 완료해주세요."
        )
    with open(TOKEN_PATH, "r", encoding="utf-8-sig") as f:
        token_data = json.load(f)
    age_days = (time.time() - token_data["obtained_at"]) / 86400
    if age_days > 50:
        print("토큰 만료 임박, 갱신 중...")
        token_data = _refresh_token(token_data)
    return token_data


def upload_reel(video_url, caption):
    token_data = get_token()
    access_token = token_data["access_token"]
    user_id = token_data["user_id"]

    create_resp = requests.post(
        f"https://graph.instagram.com/v21.0/{user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "access_token": access_token,
        },
    )
    if create_resp.status_code != 200:
        print(f"미디어 생성 실패 응답: {create_resp.status_code} {create_resp.text}")
    create_resp.raise_for_status()
    container_id = create_resp.json()["id"]
    print(f"컨테이너 생성됨: {container_id}, 처리 대기 중...")

    for _ in range(60):
        status_resp = requests.get(
            f"https://graph.instagram.com/v21.0/{container_id}",
            params={"fields": "status_code", "access_token": access_token},
        )
        status_resp.raise_for_status()
        status = status_resp.json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError("인스타그램 영상 처리 실패")
        time.sleep(5)
    else:
        raise RuntimeError("영상 처리 시간 초과")

    publish_resp = requests.post(
        f"https://graph.instagram.com/v21.0/{user_id}/media_publish",
        data={"creation_id": container_id, "access_token": access_token},
    )
    publish_resp.raise_for_status()
    media_id = publish_resp.json()["id"]
    print(f"완료: media_id={media_id}")
    return media_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video-url", help="공개적으로 접근 가능한 영상 URL")
    ap.add_argument("--caption", help="게시글 캡션")
    ap.add_argument("--get-auth-url", action="store_true", help="최초 인증용 URL 출력")
    ap.add_argument("--exchange-code", help="인증 후 받은 code 값으로 토큰 발급")
    args = ap.parse_args()

    if args.get_auth_url:
        print(get_auth_url())
        return
    if args.exchange_code:
        exchange_code(args.exchange_code)
        print("토큰 저장 완료")
        return
    if not args.video_url or not args.caption:
        raise SystemExit("--video-url 와 --caption 이 필요합니다")
    upload_reel(args.video_url, args.caption)


if __name__ == "__main__":
    main()
