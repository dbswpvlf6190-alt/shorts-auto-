"""v2 영상 포맷 빌더 (2026-09-20). 결과 먼저·금액 예시·중간 반전·애니메이션 자막·효과음.
입력: meta.json의 "scenes" 배열(장면마다 voice 문장 + 화면 종류). 스키마는 docs/script_template_v2.md 참고.
출력: out-dir/youtube.mp4, tiktok.mp4(동일 영상 복사), thumb.png(첫 장면 완성 프레임), v2_report.json.
이미지는 Cloudflare FLUX(scripts/imagegen_cloudflare.py)로 장면별 생성하고, 실패하면 그라데이션 배경으로 대체해 계속 진행한다.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import time

import numpy as np
import soundfile as sf

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageEnhance  # noqa: E402
import imagegen_cloudflare as cf  # noqa: E402
import make_graphic as gfx  # noqa: E402
import make_short as base  # noqa: E402

W, H, FPS = 1080, 1920, 30
GOLD = (242, 193, 78)
WHITE = (247, 248, 250)
RED = (255, 96, 96)
GREEN = (120, 220, 140)
COLORS = {"green": GREEN, "gold": GOLD, "red": RED, "white": WHITE}
KINDS = ("photo", "big", "money", "timeline")
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def strip_marks(s):
    return s.replace("{", "").replace("}", "").replace("[", "").replace("]", "")


def fit_font(draw, lines, max_w, start=96, min_size=52):
    size = start
    while size > min_size:
        f = gfx.font(size)
        if all(draw.textlength(strip_marks(ln), font=f) <= max_w for ln in lines):
            return f
        size -= 4
    return gfx.font(min_size)


def caption_layer(text, cy, max_w=940):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lines = text.split("\n")
    f = fit_font(d, lines, max_w)
    line_h = f.size + 26
    y = H * cy - line_h * len(lines) / 2
    for ln in lines:
        segs, color, buf = [], WHITE, ""
        for ch in ln:
            if ch in "{[":
                if buf:
                    segs.append((buf, color))
                buf, color = "", (GOLD if ch == "{" else RED)
            elif ch in "}]":
                if buf:
                    segs.append((buf, color))
                buf, color = "", WHITE
            else:
                buf += ch
        if buf:
            segs.append((buf, color))
        total = sum(d.textlength(s, font=f) for s, _ in segs)
        x = W / 2 - total / 2
        for s, c in segs:
            d.text((x, y), s, font=f, fill=c + (255,), stroke_width=9, stroke_fill=(0, 0, 0, 255))
            x += d.textlength(s, font=f)
        y += line_h
    return layer


def cover(path):
    im = Image.open(path).convert("RGB")
    scale = H / im.height
    im = im.resize((int(im.width * scale), H), Image.LANCZOS)
    left = (im.width - W) // 2
    im = im.crop((left, 0, left + W, H))
    return ImageEnhance.Brightness(im).enhance(0.72)


def gradient_bg():
    img = gfx.vertical_gradient(W, H, gfx.BG_TOP, gfx.BG_BOTTOM)
    return gfx.add_glow(img, (W // 2, H // 2), 520, gfx.ACCENT, opacity=45)


def add_source(img, source):
    if not source:
        return img
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = gfx.font(34, bold=False)
    tw = d.textlength(source, font=f)
    d.text((W / 2 - tw / 2, 1810), source, font=f, fill=(235, 236, 240, 200), stroke_width=4, stroke_fill=(0, 0, 0, 200))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def make_base(scene, image_path, source):
    kind = scene["kind"]
    im = cover(image_path) if (kind == "photo" and image_path) else gradient_bg()
    d = ImageDraw.Draw(im)
    if kind == "timeline":
        cards = scene["cards"]
        active = scene.get("active", "all")
        n = len(cards)
        ch, gap = 240, 34
        top = 1710 - (n * ch + (n - 1) * gap)
        for i, card in enumerate(cards):
            y0 = top + i * (ch + gap)
            on = active == "all" or i in (active if isinstance(active, list) else [active])
            col = COLORS.get(card.get("color", "white"), WHITE)
            d.rounded_rectangle([90, y0, W - 90, y0 + ch], radius=36, fill=(40, 54, 84) if on else (30, 40, 60),
                                outline=col if on else (70, 80, 100), width=8 if on else 3)
            d.text((150, y0 + 22), card["date"], font=gfx.font(84), fill=WHITE if on else (120, 130, 150))
            who = card.get("who", "")
            d.text((150, y0 + 128), who, font=gfx.font(48 if len(who) > 6 else 64), fill=col if on else (110, 120, 140))
    if kind == "big":
        f = gfx.font(150)
        while d.textlength(scene["big"], font=f) > 940 and f.size > 70:
            f = gfx.font(f.size - 8)
        tw = d.textlength(scene["big"], font=f)
        d.text((W / 2 - tw / 2, H * 0.44), scene["big"], font=f, fill=GOLD, stroke_width=7, stroke_fill=(0, 0, 0))
    return add_source(im, source)


def extras(scene, base_img, t):
    im = base_img.copy()
    d = ImageDraw.Draw(im)
    kind = scene["kind"]
    if kind == "money":
        n = int(round(scene["amount"] * ease(t / 0.9)))
        f = gfx.font(230)
        txt = f"{n}{scene.get('unit', '만 원')}"
        tw = d.textlength(txt, font=f)
        d.text((W / 2 - tw / 2, H * 0.44), txt, font=f, fill=GOLD, stroke_width=10, stroke_fill=(0, 0, 0))
        note = scene.get("note", "(예시 금액)")
        if note:
            f2 = gfx.font(46, bold=False)
            d.text((W / 2 - d.textlength(note, font=f2) / 2, H * 0.44 + 290), note, font=f2, fill=(190, 198, 212))
    if kind == "big" and scene.get("badge") and t > 0.45:
        s = 0.7 + 0.3 * ease((t - 0.45) / 0.25)
        pill = Image.new("RGBA", (int(620 * s), int(150 * s)), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle([0, 0, pill.width - 1, pill.height - 1], radius=int(75 * s), fill=(220, 60, 60, 255))
        pf = gfx.font(int(74 * s))
        label = scene["badge"]
        pd.text((pill.width / 2 - pd.textlength(label, font=pf) / 2, pill.height / 2 - pf.size / 2 - 6), label, font=pf, fill=(255, 255, 255, 255))
        im.paste(pill, (int(W / 2 - pill.width / 2), int(H * 0.64)), pill)
    return im


def compose(scene, base_img, cap, t):
    im = extras(scene, base_img, t) if scene["kind"] in ("money", "big") else base_img.copy()
    p = ease(t / 0.25)
    s = 0.88 + 0.12 * p
    layer = cap.resize((int(W * s), int(H * s)), Image.LANCZOS)
    layer.putalpha(layer.getchannel("A").point(lambda v: int(v * p)))
    im = im.convert("RGBA")
    im.alpha_composite(layer, (int((W - layer.width) / 2), int((H - layer.height) / 2)))
    return im.convert("RGB")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"failed: {' '.join(cmd[:5])}\n{r.stderr[-1500:]}")


def get_image(i, scene, img_dir):
    if scene["kind"] != "photo":
        return None
    p = os.path.join(img_dir, f"scene_{i:02d}.jpg")
    if os.path.exists(p):
        return p
    prompt = scene.get("image_prompt")
    if not prompt:
        return None
    if "no text" not in prompt.lower():
        prompt += ", no text"
    for attempt in range(3):
        try:
            cf.generate(prompt, p, steps=4)
            return p
        except Exception as e:  # 네트워크/한도/토큰 문제 — 이 장면만 그라데이션으로 대체
            print(f"  이미지 생성 실패 scene {i} (시도 {attempt + 1}/3): {str(e)[:120]}", flush=True)
            time.sleep(2)
    return None


def render_scene(work, i, scene, image_path, source, dur):
    base_img = make_base(scene, image_path, source)
    cy = scene.get("cy", 0.53 if scene["kind"] == "photo" else 0.27)
    cap = caption_layer(scene["caption"], cy)
    intro_t = 0.95 if scene["kind"] == "money" else (0.75 if (scene["kind"] == "big" and scene.get("badge")) else 0.25)
    n_intro = min(int(intro_t * FPS), max(int(dur * FPS) - 1, 1))
    fdir = os.path.join(work, f"f{i:02d}")
    os.makedirs(fdir, exist_ok=True)
    for k in range(n_intro):
        compose(scene, base_img, cap, k / FPS).save(os.path.join(fdir, f"{k:04d}.png"))
    final_png = os.path.join(work, f"final_{i:02d}.png")
    compose(scene, base_img, cap, 5.0).save(final_png)
    intro_mp4 = os.path.join(work, f"intro_{i:02d}.mp4")
    hold_mp4 = os.path.join(work, f"hold_{i:02d}.mp4")
    run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(fdir, "%04d.png"), *ENC, intro_mp4])
    run(["ffmpeg", "-y", "-loop", "1", "-i", final_png, "-t", f"{max(dur - n_intro / FPS, 1 / FPS):.3f}", *ENC, hold_mp4])
    lst = os.path.join(work, f"c_{i:02d}.txt")
    with open(lst, "w", encoding="utf-8") as f:
        f.write(f"file '{os.path.basename(intro_mp4)}'\nfile '{os.path.basename(hold_mp4)}'\n")
    out = os.path.join(work, f"scene_{i:02d}.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    shutil.rmtree(fdir, ignore_errors=True)
    return out, final_png


def whoosh(sr, dur=0.26, amp=0.10):
    rng = np.random.default_rng(3)
    n = int(sr * dur)
    noise = rng.standard_normal(n)
    y, prev = np.zeros(n), 0.0
    for i in range(n):
        prev += (0.02 + 0.45 * math.sin(math.pi * i / n)) * (noise[i] - prev)
        y[i] = prev
    y = y / (np.max(np.abs(y)) + 1e-9)
    return y * (np.sin(np.pi * np.linspace(0, 1, n)) ** 2) * amp


def impact(sr, dur=0.6, amp=0.30):
    t = np.arange(int(sr * dur)) / sr
    rng = np.random.default_rng(5)
    return amp * (np.sin(2 * np.pi * 55 * t) * np.exp(-t * 8) + 0.35 * rng.standard_normal(len(t)) * np.exp(-t * 45))


def ding(sr, dur=0.55, amp=0.11):
    t = np.arange(int(sr * dur)) / sr
    return amp * (np.sin(2 * np.pi * 1318 * t) * np.exp(-t * 5) + 0.5 * np.sin(2 * np.pi * 1976 * t) * np.exp(-t * 7))


def mix_audio(voice_path, scenes, starts, out_path):
    v, sr = sf.read(voice_path, dtype="float32")
    if v.ndim > 1:
        v = v.mean(axis=1)
    track = np.zeros(len(v) + sr)
    track[:len(v)] += v

    def put(sig, t):
        i = int(t * sr)
        if i < len(track):
            track[i:i + len(sig)] += sig[:len(track) - i]

    for k, (sc, s) in enumerate(zip(scenes, starts)):
        if k > 0:
            put(whoosh(sr), max(s - 0.05, 0))
        if k == 0:
            put(impact(sr), 0.0)
        if sc["kind"] == "money":
            put(impact(sr, amp=0.22), s)
        if sc.get("sfx") == "ding":
            put(ding(sr), s + 0.05)
    peak = np.max(np.abs(track))
    if peak > 0.95:
        track *= 0.95 / peak
    sf.write(out_path, track[:len(v)], sr)


def validate(scenes):
    if not scenes:
        raise ValueError("scenes가 비어 있음")
    for i, sc in enumerate(scenes):
        if sc.get("kind") not in KINDS:
            raise ValueError(f"scene {i}: kind는 {KINDS} 중 하나여야 함 ({sc.get('kind')})")
        for key in ("voice", "caption"):
            if not str(sc.get(key, "")).strip():
                raise ValueError(f"scene {i}: {key} 누락")
        if sc["kind"] == "big" and not sc.get("big"):
            raise ValueError(f"scene {i}: big 누락")
        if sc["kind"] == "money" and not isinstance(sc.get("amount"), (int, float)):
            raise ValueError(f"scene {i}: amount(숫자) 누락")
        if sc["kind"] == "timeline" and not sc.get("cards"):
            raise ValueError(f"scene {i}: cards 누락")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--work", default=None)
    ap.add_argument("--rate", default=None)
    args = ap.parse_args()

    with open(args.meta, "r", encoding="utf-8") as f:
        meta = json.load(f)
    scenes = meta["scenes"]
    validate(scenes)
    source = meta.get("source_label", "")
    rate = args.rate or meta.get("rate", "+15%")
    os.makedirs(args.out_dir, exist_ok=True)
    work = args.work or os.path.join(args.out_dir, "_v2_work")
    img_dir = os.path.join(work, "images")
    os.makedirs(img_dir, exist_ok=True)

    text = " ".join(s["voice"].strip() for s in scenes)
    audio = os.path.join(work, "voice.wav")
    t0 = time.time()
    words = base.tts_cloned_voice(text, work, audio, rate)
    total = base.get_duration(audio)
    print(f"voice {total:.1f}s ({len(text)}자, {time.time() - t0:.0f}s)", flush=True)
    counts = [len(s["voice"].strip().split(" ")) for s in scenes]
    if sum(counts) != len(words):
        raise RuntimeError(f"음성 단어 수 불일치: 대본 {sum(counts)} vs 타이밍 {len(words)}")
    starts, idx = [], 0
    for c in counts:
        starts.append(words[idx][0])
        idx += c
    starts[0] = 0.0
    ends = starts[1:] + [total]

    clips, finals, report = [], [], []
    for i, (sc, s, e) in enumerate(zip(scenes, starts, ends)):
        img = get_image(i, sc, img_dir)
        clip, final_png = render_scene(work, i, sc, img, source, max(e - s, 0.5))
        clips.append(clip)
        finals.append(final_png)
        report.append({"scene": i, "kind": sc["kind"], "start": round(s, 2), "end": round(e, 2), "image": bool(img) if sc["kind"] == "photo" else None})
        print(f"scene {i:>2} {sc['kind']:<8} {s:5.1f}-{e:5.1f}s", flush=True)

    lst = os.path.join(work, "concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{os.path.basename(c)}'\n")
    video = os.path.join(work, "video_only.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])
    mixed = os.path.join(work, "mixed.wav")
    mix_audio(audio, scenes, starts, mixed)
    youtube = os.path.join(args.out_dir, "youtube.mp4")
    run(["ffmpeg", "-y", "-i", video, "-i", mixed, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", youtube])
    shutil.copy2(youtube, os.path.join(args.out_dir, "tiktok.mp4"))
    shutil.copy2(finals[0], os.path.join(args.out_dir, "thumb.png"))
    with open(os.path.join(args.out_dir, "v2_report.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": total, "chars": len(text), "scenes": report}, f, ensure_ascii=False, indent=1)
    print(f"done: {youtube} ({base.get_duration(youtube):.1f}s)", flush=True)


if __name__ == "__main__":
    main()
