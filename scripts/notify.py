"""ntfy 푸시 알림 — 사용자가 폰(ntfy 앱)으로 업로드/게시 결과를 받게 한다.
설정: credentials/ntfy.json {"topic": "...", "server": "https://ntfy.sh"} (git 제외, 컴퓨터마다 같은 파일 필요).
파일이 없거나 네트워크가 안 되면 조용히 False를 반환할 뿐, 절대 파이프라인을 멈추거나 예외를 던지지 않는다.
테스트: python scripts/notify.py --test"""
import json
import os
import sys
import urllib.request

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "credentials", "ntfy.json")


def notify(title, message, priority=3, tags=None, click=None):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        body = {"topic": cfg["topic"], "title": title, "message": message, "priority": priority, "tags": tags or []}
        if click:
            body["click"] = click
        req = urllib.request.Request(
            cfg.get("server", "https://ntfy.sh"),
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        urllib.request.urlopen(req, timeout=8).read()
        return True
    except Exception:
        return False


# 실패 메시지에서 흔한 원인을 한글 한 줄로 요약(못 알아보면 원문 끝부분만).
_REASONS = [
    (("fetch first", "non-fast-forward"), "미디어 저장소가 최신이 아니라 push 거부됨"),
    (("Could not resolve host", "Failed to establish", "Max retries exceeded", "getaddrinfo"), "인터넷 연결 안 됨"),
    (("timed out", "TimeoutExpired", "120초"), "시간 초과(인증 대기 등)"),
    (("RefreshError", "invalid_grant"), "유튜브 토큰 만료(재인증 필요)"),
    (("quotaExceeded", "quota"), "API 일일 한도 초과"),
    (("OAuthException", "access token", "Invalid OAuth"), "인스타 토큰 문제"),
    (("403", "Permission", "denied"), "권한 거부(토큰 확인)"),
    (("401", "Authentication"), "인증 실패(토큰 만료?)"),
    (("moov atom", "Invalid data found"), "영상 파일 손상"),
    (("No such file", "FileNotFoundError"), "파일을 찾을 수 없음"),
]


def summarize_error(text):
    t = str(text or "")
    for keys, reason in _REASONS:
        if any(k in t for k in keys):
            return f"사유: {reason}"
    tail = " ".join(t.split())[-100:]
    return f"사유: {tail}" if tail else "사유: 알 수 없음(로그 확인)"


if __name__ == "__main__":
    if "--test" in sys.argv:
        ok = notify("✅ 알림 테스트", "이 메시지가 폰에 보이면 업로드 보고 설정이 끝난 거예요.", tags=["white_check_mark"])
        print("전송 성공" if ok else "전송 실패(설정 파일/네트워크 확인)")
