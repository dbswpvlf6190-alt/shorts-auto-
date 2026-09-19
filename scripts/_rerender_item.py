"""이미 처리된 대기열 항목을 다시 렌더링하는 수동 도구 (2026-09-19).
run_queue.py는 done.txt가 있는 항목을 건너뛰므로, 목소리 교체/결함 수정 후 영상을 다시 만들 때 쓴다.
유튜브 업로드는 하지 않는다(교체 업로드는 기존 영상 비공개 처리 등 판단이 필요해서 사람이 결정).

사용: python scripts/_rerender_item.py 36 [--delivery] [--instagram]
  --delivery   오늘 날짜 배송 폴더 + 바탕화면의 유튜브/틱톡 파일을 새 렌더로 교체(같은 파일명이면 덮어씀)
  --instagram  publish_instagram.py로 인스타그램 게시
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys
from datetime import datetime

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_queue as rq  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("number", help="대기열 번호 앞자리(예: 36)")
    ap.add_argument("--delivery", action="store_true")
    ap.add_argument("--instagram", action="store_true")
    args = ap.parse_args()

    matches = glob.glob(os.path.join(rq.QUEUE_DIR, f"{int(args.number):02d}_*"))
    if len(matches) != 1:
        raise SystemExit(f"대기열 폴더를 하나로 특정하지 못함: {matches}")
    item_dir = matches[0]
    name = os.path.basename(item_dir)
    with open(os.path.join(item_dir, "meta.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)

    script_path = os.path.join(item_dir, "script.txt")
    render_dir = os.path.join(rq.QUEUE_RENDER_DIR, name)
    work_dir = os.path.join(render_dir, "_work")
    platform_dir = os.path.join(render_dir, "platform")
    os.makedirs(work_dir, exist_ok=True)
    base_video = os.path.join(render_dir, "base.mp4")
    scripts = os.path.join(rq.BASE_DIR, "scripts")

    rq.run([
        sys.executable, os.path.join(scripts, "make_short.py"),
        "--script", script_path, "--images", os.path.join(item_dir, "images"),
        "--voice", meta.get("voice", "cloned"), "--out", base_video, "--work", work_dir,
        "--img-dur", str(meta.get("img_dur", 5)),
    ])
    closing_question = rq.extract_closing_question(script_path)
    rq.run([
        sys.executable, os.path.join(scripts, "make_platform_variants.py"),
        "--base-video", base_video,
        "--yt-hook-lines", meta["yt_hook_lines"],
        "--tiktok-hook-text", meta["tiktok_hook_text"],
        "--out-dir", platform_dir,
        "--voice", meta.get("voice", "cloned"),
        "--rate", meta.get("rate", "+30%"),
    ] + (["--next-teaser", meta["next_teaser"]] if meta.get("next_teaser") else [])
      + (["--closing-question", closing_question] if closing_question else []))
    print(f"렌더 완료: {platform_dir}")

    yt_video = os.path.join(platform_dir, "youtube.mp4")
    tiktok_video = os.path.join(platform_dir, "tiktok.mp4")
    date_str = datetime.now().strftime("%Y-%m-%d")

    if args.delivery:
        weekday_kr = ["월", "화", "수", "목", "금", "토", "일"][datetime.now().weekday()]
        day_dir = os.path.join(rq.DELIVERY_DIR, f"{date_str}-{weekday_kr}")
        os.makedirs(day_dir, exist_ok=True)
        shutil.copy2(yt_video, os.path.join(day_dir, f"유튜브_{date_str}_{name}.mp4"))
        caption = meta.get("tiktok_caption", "")
        tiktok_filename = f"틱톡_{date_str}_{rq.sanitize_filename(caption) if caption else name}.mp4"
        shutil.copy2(tiktok_video, os.path.join(day_dir, tiktok_filename))
        desktop = rq.get_tiktok_delivery_path()
        with open(tiktok_video, "rb") as fsrc, open(os.path.join(desktop, tiktok_filename), "wb") as fdst:
            shutil.copyfileobj(fsrc, fdst)
        print(f"배송 파일 교체 완료: {day_dir} / {desktop}")

    if args.instagram:
        ig_name = re.sub(r"[^A-Za-z0-9_-]", "", name) or "video"
        rq.run([
            sys.executable, os.path.join(scripts, "publish_instagram.py"),
            "--video", tiktok_video,
            "--caption", meta.get("instagram_caption", meta.get("tiktok_caption", "")),
            "--name", f"{date_str}_{ig_name}.mp4",
        ])
        print("인스타그램 게시 완료")


if __name__ == "__main__":
    main()
