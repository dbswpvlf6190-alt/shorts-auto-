"""로컬 AI 이미지 생성 (2026-09-20). 무료·오프라인. vendor/imagegen/venv 파이썬으로 실행해야 함.

모델: Lykon/dreamshaper-8 (SD1.5 계열, CreativeML OpenRAIL-M = 상업 이용 가능)
     + latent-consistency/lcm-lora-sdv1-5 (4단계 생성용 LoRA)
사용: vendor/imagegen/venv/Scripts/python scripts/imagegen_local.py --prompts-file p.json --out-dir out/
      p.json = [{"name": "01", "prompt": "..."}, ...]   (프롬프트는 영어가 가장 잘 먹음)
모델은 한 번만 로드하고 여러 장을 연속 생성한다(로딩이 오래 걸려서).
"""
import argparse
import json
import os
import sys
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import torch
from diffusers import LCMScheduler, StableDiffusionPipeline

MODEL = "Lykon/dreamshaper-8"
LORA = "latent-consistency/lcm-lora-sdv1-5"
NEGATIVE = "text, watermark, logo, letters, words, cartoon, illustration, drawing, deformed, blurry, low quality, extra fingers"


def load_pipe():
    pipe = StableDiffusionPipeline.from_pretrained(MODEL, torch_dtype=torch.float32, safety_checker=None)
    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
    pipe.load_lora_weights(LORA)
    pipe.fuse_lora()
    pipe.set_progress_bar_config(disable=True)
    return pipe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts-file", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--width", type=int, default=512)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    with open(args.prompts_file, "r", encoding="utf-8") as f:
        items = json.load(f)
    os.makedirs(args.out_dir, exist_ok=True)
    torch.set_num_threads(os.cpu_count() or 4)

    t0 = time.time()
    pipe = load_pipe()
    print(f"model loaded in {time.time() - t0:.0f}s", flush=True)
    for it in items:
        t = time.time()
        gen = torch.Generator("cpu").manual_seed(args.seed)
        img = pipe(
            prompt=it["prompt"], negative_prompt=NEGATIVE, width=args.width, height=args.height,
            num_inference_steps=args.steps, guidance_scale=1.0, generator=gen,
        ).images[0]
        path = os.path.join(args.out_dir, f"{it['name']}.png")
        img.save(path)
        print(f"{it['name']}: {time.time() - t:.0f}s -> {path}", flush=True)


if __name__ == "__main__":
    main()
