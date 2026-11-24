"""틱톡 '임시 저장함(받은 편지함)'으로 영상 보내기 — Content Posting API의 Upload(inbox) 방식 (2026-11-24 추가).

영상은 공개되지 않고 사용자 틱톡 앱에 알림으로 도착한다. 사용자가 알림을 눌러 '게시'만 하면 끝.
(바로 공개(Direct Post)는 틱톡 심사(audit) 통과 전엔 '나만 보기'로만 올라가서 안 씀.)

설정 파일 (git 밖, OneDrive에 둬서 노트북·데스크톱이 같은 토큰을 씀 — 리프레시 토큰은 쓸 때마다
새로 바뀌고 옛것은 죽기 때문에 컴퓨터마다 따로 두면 한쪽이 반드시 깨진다. 두 대가 동시에 켜지지 않는 운영이라 안전):
  %OneDrive%\\shorts_auto_secrets\\tiktok_app.json   {"client_key": "...", "client_secret": "..."}  ← 사용자가 직접 입력
  %OneDrive%\\shorts_auto_secrets\\tiktok_token.json ← auth 명령이 만들고 upload가 갱신

명령:
  python scripts/tiktok_upload.py auth                 # 처음 한 번(그리고 180일마다): 브라우저로 로그인·허용
  python scripts/tiktok_upload.py upload --video X.mp4 # 임시 저장함으로 보내기
  python scripts/tiktok_upload.py status               # 토큰 상태 확인

종료 코드: 0 성공 / 2 설정·토큰 없음(아직 연결 안 함) / 1 그 밖의 실패.
"""
import argparse
import http.server
import json
import os
import secrets
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

SECRETS_DIR = os.environ.get(
    "SHORTS_SECRETS_DIR",
    os.path.join(os.environ.get("OneDrive", os.path.expanduser("~")), "shorts_auto_secrets"),
)
APP_PATH = os.path.join(SECRETS_DIR, "tiktok_app.json")
TOKEN_PATH = os.path.join(SECRETS_DIR, "tiktok_token.json")

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
SCOPE = "user.info.basic,video.upload"
# 틱톡은 https 주소만 콜백으로 받는다 → GitHub Pages의 정적 페이지가 받은 code를 이 컴퓨터(127.0.0.1)로 넘겨준다.
REDIRECT_URI = "https://dbswpvlf6190-alt.github.io/shorts-auto-/tiktok/callback/"
LOCAL_PORT = 8765

MB = 1024 * 1024


class NotConnected(Exception):
    """앱 키나 토큰이 아직 없음 — 파이프라인은 조용히 건너뛰면 된다."""


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_token(tok):
    os.makedirs(SECRETS_DIR, exist_ok=True)
    now = int(time.time())
    data = {
        "access_token": tok["access_token"],
        "refresh_token": tok["refresh_token"],
        "open_id": tok.get("open_id", ""),
        "scope": tok.get("scope", ""),
        "access_expires_at": now + int(tok.get("expires_in", 0)) - 120,
        "refresh_expires_at": now + int(tok.get("refresh_expires_in", 0)),
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    tmp = TOKEN_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, TOKEN_PATH)
    return data


def _app():
    if not os.path.exists(APP_PATH):
        raise NotConnected(f"앱 키 파일 없음: {APP_PATH}")
    app = _load(APP_PATH)
    if not app.get("client_key") or not app.get("client_secret"):
        raise NotConnected(f"앱 키 파일에 client_key/client_secret가 비어 있음: {APP_PATH}")
    return app


