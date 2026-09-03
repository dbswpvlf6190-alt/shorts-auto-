import json
import os
import re
import shutil
import socket
import subprocess
import sys
import winreg
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

LOCK_STALE_HOURS = 3  # 이 시간이 지난 락은 이전 실행이 비정상 종료된 것으로 보고 무시

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_DIR = os.path.join(BASE_DIR, "input", "queue")
LOG_PATH = os.path.join(BASE_DIR, "output", "queue_log.txt")

# 렌더링 결과물(영상)은 이 git 저장소 밖, 이 컴퓨터 로컬에만 저장한다(용량이 크고 자주 바뀌어 git에 안 맞음).
# OneDrive로 동기화하던 시절 용량 초과로 로컬 파일까지 지워진 사고가 있었음(2026-08-21~22) — 재발 방지 차원에서도 계속 분리 유지.
# 이 폴더는 컴퓨터마다 독립적이며 동기화되지 않는다.
RENDER_ROOT = os.environ.get("SHORTS_RENDER_DIR", os.path.join(os.path.expanduser("~"), "ShortsAutoRender"))
QUEUE_RENDER_DIR = os.path.join(RENDER_ROOT, "queue_render")
DELIVERY_DIR = os.path.join(RENDER_ROOT, "업로드영상")


def log(msg):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sanitize_filename(text, max_len=150):
    # 이모지(BMP 밖 문자)가 파일명에 남으면 콘솔/로그 인코딩(cp949)이 이걸 못 담아서
    # 프로그램이 죽는 사고가 있었음(2026-08-28, 바탕화면 복사가 조용히 실패했었음) — 아예 제거.
    text = "".join(ch for ch in text if ord(ch) <= 0xFFFF)
    text = re.sub(r'[\\/:*?"<>|]', '', text).strip()
    return text[:max_len].rstrip()


def get_desktop_path():
    """바탕화면 실제 경로를 레지스트리에서 읽음 — 컴퓨터마다 OneDrive로 리디렉션됐는지
    여부가 달라서(노트북은 리디렉션됨, 데스크톱은 아님) 고정 경로를 쓰면 안 됨."""
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
    )
    path, _ = winreg.QueryValueEx(key, "Desktop")
    return os.path.expandvars(path)


def get_tiktok_delivery_path():
    """틱톡 파일을 실제로 가져다 놓을 폴더. 사용자가 원래 몇 달째 수동으로 관리해오던
    정리 폴더(바탕화면\\05_영상_SNS\\틱톡 영상)가 있으면 그걸 그대로 쓰고(2026-09-03에
    바탕화면 루트에 떨어뜨려서 사용자가 못 찾은 사고 있었음 — 그 폴더엔 8/14 이후로
    새 파일이 하나도 안 들어가고 있었던 게 증거), 없으면(다른 컴퓨터 등) 바탕화면
    루트로 그냥 떨어뜨림."""
    desktop = get_desktop_path()
    organized = os.path.join(desktop, "05_영상_SNS", "틱톡 영상")
    if os.path.isdir(organized):
        return organized
    return desktop


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        log(f"  FAILED: {' '.join(cmd)}\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}")
        raise RuntimeError("step failed")
    return result.stdout


