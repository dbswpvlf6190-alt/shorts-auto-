import argparse
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instagram_upload  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# media_host는 git 저장소라 OneDrive 동기화와 상극(.git 내부 파일이 손상될 수 있음, 2026-08-22에 실제로 손상됨) — 로컬 전용 폴더 사용.
RENDER_ROOT = os.environ.get("SHORTS_RENDER_DIR", os.path.join(os.path.expanduser("~"), "ShortsAutoRender"))
MEDIA_HOST_DIR = os.path.join(RENDER_ROOT, "media_host")
GITHUB_TOKEN_PATH = os.path.join(BASE_DIR, "credentials", "github_token.txt")
GITHUB_REPO = "dbswpvlf6190-alt/shorts-media-host"


def run(cmd, cwd):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"git 명령 실패: {' '.join(cmd)}\n{result.stdout}\n{result.stderr}")
    return result.stdout


def push_video(video_path, remote_name):
    dest = os.path.join(MEDIA_HOST_DIR, remote_name)
    shutil.copy2(video_path, dest)

    with open(GITHUB_TOKEN_PATH, "r", encoding="utf-8") as f:
        token = f.read().strip()
    remote_url = f"https://{token}@github.com/{GITHUB_REPO}.git"
    run(["git", "remote", "set-url", "origin", remote_url], MEDIA_HOST_DIR)
    run(["git", "add", remote_name], MEDIA_HOST_DIR)
    run(["git", "commit", "-m", f"add {remote_name}"], MEDIA_HOST_DIR)
    run(["git", "push"], MEDIA_HOST_DIR)

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
