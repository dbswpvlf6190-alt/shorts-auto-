"""롱폼 그림 마저 만들기 → 렌더 → 폰 알림 (2026-11-22). 업로드는 하지 않는다(사람 검수 후 upload_longform.py).
사용: python scripts/run_longform_job.py 12_자녀증여세금폭탄 [--start-after 11:50] [--max-hours 8]
- --start-after: 이 시각(오늘, KST)까지 기다렸다가 시작한다. 아침 8시 쇼츠가 쓸 그림 몫(무료 한도, 최근 24시간 기준)을
  먼저 쓰지 않으려고 정오 무렵부터 돌린다.
- 다른 컴퓨터에서 만든 그림을 git으로 넘겨받았다면 input/longform/<이름>/_art_cache/*.png를 렌더 폴더 캐시로 먼저 복사한다.
- 돌아가는 동안 절전을 막는다(노트북 무인 실행 대비, run_queue와 같은 방식)."""
import argparse
import ctypes
import datetime
import glob
import os
import shutil
import subprocess
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="input/longform 아래 폴더 이름(예: 12_자녀증여세금폭탄)")
    ap.add_argument("--start-after", default="", help="HH:MM — 이 시각까지 기다렸다가 시작")
    ap.add_argument("--max-hours", default="8")
    args = ap.parse_args()
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    except Exception:
        pass
    src = os.path.join(BASE, "input", "longform", args.name)
    meta = os.path.join(src, "meta.json")
    out = os.path.join(os.environ.get("SHORTS_RENDER_DIR", os.path.join(os.path.expanduser("~"), "ShortsAutoRender")), "longform", args.name)
    img = os.path.join(out, "_work", "images")
    os.makedirs(img, exist_ok=True)

    if args.start_after:
        h, m = map(int, args.start_after.split(":"))
        start = datetime.datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        while datetime.datetime.now() < start:
            print(f"{datetime.datetime.now():%H:%M} — {args.start_after}까지 대기", flush=True)
            time.sleep(min(600, max(5, (start - datetime.datetime.now()).total_seconds())))

    copied = 0
    for f in glob.glob(os.path.join(src, "_art_cache", "*.png")):
        dst = os.path.join(img, os.path.basename(f))
        if not os.path.exists(dst):
            shutil.copy2(f, dst)
            copied += 1
    print(f"넘겨받은 그림 {copied}장 복사 → {img}", flush=True)

    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    print("그림 마저 만들기 시작", flush=True)
    r = subprocess.run([sys.executable, os.path.join(BASE, "scripts", "pregen_longform_art.py"), "--meta", meta, "--out-dir", out,
                        "--max-hours", args.max_hours], cwd=BASE, env=env)
    if r.returncode != 0:
        _notify(f"⚠️ 롱폼 {args.name} 그림이 다 안 모임", "한도에 걸려 시간 안에 못 끝냄 — 나중에 같은 명령을 다시 실행")
        sys.exit(r.returncode)
    print("렌더 시작", flush=True)
    with open(os.path.join(out, "_render.log"), "w", encoding="utf-8") as f:
        r = subprocess.run([sys.executable, os.path.join(BASE, "scripts", "make_longform.py"), "--meta", meta, "--out-dir", out],
                           cwd=BASE, stdout=f, stderr=subprocess.STDOUT, env=env)
    ok = r.returncode == 0 and os.path.exists(os.path.join(out, "long.mp4"))
    print("렌더 " + ("완료: " + os.path.join(out, "long.mp4") if ok else "실패 — _render.log 확인"), flush=True)
    _notify(("🎬 롱폼 렌더 완료: " if ok else "❌ 롱폼 렌더 실패: ") + args.name, "검수 후 사장님 확인 → 예약(업로드는 아직 안 함)")
    sys.exit(0 if ok else 1)


def _notify(title, msg):
    try:
        import notify
        notify.notify(title, msg, priority=3)
    except Exception:
        pass


if __name__ == "__main__":
    main()
