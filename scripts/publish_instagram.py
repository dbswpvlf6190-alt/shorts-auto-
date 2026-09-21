import argparse
import os
import shutil
import subprocess
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_upload  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# media_host는 git 저장소라 OneDrive 동기화와 상극(.git 내부 파일이 손상될 수 있음, 2026-08-22에 실제로 손상됨) — 로컬 전용 폴더 사용.
RENDER_ROOT = os.environ.get("SHORTS_RENDER_DIR", os.path.join(os.path.expanduser("~"), "ShortsAutoRender"))
MEDIA_HOST_DIR = os.path.join(RENDER_ROOT, "media_host")
GITHUB_TOKEN_PATH = os.path.join(BASE_DIR, "credentials", "github_token.txt")
GITHUB_REPO = "dbswpvlf6190-alt/shorts-media-host"


def run(cmd, cwd):
    # GCM(Git Credential Manager)이 데스크톱 세션 없는 Task Scheduler 환경에서
    # 응답 없는 인증창을 띄우려다 몇 시간씩 멈추는 문제가 실제로 발생함(2026-09-16/17,
    # 34/35번 인스타 게시 각각 3~4시간, 2시간 무응답 후 조용히 실패). URL에 토큰이
    # 이미 포함돼 있어 credential helper가 끼어들 필요가 없으므로 프롬프트 자체를
    # 차단하고, 그래도 멈추면 짧은 timeout으로 빨리 실패하게 함.
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"}
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git 명령 실패: {' '.join(cmd)}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def commit_and_push(add_paths, message):
    """같은 media_host를 노트북·데스크톱이 번갈아 쓰므로 push 전에 항상 최신을 받아 합친다
    (안 그러면 다른 컴퓨터가 먼저 올린 날 push가 fetch first로 거부돼 인스타 게시가 실패함,
    2026-09-21 노트북 38/39번 실제로 겪음). 이미 커밋된 같은 파일의 재시도는 커밋을 건너뛴다."""
    run(["git", "pull", "--no-rebase", "--no-edit", "origin", "main"], MEDIA_HOST_DIR)
    run(["git", "add", *add_paths], MEDIA_HOST_DIR)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=MEDIA_HOST_DIR).returncode != 0
    if staged:
        run(["git", "commit", "-m", message], MEDIA_HOST_DIR)
    try:
        run(["git", "push"], MEDIA_HOST_DIR)
    except RuntimeError:
        run(["git", "pull", "--no-rebase", "--no-edit", "origin", "main"], MEDIA_HOST_DIR)
        run(["git", "push"], MEDIA_HOST_DIR)


def push_video(video_path, remote_name):
    dest = os.path.join(MEDIA_HOST_DIR, remote_name)
    shutil.copy2(video_path, dest)

    with open(GITHUB_TOKEN_PATH, "r", encoding="utf-8") as f:
        token = f.read().strip()
    remote_url = f"https://{token}@github.com/{GITHUB_REPO}.git"
    run(["git", "remote", "set-url", "origin", remote_url], MEDIA_HOST_DIR)
    commit_and_push([remote_name], f"add {remote_name}")

    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{remote_name}"


def publish(video_path, caption, remote_name):
    print(f"1/2 깃허브에 영상 업로드 중... ({remote_name})")
    url = push_video(video_path, remote_name)
    print(f"   URL: {url}")
    time.sleep(8)
    print("2/2 인스타그램에 게시 중...")
    return instagram_upload.upload_reel(url, caption)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--caption", required=True)
    ap.add_argument("--name", required=True, help="깃허브에 올릴 파일명 (예: 20260816_dsr.mp4)")
    args = ap.parse_args()
    publish(args.video, args.caption, args.name)


if __name__ == "__main__":
    main()