def git(args):
    return subprocess.run(["git"] + args, cwd=BASE_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")


def git_pull():
    result = git(["pull", "--rebase", "origin", "main"])
    if result.returncode != 0:
        log(f"  git pull 실패(무시하고 로컬 상태로 계속): {result.stderr[-500:]}")


def git_commit_push(paths, message):
    """지정한 경로만 커밋해서 push. 실패해도 예외를 던지지 않는다(네트워크 문제로 전체 실행이
    멈추면 안 되므로) — 대신 성공 여부를 반환해서 호출부가 판단하게 한다."""
    git(["add"] + paths)
    commit = git(["commit", "-m", message])
    if commit.returncode != 0:
        if "nothing to commit" in (commit.stdout + commit.stderr).lower():
            return True  # 변경사항 없음 -> 이미 최신 상태이므로 성공으로 취급
        return False
    push = git(["push", "origin", "main"])
    return push.returncode == 0


def try_acquire_lock(item_dir):
    """두 컴퓨터가 같은 git 저장소를 공유하다 보니 동시에 같은 항목을 처리할 위험이 있음
    (OneDrive 시절 2026-08-22에 실제로 겪음) — 처리 시작 전 락 파일을 커밋+push해서 남기고,
    push가 거부되면(다른 컴퓨터가 먼저 push함) 양보한다. git push의 원자성을 이용하는 것이라
    OneDrive의 "잠시 대기 후 재확인"보다 훨씬 확실하다."""
    lock_path = os.path.join(item_dir, "processing.lock")
    rel_lock_path = os.path.relpath(lock_path, BASE_DIR)
    me = f"{socket.gethostname()}|{os.getpid()}"

    if os.path.exists(lock_path):
        with open(lock_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        try:
            holder, ts = content.rsplit(" ", 1)
            age_hours = (datetime.now() - datetime.fromisoformat(ts)).total_seconds() / 3600
        except ValueError:
            holder, age_hours = content, 0
        if age_hours < LOCK_STALE_HOURS:
            return False, holder
        # 오래된 락은 이전 실행이 비정상 종료된 것으로 보고 무시하고 덮어씀

    with open(lock_path, "w", encoding="utf-8") as f:
        f.write(f"{me} {datetime.now().isoformat()}")

    if not git_commit_push([rel_lock_path], f"lock: {os.path.basename(item_dir)} by {me}"):
        # push 거부됨 -> 다른 컴퓨터가 먼저 뭔가를 올렸다는 뜻. 최신 상태를 받아와서 재확인.
        git_pull()
        if os.path.exists(lock_path):
            with open(lock_path, "r", encoding="utf-8") as f:
                current = f.read().strip()
            if not current.startswith(me):
                return False, current  # 다른 컴퓨터가 락을 선점함 -> 양보
        # 그 외의 이유로 push가 실패한 경우(네트워크 등)는 일단 로컬 락으로 진행하되 다음 push 때 재시도됨

    return True, me


def release_lock(item_dir):
    lock_path = os.path.join(item_dir, "processing.lock")
    rel_lock_path = os.path.relpath(lock_path, BASE_DIR)
    if os.path.exists(lock_path):
        os.remove(lock_path)
    git_commit_push([rel_lock_path], f"unlock: {os.path.basename(item_dir)}")


def process_item(item_dir):
    name = os.path.basename(item_dir)
    meta_path = os.path.join(item_dir, "meta.json")
    script_path = os.path.join(item_dir, "script.txt")
    images_dir = os.path.join(item_dir, "images")
    done_marker = os.path.join(item_dir, "done.txt")

    if os.path.exists(done_marker):
        return "done_already"
    if not (os.path.exists(meta_path) and os.path.exists(script_path) and os.path.isdir(images_dir)):
        log(f"skip {name}: meta.json/script.txt/images 중 누락됨")
        return "invalid"

    acquired, holder = try_acquire_lock(item_dir)
    if not acquired:
        log(f"skip {name}: 다른 컴퓨터({holder})가 이미 처리 중인 것으로 보임")
        return "locked"

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        log(f"processing {name}...")
        render_dir = os.path.join(QUEUE_RENDER_DIR, name)
        work_dir = os.path.join(render_dir, "_work")
        os.makedirs(work_dir, exist_ok=True)

        base_video = os.path.join(render_dir, "base.mp4")
        run([
            sys.executable, os.path.join(BASE_DIR, "scripts", "make_short.py"),
            "--script", script_path, "--images", images_dir,
            "--voice", meta.get("voice", "cloned"),
            "--out", base_video, "--work", work_dir,
            "--img-dur", str(meta.get("img_dur", 5)),
        ])

        platform_dir = os.path.join(render_dir, "platform")
        run([
            sys.executable, os.path.join(BASE_DIR, "scripts", "make_platform_variants.py"),
            "--base-video", base_video,
            "--yt-hook-lines", meta["yt_hook_lines"],
            "--tiktok-hook-text", meta["tiktok_hook_text"],
            "--out-dir", platform_dir,
            "--voice", meta.get("voice", "cloned"),
            "--rate", meta.get("rate", "+30%"),
        ] + (["--next-teaser", meta["next_teaser"]] if meta.get("next_teaser") else []))

        yt_video = os.path.join(platform_dir, "youtube.mp4")
        run([
            sys.executable, os.path.join(BASE_DIR, "scripts", "youtube_upload.py"),
            "--video", yt_video,
            "--title", meta["youtube_title"],
            "--description", meta["youtube_description"],
            "--privacy", meta.get("privacy", "private"),
            "--tags", meta.get("tags", ""),
        ])

        date_str = datetime.now().strftime("%Y-%m-%d")
        weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][datetime.now().weekday()]
        day_dir = os.path.join(DELIVERY_DIR, f"{date_str}-{weekday_kr}")
        os.makedirs(day_dir, exist_ok=True)
        tiktok_video = os.path.join(platform_dir, "tiktok.mp4")
        shutil.copy2(yt_video, os.path.join(day_dir, f"유튜브_{date_str}_{name}.mp4"))
        if os.path.exists(tiktok_video):
            caption = meta.get("tiktok_caption", "")
            caption_part = sanitize_filename(caption) if caption else name
            tiktok_filename = f"틱톡_{date_str}_{caption_part}.mp4"
            shutil.copy2(tiktok_video, os.path.join(day_dir, tiktok_filename))
            try:
                tiktok_delivery_path = get_tiktok_delivery_path()
                # OneDrive로 리디렉션된 바탕화면에 파일명에 이모지가 들어간 채로 복사하면
                # cp949 인코딩 에러가 남 (2026-08-26/27 실제로 겪음, day_dir는 OneDrive 밖이라 문제없었음).
                # shutil.copy2는 물론 shutil.copyfile도 큰 파일(mp4)에서는 Windows용 내부 고속복사
                # 경로(_winapi 기반)를 타면서 같은 문제가 재현됨 — 그 경로를 아예 안 쓰도록
                # 순수 파이썬 청크 단위 read/write로 우회.
                with open(tiktok_video, "rb") as fsrc, open(os.path.join(tiktok_delivery_path, tiktok_filename), "wb") as fdst:
                    shutil.copyfileobj(fsrc, fdst)
                log(f"  틱톡 파일 복사 완료 ({tiktok_delivery_path}): {tiktok_filename}")
            except Exception as e:
                log(f"  바탕화면 복사 실패(건너뜀): {e}")
        log(f"  정리 완료: {day_dir}")

        if meta.get("instagram", True) and os.path.exists(tiktok_video):
            ig_caption = meta.get("instagram_caption", meta.get("tiktok_caption", ""))
            ig_name = re.sub(r'[^A-Za-z0-9_-]', '', name) or "video"
            try:
                run([
                    sys.executable, os.path.join(BASE_DIR, "scripts", "publish_instagram.py"),
                    "--video", tiktok_video,
                    "--caption", ig_caption,
                    "--name", f"{date_str}_{ig_name}.mp4",
                ])
                log("  인스타그램 게시 완료")
            except Exception as e:
                log(f"  인스타그램 게시 실패(건너뜀): {e}")

        with open(done_marker, "w", encoding="utf-8") as f:
            f.write(datetime.now().isoformat())
        log(f"done: {name}")
        rel_done = os.path.relpath(done_marker, BASE_DIR)
        rel_log = os.path.relpath(LOG_PATH, BASE_DIR)
        git_commit_push([rel_done, rel_log], f"done: {name}")
        return "processed"
    finally:
        release_lock(item_dir)


def main():
    if not os.path.isdir(QUEUE_DIR):
        log("큐 폴더 없음")
        return
    git_pull()  # 다른 컴퓨터가 먼저 처리/락 건 게 있는지 최신 상태부터 받아옴
    items = sorted(os.listdir(QUEUE_DIR))
    processed = 0
    for name in items:
        item_dir = os.path.join(QUEUE_DIR, name)
        if not os.path.isdir(item_dir):
            continue
        if os.path.exists(os.path.join(item_dir, "done.txt")):
            continue
        try:
            status = process_item(item_dir)
        except Exception as e:
            log(f"error on {name}: {e}")
            break
        if status == "processed":
            processed += 1
            break  # 하루 1개만 처리
        if status == "locked":
            # 다른 컴퓨터가 오늘치를 이미 처리 중 -> 하루 1개 원칙을 지키기 위해 여기서 종료
            break
        # status == "invalid" 인 경우는 이 항목만 건너뛰고 다음 항목을 계속 확인
    if processed == 0:
        log("처리할 대기 항목 없음")


if __name__ == "__main__":
    main()