def _post_form(url, fields):
    req = urllib.request.Request(
        url, data=urllib.parse.urlencode(fields).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Cache-Control": "no-cache"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode() or "{}")
    if "access_token" not in body:
        raise RuntimeError(f"토큰 요청 실패: {body.get('error')} {body.get('error_description', '')}".strip())
    return body


def _post_json(url, token, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode() or "{}")
    err = body.get("error", {})
    if err.get("code") not in (None, "ok"):
        raise RuntimeError(f"틱톡 API 오류 {err.get('code')}: {err.get('message', '')}")
    return body.get("data", {})


def access_token():
    """유효한 access token을 돌려준다(2시간짜리라 필요하면 refresh 토큰으로 새로 받음)."""
    app = _app()
    if not os.path.exists(TOKEN_PATH):
        raise NotConnected("틱톡 연결 전 — `python scripts/tiktok_upload.py auth` 를 먼저 실행")
    tok = _load(TOKEN_PATH)
    now = time.time()
    if tok.get("access_expires_at", 0) > now:
        return tok["access_token"]
    if tok.get("refresh_expires_at", 0) <= now:
        raise NotConnected("틱톡 연결이 만료됨(180일) — `python scripts/tiktok_upload.py auth` 다시 실행")
    new = _post_form(TOKEN_URL, {
        "client_key": app["client_key"], "client_secret": app["client_secret"],
        "grant_type": "refresh_token", "refresh_token": tok["refresh_token"],
    })
    return _save_token(new)["access_token"]


def days_left():
    try:
        return int((_load(TOKEN_PATH)["refresh_expires_at"] - time.time()) // 86400)
    except Exception:
        return None


def upload(video):
    """영상을 임시 저장함으로 보내고 publish_id를 돌려준다."""
    token = access_token()
    size = os.path.getsize(video)
    # 규칙: 5MB 미만은 통째로, 64MB 이하는 한 조각, 그보다 크면 10MB씩(마지막 조각이 나머지를 다 가짐).
    if size <= 64 * MB:
        chunk, count = size, 1
    else:
        chunk = 10 * MB
        count = size // chunk
    data = _post_json(INIT_URL, token, {"source_info": {
        "source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk, "total_chunk_count": count,
    }})
    publish_id, upload_url = data["publish_id"], data["upload_url"]
    with open(video, "rb") as f:
        for i in range(count):
            start = i * chunk
            end = size - 1 if i == count - 1 else start + chunk - 1
            f.seek(start)
            part = f.read(end - start + 1)
            for attempt in range(3):
                req = urllib.request.Request(upload_url, data=part, method="PUT", headers={
                    "Content-Type": "video/mp4", "Content-Length": str(len(part)),
                    "Content-Range": f"bytes {start}-{end}/{size}",
                })
                try:
                    with urllib.request.urlopen(req, timeout=300) as r:
                        code = r.status
                    break
                except urllib.error.HTTPError as e:
                    if e.code >= 500 and attempt < 2:
                        time.sleep(5)
                        continue
                    raise RuntimeError(f"틱톡 영상 전송 실패 (조각 {i + 1}/{count}, HTTP {e.code}): {e.read()[:200]!r}")
            if code not in (200, 201, 206):
                raise RuntimeError(f"틱톡 영상 전송 응답 이상 (조각 {i + 1}/{count}, HTTP {code})")
    return publish_id


def wait_inbox(publish_id, timeout=240):
    """처리가 끝나 앱 알림이 갔는지(SEND_TO_USER_INBOX) 확인. 시간 안에 못 보면 마지막 상태를 돌려준다."""
    token = access_token()
    status = "UNKNOWN"
    end = time.time() + timeout
    while time.time() < end:
        data = _post_json(STATUS_URL, token, {"publish_id": publish_id})
        status = data.get("status", "UNKNOWN")
        if status in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"):
            return status
        if status == "FAILED":
            raise RuntimeError(f"틱톡 처리 실패: {data.get('fail_reason', '')}")
        time.sleep(10)
    return status


def auth():
    """브라우저로 틱톡 로그인·허용 → GitHub Pages 콜백 → 이 컴퓨터 127.0.0.1:8765 로 code 도착 → 토큰 저장."""
    app = _app()
    state = secrets.token_urlsafe(16)
    got = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            ok = "code" in got and got.get("state") == state
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "연결됐어요. 이 창은 닫아도 돼요." if ok else "연결에 실패했어요. 터미널 메시지를 확인해 주세요."
            self.wfile.write(f"<meta charset=utf-8><p style='font:20px sans-serif;padding:40px'>{msg}</p>".encode())

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", LOCAL_PORT), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()
    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_key": app["client_key"], "response_type": "code", "scope": SCOPE,
        "redirect_uri": REDIRECT_URI, "state": state,
    })
    print("브라우저에서 틱톡 로그인 → '허용'을 눌러 주세요. (안 열리면 아래 주소를 복사해 여세요)\n" + url)
    webbrowser.open(url)
    for _ in range(600):
        if got:
            break
        time.sleep(0.5)
    server.server_close()
    if not got:
        raise RuntimeError("5분 안에 응답이 없었어요. 다시 실행해 주세요.")
    if got.get("state") != state:
        raise RuntimeError("보안 확인값(state)이 달라요. 다시 실행해 주세요.")
    if "code" not in got:
        raise RuntimeError(f"허용이 안 됐어요: {got.get('error')} {got.get('error_description', '')}")
    tok = _post_form(TOKEN_URL, {
        "client_key": app["client_key"], "client_secret": app["client_secret"], "code": got["code"],
        "grant_type": "authorization_code", "redirect_uri": REDIRECT_URI,
    })
    data = _save_token(tok)
    print(f"✅ 틱톡 연결 완료. 권한: {data['scope']} · 다시 연결 필요까지 {days_left()}일")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    sub.add_parser("status")
    up = sub.add_parser("upload")
    up.add_argument("--video", required=True)
    args = ap.parse_args()
    try:
        if args.cmd == "auth":
            auth()
        elif args.cmd == "status":
            access_token()
            print(f"연결됨 · 다시 연결 필요까지 {days_left()}일")
        else:
            pid = upload(args.video)
            st = wait_inbox(pid)
            print(f"TIKTOK_OK publish_id={pid} status={st} days_left={days_left()}")
    except NotConnected as e:
        print(f"TIKTOK_NOT_CONNECTED {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
