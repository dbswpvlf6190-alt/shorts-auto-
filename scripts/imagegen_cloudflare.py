"""Cloudflare Workers AI(FLUX.1 schnell)로 이미지 생성 (2026-09-20). 무료 하루 10,000 뉴런(약 170장).
자격증명: credentials/cloudflare.json (git 제외). 표준 라이브러리만 사용.

사용: python scripts/imagegen_cloudflare.py --prompts-file p.json --out-dir out/ [--width 720 --height 1280 --steps 4]
      p.json = [{"name": "01", "prompt": "..."}]
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRED_PATH = os.path.join(BASE_DIR, "credentials", "cloudflare.json")
MODEL = "@cf/black-forest-labs/flux-1-schnell"


def generate(prompt, out_path, steps=4, width=None, height=None, seed=None):
    with open(CRED_PATH, "r", encoding="utf-8") as f:
        cred = json.load(f)
    url = f"https://api.cloudflare.com/client/v4/accounts/{cred['account_id']}/ai/run/{MODEL}"
    body = {"prompt": prompt, "steps": steps}
    if width:
        body["width"] = width
    if height:
        body["height"] = height
    if seed is not None:
        body["seed"] = seed
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {cred['api_token']}", "Content-Type": "application/json", "User-Agent": "shorts-auto"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Cloudflare HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}")
    if not data.get("success"):
        raise RuntimeError(f"Cloudflare error: {str(data.get('errors'))[:300]}")
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(data["result"]["image"]))
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts-file", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--steps", type=int, default=4)
    args = ap.parse_args()
    with open(args.prompts_file, "r", encoding="utf-8") as f:
        items = json.load(f)
    os.makedirs(args.out_dir, exist_ok=True)
    for it in items:
        t = time.time()
        path = os.path.join(args.out_dir, f"{it['name']}.jpg")
        generate(it["prompt"], path, args.steps, args.width, args.height)
        print(f"{it['name']}: {time.time() - t:.1f}s -> {path}", flush=True)


if __name__ == "__main__":
    main()
