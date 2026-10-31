"""롱폼 그림 미리 만들기(2026-10-30). make_longform은 그림 생성이 한도(429)로 실패하면 앞 그림을 돌려 써서
같은 그림이 반복된다(03 첫 렌더에서 6장이 약 50번 반복). 렌더 전에 이 스크립트로 썸네일·장면 그림을 전부
캐시(`<out-dir>/_work/images`, make_longform과 같은 파일 이름)에 만들어 두고, 다 모였을 때만 렌더한다.
한도에 걸리면 기다렸다가 이어서 만든다(한도는 최근 24시간 사용량 기준이라 조금씩 풀린다).

종료 코드: 0 = 전부 준비됨, 2 = 제한 시간 안에 다 못 만듦(남은 개수 출력)."""
import argparse
import hashlib
import json
import os
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_longform as L  # noqa: E402


def targets(meta, img_dir):
    out = []
    for key in ("thumbnail", "thumbnail_b"):
        art = meta.get(key, {}).get("art_prompt")
        if art:
            out.append((art, os.path.join(img_dir, "thumb_art_" + hashlib.md5(art.encode("utf-8")).hexdigest()[:12] + ".png")))
    for ch in meta["chapters"]:
        for sc in ch["scenes"]:
            if sc["kind"] == "art":
                p = os.path.join(img_dir, "art_" + hashlib.md5(sc["image_prompt"].encode("utf-8")).hexdigest()[:12] + ".png")
                if all(p != q for _, q in out):
                    out.append((sc["image_prompt"], p))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-hours", type=float, default=6)
    ap.add_argument("--wait-min", type=float, default=5, help="한도에 걸렸을 때 다시 시도하기 전 기다리는 분")
    args = ap.parse_args()

    meta = json.load(open(args.meta, encoding="utf-8"))
    img_dir = os.path.join(args.out_dir, "_work", "images")
    os.makedirs(img_dir, exist_ok=True)
    todo = [(pr, p) for pr, p in targets(meta, img_dir) if not os.path.exists(p)]
    total = len(targets(meta, img_dir))
    print(f"그림 {total}장 중 {total - len(todo)}장 이미 있음, {len(todo)}장 생성", flush=True)
    deadline = time.time() + args.max_hours * 3600
    while todo:
        prompt, p = todo[0]
        if L.gen_art(prompt, p):
            todo.pop(0)
            print(f"  {time.strftime('%H:%M:%S')} {total - len(todo)}/{total}", flush=True)
            continue
        if time.time() > deadline:
            print(f"제한 시간 초과: {len(todo)}장 남음", flush=True)
            sys.exit(2)
        print(f"  {time.strftime('%H:%M:%S')} 한도 — {args.wait_min:.0f}분 뒤 다시 ({len(todo)}장 남음)", flush=True)
        time.sleep(args.wait_min * 60)
    print("그림 준비 완료", flush=True)


if __name__ == "__main__":
    main()
