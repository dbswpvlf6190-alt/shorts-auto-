"""롱폼(가로 1920x1080) 정보 해설 영상 빌더 (2026-10-29 시제품).
v1(글자 카드 위주)은 "보는 재미가 없다"는 피드백을 받았다. 그래서 v2는 성적이 가장 좋은 경제해적단형으로 바꿨다:
영화풍 AI 그림(`art`, FLUX.2 klein 16:9)이 7~10초마다 바뀌고, 그 위에 큰 한글 제목·영어 부제·숫자를 우리가 얹는다(그림 속 글자는 깨지므로).
그림은 천천히 확대·축소된다. 밝은 정보 카드(cards·checklist 등)는 금액·날짜 정리용으로 일부만 쓴다.
입력: meta.json의 "chapters"(장마다 scenes). 스키마는 docs/script_template_longform.md.
출력: out-dir/long.mp4, thumb.png(1280x720), chapters.txt(유튜브 설명용), long_report.json, frames/(장면별 대표 프레임).
음성은 장(chapter)마다 따로 합성해 캐시한다 — 화면만 고쳐 다시 렌더할 때 음성은 다시 만들지 않는다(--fresh-voice로 강제).
"""
import argparse
import hashlib
import json
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
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter  # noqa: E402
import base64  # noqa: E402
import urllib.request  # noqa: E402
import uuid  # noqa: E402
import imagegen_cloudflare as cf  # noqa: E402
import make_graphic as gfx  # noqa: E402
import make_short as base  # noqa: E402
import make_video_v2 as v2  # noqa: E402

BRAND = "도장찍기전에"  # 10/29 채널 이름 변경(데일리.팩트랩 → 도장찍기전에). 롱폼은 유튜브 전용이라 새 이름을 쓴다
W, H, FPS = 1920, 1080, 30
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS)]  # 10/29: 어두운 그림이 많아 유튜브 변환 후 화질 확보용으로 20→17
CHAPTER_GAP = 0.6  # 장 사이 쉼(초)

BG = (244, 246, 250)
NAVY = (20, 32, 56)
INK = (28, 34, 48)
MUTED = (110, 118, 134)
CARD = (255, 255, 255)
LINE = (222, 226, 234)
ORANGE = (226, 120, 0)   # 밝은 배경용 강조 {…}
RED = (214, 48, 49)      # 밝은 배경용 경고 […]
GOLD = gfx.ACCENT
GREEN = (34, 150, 90)
COLORS = {"orange": ORANGE, "red": RED, "green": GREEN, "navy": NAVY, "gold": GOLD}
KINDS = ("art", "title", "cards", "number", "checklist", "compare", "timeline", "photo", "quote")
ART_W, ART_H = 1280, 720
KLEIN = "@cf/black-forest-labs/flux-2-klein-4b"
ART_STYLE = ("dark cinematic digital illustration, dramatic moody lighting, rich detail, epic composition, "
             "{p}, no text, no letters, no numbers, no signs")
HEAD_H = 96
SUB_TOP = 880  # 이 아래는 자막 자리 — 카드가 들어오지 않게 한다


def ease(x):
    return v2.ease(x)


# ---------- 글자 ----------
def segs_of(text, base_col, hi=ORANGE, warn=RED):
    """{강조}·[경고] 마크업을 (글자, 색) 조각으로."""
    segs, col, buf = [], base_col, ""
    for ch in text:
        if ch in "{[":
            if buf:
                segs.append((buf, col))
            buf, col = "", (hi if ch == "{" else warn)
        elif ch in "}]":
            if buf:
                segs.append((buf, col))
            buf, col = "", base_col
        else:
            buf += ch
    if buf:
        segs.append((buf, col))
    return segs


def plain(text):
    return v2.strip_marks(text)


def fit(d, lines, max_w, start, min_size=28, bold=True):
    size = start
    while size > min_size:
        f = gfx.font(size, bold)
        if all(d.textlength(plain(ln), font=f) <= max_w for ln in lines):
            return f
        size -= 2
    return gfx.font(min_size, bold)


def wrap(d, text, f, max_w):
    """단어 단위 줄바꿈(\n은 강제 줄바꿈). 마크업은 줄을 넘어가도 유지되게 줄마다 다시 열어 준다."""
    out = []
    for para in text.split("\n"):
        line, open_mark = "", ""
        for word in para.split(" "):
            cand = (line + " " + word).strip()
            if line and d.textlength(plain(cand), font=f) > max_w:
                out.append(line)
                line = open_mark + word
            else:
                line = cand
            for ch in word:
                if ch in "{[":
                    open_mark = ch
                elif ch in "}]":
                    open_mark = ""
        if open_mark:
            close = "}" if open_mark == "{" else "]"
            out.append(line + close)
        else:
            out.append(line)
    return out


def draw_rich(d, xy, text, f, base_col, anchor="l", stroke=0, stroke_fill=None, hi=ORANGE, warn=RED):
    segs = segs_of(text, base_col, hi, warn)
    total = sum(d.textlength(s, font=f) for s, _ in segs)
    x, y = xy
    if anchor == "c":
        x -= total / 2
    elif anchor == "r":
        x -= total
    for s, c in segs:
        d.text((x, y), s, font=f, fill=c, stroke_width=stroke, stroke_fill=stroke_fill)
        x += d.textlength(s, font=f)
    return total


def draw_block(d, text, f, max_w, x, y, col, anchor="l", gap=12, **kw):
    lines = wrap(d, text, f, max_w)
    for ln in lines:
        draw_rich(d, (x, y), ln, f, col, anchor=anchor, **kw)
        y += f.size + gap
    return y


# ---------- 공통 틀 ----------
def frame_base(ctx, dark=False):
    if dark:
        im = gfx.vertical_gradient(W, H, gfx.BG_TOP, gfx.BG_BOTTOM)
        im = gfx.add_glow(im, (W // 2, H // 2 - 80), 620, gfx.ACCENT, opacity=40)
    else:
        im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, HEAD_H], fill=NAVY)
    d.rectangle([0, HEAD_H, W, HEAD_H + 6], fill=GOLD)
    tag = ctx.get("tag", "")
    if tag:
        d.text((48, 22), tag, font=gfx.font(42), fill=(255, 255, 255))
    lf = gfx.font(36)
    d.text((W - 48 - d.textlength(BRAND, font=lf), 28), BRAND, font=lf, fill=GOLD)
    src = ctx.get("source", "")
    if src:
        sf_ = gfx.font(26, bold=False)
        d.text((W - 48 - d.textlength(src, font=sf_), HEAD_H + 18), src, font=sf_, fill=(200, 205, 215) if dark else MUTED)
    return im


def heading(d, text, y=150, dark=False):
    f = fit(d, [text], W - 200, 66, 44)
    draw_rich(d, (W / 2, y), text, f, (255, 255, 255) if dark else INK, anchor="c", hi=GOLD if dark else ORANGE)
    return y + f.size + 40


def shadow_card(im, box, radius=28, fill=CARD, outline=None, width=0):
    x0, y0, x1, y1 = [int(v) for v in box]
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 4, y0 + 10, x1 + 4, y1 + 10], radius=radius, fill=(20, 30, 50, 40))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    im.paste(Image.alpha_composite(im.convert("RGBA"), sh).convert("RGB"))
    ImageDraw.Draw(im).rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


def fade_in(im_from, im_to, p):
    return Image.blend(im_from, im_to, ease(p)) if p < 1 else im_to


# ---------- 장면 종류 ----------
def draw_title(sc, ctx, t):
    im = frame_base({**ctx, "source": ""}, dark=True)
    d = ImageDraw.Draw(im)
    p = ease(t / 0.5)
    num = sc.get("number", "")
    cy = 470
    if num:
        r = 92
        d.ellipse([W / 2 - r, cy - 250 - r, W / 2 + r, cy - 250 + r], fill=GOLD)
        nf = gfx.font(120)
        d.text((W / 2 - d.textlength(num, font=nf) / 2, cy - 250 - 78), num, font=nf, fill=NAVY)
    f = fit(d, sc["title"].split("\n"), W - 240, 104, 60)
    y = cy - 40 + int((1 - p) * 30)
    for ln in sc["title"].split("\n"):
        draw_rich(d, (W / 2, y), ln, f, (255, 255, 255), anchor="c", hi=GOLD, warn=(255, 110, 110), stroke=4, stroke_fill=(0, 0, 0))
        y += f.size + 24
    if sc.get("sub"):
        sfnt = gfx.font(46, bold=False)
        draw_block(d, sc["sub"], sfnt, W - 400, W / 2, y + 30, (215, 220, 230), anchor="c", hi=GOLD)
    return im


def draw_cards(sc, ctx, t, reveal):
    im = frame_base(ctx)
    d = ImageDraw.Draw(im)
    top = heading(d, sc.get("heading", "")) if sc.get("heading") else 160
    cards = sc["cards"]
    n = len(cards)
    gap = 44
    cw = (W - 160 - gap * (n - 1)) / n
    bf = gfx.font(42, bold=False)

    def need(c):
        h = 54 + (82 if c.get("label") else 0)
        tf = fit(d, wrap(d, c["title"], gfx.font(68), cw - 60), cw - 60, 68, 40)
        h += len(wrap(d, c["title"], tf, cw - 60)) * (tf.size + 10)
        if c.get("body"):
            h += 26 + len(wrap(d, c["body"], bf, cw - 70)) * (bf.size + 12)
        return h + 50
    avail = SUB_TOP - 30 - top
    ch = min(max(max(need(c) for c in cards), 360), avail)
    top = top + (avail - ch) / 2
    for i, c in enumerate(cards):
        if i >= reveal:
            break
        x0 = 80 + i * (cw + gap)
        col = COLORS.get(c.get("color", "navy"), NAVY)
        shadow_card(im, (x0, top, x0 + cw, top + ch))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([x0, top, x0 + cw, top + 18], radius=9, fill=col)
        y = top + 54
        if c.get("label"):
            lf = gfx.font(30)
            lw = d.textlength(c["label"], font=lf) + 36
            d.rounded_rectangle([x0 + cw / 2 - lw / 2, y, x0 + cw / 2 + lw / 2, y + 50], radius=25, fill=col)
            d.text((x0 + cw / 2 - lw / 2 + 18, y + 6), c["label"], font=lf, fill=(255, 255, 255))
            y += 82
        tf = fit(d, wrap(d, c["title"], gfx.font(68), cw - 60), cw - 60, 68, 40)
        y = draw_block(d, c["title"], tf, cw - 60, x0 + cw / 2, y, INK, anchor="c", gap=10)
        if c.get("body"):
            draw_block(d, c["body"], bf, cw - 70, x0 + cw / 2, y + 26, MUTED, anchor="c", gap=12)
    return im


def draw_number(sc, ctx, t):
    im = frame_base(ctx)
    d = ImageDraw.Draw(im)
    top = heading(d, sc["heading"]) if sc.get("heading") else 200
    amount = sc["amount"]
    val = amount * ease(t / 0.9)
    shown = f"{val:.1f}" if isinstance(amount, float) and not float(amount).is_integer() else f"{int(round(val)):,}"
    unit = sc.get("unit", "")
    nf, uf = gfx.font(250), gfx.font(110)
    col = COLORS.get(sc.get("color", "red"), RED)
    total = d.textlength(shown, font=nf) + 20 + d.textlength(unit, font=uf)
    x = W / 2 - total / 2
    y = top + 80
    d.text((x, y), shown, font=nf, fill=col)
    d.text((x + d.textlength(shown, font=nf) + 20, y + 120), unit, font=uf, fill=col)
    if sc.get("label"):
        draw_block(d, sc["label"], gfx.font(48), W - 300, W / 2, y + 300, INK, anchor="c")
    if sc.get("note"):
        nf2 = gfx.font(32, bold=False)
        d.text((W / 2 - d.textlength(sc["note"], font=nf2) / 2, SUB_TOP - 60), sc["note"], font=nf2, fill=MUTED)
    return im


def check_mark(d, cx, cy, r, on, col, mark="check"):
    if on:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
        if mark == "x":
            w, k = int(r * 0.26), r * 0.4
            d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=(255, 255, 255), width=w)
            d.line([(cx - k, cy + k), (cx + k, cy - k)], fill=(255, 255, 255), width=w)
        else:
            d.line([(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)], fill=(255, 255, 255), width=int(r * 0.28))
    else:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=LINE, width=5)


def draw_checklist(sc, ctx, t, reveal):
    im = frame_base(ctx)
    d = ImageDraw.Draw(im)
    top = heading(d, sc["heading"]) if sc.get("heading") else 170
    items = sc["items"]
    n = len(items)
    row = min(150, (SUB_TOP - 30 - top) / n)
    top = top + ((SUB_TOP - 30 - top) - row * n) / 2
    f = fit(d, [it["text"] for it in items], W - 760, 54, 36)
    for i, it in enumerate(items):
        y = top + i * row
        on = i < reveal
        shadow_card(im, (180, y, W - 180, y + row - 26), radius=24, fill=CARD if on else (250, 251, 253))
        d = ImageDraw.Draw(im)
        mid = y + (row - 26) / 2
        col = COLORS.get(it.get("color", "green"), GREEN)
        check_mark(d, 250, mid, 32, on, col, it.get("mark", "check"))
        draw_rich(d, (310, mid - f.size / 2 - 6), it["text"], f, INK if on else (180, 186, 198))
        if it.get("right"):
            rf = gfx.font(46)
            d.text((W - 220 - d.textlength(it["right"], font=rf), mid - rf.size / 2 - 6), it["right"], font=rf,
                   fill=COLORS.get(it.get("right_color", "red"), RED) if on else (200, 204, 212))
    return im


def draw_compare(sc, ctx, t, reveal):
    im = frame_base(ctx)
    d = ImageDraw.Draw(im)
    top = heading(d, sc["heading"]) if sc.get("heading") else 170
    cols = [sc["left"], sc["right"]]
    cw = (W - 160 - 60) / 2
    lf = gfx.font(58)
    body_h = max(sum(len(wrap(d, ln, lf, cw - 90)) * (lf.size + 10) + 26 for ln in c["lines"]) for c in cols)
    avail = SUB_TOP - 30 - top
    bh = min(max(110 + 60 + body_h + 40, 380), avail)
    top = top + (avail - bh) / 2
    for i, c in enumerate(cols):
        if i >= reveal:
            break
        x0 = 80 + i * (cw + 60)
        col = COLORS.get(c.get("color", "green" if i == 0 else "red"), NAVY)
        shadow_card(im, (x0, top, x0 + cw, top + bh))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([x0, top, x0 + cw, top + 110], radius=28, fill=col)
        d.rectangle([x0, top + 80, x0 + cw, top + 110], fill=col)
        hf = gfx.font(54)
        d.text((x0 + cw / 2 - d.textlength(c["title"], font=hf) / 2, top + 22), c["title"], font=hf, fill=(255, 255, 255))
        y = top + 110 + (bh - 110 - body_h) / 2
        for ln in c["lines"]:
            y = draw_block(d, ln, lf, cw - 90, x0 + cw / 2, y, INK, anchor="c", gap=10) + 26
    return im


def draw_timeline(sc, ctx, t, reveal):
    im = frame_base(ctx)
    d = ImageDraw.Draw(im)
    top = heading(d, sc["heading"]) if sc.get("heading") else 200
    pts = sc["points"]
    n = len(pts)
    ly = (top + SUB_TOP) / 2 - 40
    x0, x1 = (330, W - 330) if n > 2 else (520, W - 520)
    d.line([(x0, ly), (x1, ly)], fill=LINE, width=10)
    step = (x1 - x0) / max(n - 1, 1)
    for i, p in enumerate(pts):
        x = x0 + i * step if n > 1 else W / 2
        on = i < reveal
        col = COLORS.get(p.get("color", "navy"), NAVY) if on else (200, 204, 212)
        r = 34 if p.get("active") else 24
        d.ellipse([x - r, ly - r, x + r, ly + r], fill=col)
        if not on:
            continue
        df = gfx.font(60 if p.get("active") else 52)
        d.text((x - d.textlength(p["date"], font=df) / 2, ly - 130), p["date"], font=df, fill=col)
        draw_block(d, p["label"], gfx.font(42, bold=bool(p.get("active"))), min(step, 600) - 20, x, ly + 62, INK, anchor="c", gap=12)
    return im


def cover16(path, bright=0.55):
    im = Image.open(path).convert("RGB")
    scale = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * scale) + 1, int(im.height * scale) + 1), Image.LANCZOS)
    left, top = (im.width - W) // 2, (im.height - H) // 2
    return ImageEnhance.Brightness(im.crop((left, top, left + W, top + H))).enhance(bright)


def draw_photo(sc, ctx, t, img_path):
    if img_path:
        im = cover16(img_path)
    else:
        im = gfx.add_glow(gfx.vertical_gradient(W, H, gfx.BG_TOP, gfx.BG_BOTTOM), (W // 2, H // 2), 600, gfx.ACCENT, opacity=40)
    d = ImageDraw.Draw(im)
    lf = gfx.font(34)
    d.text((W - 48 - d.textlength(BRAND, font=lf), 30), BRAND, font=lf, fill=GOLD)
    lines = sc["caption"].split("\n")
    f = fit(d, lines, W - 260, 96, 56)
    p = ease(t / 0.4)
    y = H * 0.42 - (len(lines) * (f.size + 22)) / 2 + (1 - p) * 24
    for ln in lines:
        draw_rich(d, (W / 2, y), ln, f, (255, 255, 255), anchor="c", hi=GOLD, warn=(255, 110, 110), stroke=8, stroke_fill=(0, 0, 0))
        y += f.size + 22
    return im


def draw_quote(sc, ctx, t):
    im = frame_base(ctx)
    d = ImageDraw.Draw(im)
    top = heading(d, sc["heading"]) if sc.get("heading") else 200
    qf = gfx.font(54)
    n_lines = len(wrap(d, sc["text"], qf, W - 440 - 160))
    bh = 70 + n_lines * (qf.size + 18) + (100 if sc.get("cite") else 40)
    avail = SUB_TOP - 40 - top
    y0 = top + max((avail - bh) / 2, 0)
    box = (220, y0, W - 220, y0 + min(bh, avail))
    shadow_card(im, box, fill=(255, 252, 244))
    d = ImageDraw.Draw(im)
    d.rectangle([box[0], box[1] + 30, box[0] + 14, box[3] - 30], fill=GOLD)
    y = draw_block(d, sc["text"], qf, box[2] - box[0] - 160, box[0] + 80, box[1] + 60, INK, gap=18)
    if sc.get("cite"):
        cf_ = gfx.font(32, bold=False)
        d.text((box[2] - 60 - d.textlength(sc["cite"], font=cf_), box[3] - 80), sc["cite"], font=cf_, fill=MUTED)
    return im


def n_steps(sc):
    k = sc["kind"]
    if k == "cards":
        return len(sc["cards"])
    if k == "checklist":
        return len(sc["items"])
    if k == "compare":
        return 2
    if k == "timeline":
        return len(sc["points"])
    return 1


def draw(sc, ctx, t, reveal, img_path):
    k = sc["kind"]
    if k == "title":
        return draw_title(sc, ctx, t)
    if k == "cards":
        return draw_cards(sc, ctx, t, reveal)
    if k == "number":
        return draw_number(sc, ctx, t)
    if k == "checklist":
        return draw_checklist(sc, ctx, t, reveal)
    if k == "compare":
        return draw_compare(sc, ctx, t, reveal)
    if k == "timeline":
        return draw_timeline(sc, ctx, t, reveal)
    if k == "photo":
        return draw_photo(sc, ctx, t, img_path)
    return draw_quote(sc, ctx, t)


# ---------- 렌더 ----------
def run(cmd):
    v2.run(cmd)


def reveal_times(sc, dur):
    """단계형 장면(카드·체크리스트 등)은 장면 앞 70% 구간에 고르게 하나씩 드러낸다. "reveal_at"(초 목록)으로 직접 지정 가능."""
    n = n_steps(sc)
    if sc.get("reveal_at"):
        return [0.0] + [min(float(x), dur - 0.3) for x in sc["reveal_at"]][: n - 1]
    if n <= 1 or sc.get("reveal") == "all":
        return [0.0]
    span = dur * 0.7
    return [span * i / n for i in range(n)]


def render_scene(work, idx, sc, ctx, img_path, dur):
    """변화 시점마다 짧은 전환 프레임(0.35초, 숫자는 0.9초)을 만들고 나머지는 정지 화면으로 채운다."""
    events = reveal_times(sc, dur)
    if sc.get("reveal") == "all":
        events = [0.0]
    parts = []
    prev = Image.new("RGB", (W, H), BG if sc["kind"] not in ("title", "photo") else (8, 12, 20))
    sdir = os.path.join(work, f"s{idx:03d}")
    os.makedirs(sdir, exist_ok=True)
    for e_i, e in enumerate(events):
        nxt = events[e_i + 1] if e_i + 1 < len(events) else dur
        reveal = e_i + 1 if len(events) > 1 else n_steps(sc)
        anim = min(0.9 if sc["kind"] == "number" and e_i == 0 else 0.35, max(nxt - e, 1 / FPS))
        n_anim = max(int(anim * FPS), 1)
        target = draw(sc, ctx, 5.0, reveal, img_path)
        fdir = os.path.join(sdir, f"e{e_i}")
        os.makedirs(fdir, exist_ok=True)
        for k in range(n_anim):
            tt = k / FPS
            if sc["kind"] in ("number", "title", "photo") and e_i == 0:
                fr = draw(sc, ctx, tt, reveal, img_path)
                if sc["kind"] != "number":
                    fr = fade_in(prev, fr, tt / anim)
            else:
                fr = fade_in(prev, target, tt / anim)
            fr.save(os.path.join(fdir, f"{k:04d}.png"))
        a_mp4 = os.path.join(sdir, f"a{e_i}.mp4")
        run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(fdir, "%04d.png"), *ENC, a_mp4])
        parts.append(a_mp4)
        hold = nxt - e - n_anim / FPS
        if hold > 0.5 / FPS:
            png = os.path.join(sdir, f"h{e_i}.png")
            target.save(png)
            h_mp4 = os.path.join(sdir, f"h{e_i}.mp4")
            run(["ffmpeg", "-y", "-loop", "1", "-i", png, "-t", f"{hold:.3f}", *ENC, h_mp4])
            parts.append(h_mp4)
        prev = target
        shutil.rmtree(fdir, ignore_errors=True)
    lst = os.path.join(sdir, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{os.path.basename(p)}'\n")
    out = os.path.join(work, f"scene_{idx:03d}.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    return out, prev


def get_image(key, prompt, img_dir):
    p = os.path.join(img_dir, f"{key}.jpg")
    if os.path.exists(p):
        return p
    if not prompt:
        return None
    if "no text" not in prompt.lower():
        prompt += ", no text"
    for attempt in range(3):
        try:
            cf.generate(prompt, p, steps=4)
            return p
        except Exception as e:  # 이 장면만 그라데이션으로 대체
            print(f"  이미지 생성 실패 {key} (시도 {attempt + 1}/3): {str(e)[:120]}", flush=True)
            time.sleep(2)
    return None


def gen_art(prompt, out):
    """FLUX.2 klein(16:9 바로 생성, 장당 약 6초). 실패하면 None — 그 장면은 그라데이션으로 대체된다."""
    with open(cf.CRED_PATH, encoding="utf-8") as f:
        cred = json.load(f)
    b = uuid.uuid4().hex
    parts = [f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
             for k, v in (("prompt", ART_STYLE.format(p=prompt)), ("width", ART_W), ("height", ART_H))]
    parts.append(f"--{b}--\r\n".encode())
    url = f"https://api.cloudflare.com/client/v4/accounts/{cred['account_id']}/ai/run/{KLEIN}"
    req = urllib.request.Request(url, data=b"".join(parts), headers={
        "Authorization": "Bearer " + cred["api_token"], "Content-Type": f"multipart/form-data; boundary={b}"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r)
            with open(out, "wb") as f:
                f.write(base64.b64decode(data["result"]["image"]))
            return out
        except Exception as e:  # 한도·네트워크 — 이 장면만 대체
            print(f"  그림 생성 실패 (시도 {attempt + 1}/3): {str(e)[:160]}", flush=True)
            time.sleep(3)
    return None


def art_overlay(sc, title, en):
    """그림 위에 얹는 글자층(RGBA): 오른쪽 위 큰 제목 + 영어 부제, 왼쪽 큰 숫자, 왼쪽 위 로고."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([W * 0.42, 0, W, 230], fill=(0, 0, 0, 120))
    lay = Image.alpha_composite(lay, sh.filter(ImageFilter.GaussianBlur(60)))
    d = ImageDraw.Draw(lay)
    hi, warn = (255, 200, 60), (255, 84, 84)
    if title:
        f = fit(d, [title], W - 760, 92, 56)
        draw_rich(d, (W - 70, 56), title, f, (255, 255, 255), anchor="r", stroke=7, stroke_fill=(0, 0, 0), hi=hi, warn=warn)
        if en:
            ef = gfx.font(34, bold=False)
            d.text((W - 70 - d.textlength(en, font=ef), 66 + f.size + 14), en, font=ef, fill=(228, 228, 232),
                   stroke_width=2, stroke_fill=(0, 0, 0))
    if sc.get("big"):
        bf = fit(d, sc["big"].split("\n"), 760, 132, 70)
        y = 330
        for ln in sc["big"].split("\n"):
            draw_rich(d, (90, y), ln, bf, (255, 255, 255), stroke=9, stroke_fill=(0, 0, 0), hi=hi, warn=warn)
            y += bf.size + 20
    lf = gfx.font(32)
    d.rounded_rectangle([40, 36, 80 + d.textlength(BRAND, font=lf), 92], radius=28, fill=(10, 14, 22, 170), outline=GOLD + (255,), width=2)
    d.text((60, 42), BRAND, font=lf, fill=GOLD + (255,))
    return lay


def render_art(work, idx, sc, img_path, dur, title, en):
    """배경 그림은 ffmpeg zoompan으로 천천히 확대(짝수)·축소(홀수), 글자층은 0.4초 페이드인으로 위에 얹는다."""
    sdir = os.path.join(work, f"s{idx:03d}")
    os.makedirs(sdir, exist_ok=True)
    bg = os.path.join(sdir, "bg.png")
    if img_path:
        im = Image.open(img_path).convert("RGB").resize((W, H), Image.LANCZOS)
        im = ImageEnhance.Brightness(im).enhance(0.9)
    else:
        im = gfx.add_glow(gfx.vertical_gradient(W, H, gfx.BG_TOP, gfx.BG_BOTTOM), (W // 2, H // 2), 600, gfx.ACCENT, opacity=40)
    im.save(bg)
    ov = os.path.join(sdir, "ov.png")
    lay = art_overlay(sc, title, en)
    lay.save(ov)
    n = max(int(dur * FPS), 2)
    zoom = f"1+0.07*on/{n}" if idx % 2 == 0 else f"1.07-0.07*on/{n}"
    out = os.path.join(work, f"scene_{idx:03d}.mp4")
    flt = (f"[0:v]scale=3840:2160,zoompan=z='{zoom}':d={n}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS}[bg];"
           f"[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1[ov];[bg][ov]overlay=0:0:shortest=1,format=yuv420p[v]")
    run(["ffmpeg", "-y", "-i", bg, "-loop", "1", "-framerate", str(FPS), "-i", ov,
         "-filter_complex", flt, "-map", "[v]", "-frames:v", str(n), *ENC, out])
    final = Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")
    return out, final


def voice_style_path(name):
    """meta "voice_style"(M1·M3 등) → assets/voice_style_<이름>.json. 롱폼 목소리는 10/29 사용자가 M1로 골랐다(쇼츠는 M3 그대로)."""
    path = os.path.join(base.BASE_DIR, "assets", f"voice_style_{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"목소리 스타일 없음: {path} (vendor/supertonic_clone/supertonic3/voice_styles/에서 복사)")
    return path


def chapter_voice(ci, ch, work, rate, fresh, style="M3"):
    cdir = os.path.join(work, f"voice_ch{ci:02d}")
    os.makedirs(cdir, exist_ok=True)
    wav = os.path.join(cdir, "voice.wav")
    words_p = os.path.join(cdir, "words.json")
    text = " ".join(s["voice"].strip() for s in ch["scenes"])
    text_p = os.path.join(cdir, "source.txt")
    key = text + "|" + rate + "|" + style
    same = os.path.exists(text_p) and open(text_p, encoding="utf-8").read() == key
    if not fresh and same and os.path.exists(wav) and os.path.exists(words_p):
        with open(words_p, encoding="utf-8") as f:
            return wav, [tuple(w) for w in json.load(f)]
    prev = base.CLONED_VOICE_STYLE
    base.CLONED_VOICE_STYLE = voice_style_path(style)  # tts_cloned_voice가 이 상수를 읽는다
    try:
        words = base.tts_cloned_voice(text, cdir, wav, rate)
    finally:
        base.CLONED_VOICE_STYLE = prev
    with open(words_p, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False)
    with open(text_p, "w", encoding="utf-8") as f:
        f.write(key)
    return wav, words


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Malgun Gothic,56,&H0000E6FF,&H0000E6FF,&H20000000,&H20000000,-1,0,0,0,100,100,0,0,3,14,0,2,160,160,44,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def sentence_groups(words, max_chars=34, max_dur=4.5):
    """자막 묶음이 문장 끝(. ? !)을 넘어가지 않게 문장마다 따로 묶는다 — 넘어가면 다음 장면 문장이 앞 화면에 미리 뜬다."""
    groups, sent = [], []
    for w in words:
        sent.append(w)
        if w[2].rstrip().endswith((".", "?", "!")):
            groups += base.group_words(sent, max_chars, max_dur)
            sent = []
    if sent:
        groups += base.group_words(sent, max_chars, max_dur)
    return groups


def write_subs(words, path):
    groups = sentence_groups(words)
    with open(path, "w", encoding="utf-8") as f:
        f.write(ASS_HEADER)
        for g in groups:
            f.write(f"Dialogue: 0,{base.fmt_ts(g[0][0])},{base.fmt_ts(g[-1][1] + 0.05)},Sub,,0,0,0,,{' '.join(w for _, _, w in g)}\n")
    return len(groups)


def mix(voice, sr, scene_starts, chapter_starts, out):
    track = np.zeros(len(voice) + sr)
    track[:len(voice)] += voice

    def put(sig, t):
        i = int(t * sr)
        if 0 <= i < len(track):
            track[i:i + len(sig)] += sig[:len(track) - i]

    put(v2.impact(sr, amp=0.22), 0.0)
    for s in scene_starts[1:]:
        put(v2.whoosh(sr, amp=0.045), max(s - 0.05, 0))
    for s in chapter_starts[1:]:
        put(v2.ding(sr, amp=0.07), s + 0.05)
    peak = np.max(np.abs(track))
    if peak > 0.95:
        track *= 0.95 / peak
    sf.write(out, track[:len(voice)], sr)


THUMB_FONT = os.path.join(base.BASE_DIR, "assets", "fonts", "BlackHanSans-Regular.ttf")  # 경제해적단식 굵은 제목 글꼴(OFL, 10/29)


def tfont(size):
    from PIL import ImageFont
    return ImageFont.truetype(THUMB_FONT, size) if os.path.exists(THUMB_FONT) else gfx.font(size)


def tfit(d, text, max_w, start, min_size=40):
    size = start
    while size > min_size and d.textlength(plain(text), font=tfont(size)) > max_w:
        size -= 4
    return tfont(size)


def _rich_layer(size, xy, text, f, cols, stroke, stroke_fill):
    """마크업 글자를 투명 레이어에 그린다(그림자 흐림용)."""
    from PIL import ImageDraw as _D
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = _D.Draw(lay)
    x, y = xy
    for seg, col in segs_of(text, *cols):
        d.text((x, y), seg, font=f, fill=col, stroke_width=stroke, stroke_fill=stroke_fill)
        x += d.textlength(seg, font=f)
    return lay


def make_thumb_v3(meta, img_dir, out):
    """경제해적단 썸네일 분석(10/29, 상위 16 vs 하위 16) 반영.
    상위: 어둡고 진한 영화풍 그림이 '이야기'를 보여 주고(그림 속 숫자 팻말·라벨), 아래 1/3에 큰 글자 2줄
    (1줄 흰색 설정 → 2줄 더 크게 노랑/빨강 결론), 구체 숫자·vs·'이것', 채널 로고 없음, 날짜 등은 글자 위 작은 빨간 라벨.
    하위: 밝은 낮 배경 + 해적 마스코트(10월 이후) + 막연한 문구. 마스코트는 쓰지 않는다(사용자).
    품질(10/29 2차): Black Han Sans, 흐린 그림자+두꺼운 테두리, 색 보정·비네트·선명도, 팻말 그림자."""
    th = meta.get("thumbnail", {})
    tw, thh = 1280, 720
    p = th.get("image_path")
    if not p and th.get("art_prompt"):
        p = os.path.join(img_dir, "thumb_art_" + hashlib.md5(th["art_prompt"].encode("utf-8")).hexdigest()[:12] + ".png")
        if not os.path.exists(p):
            p = gen_art(th["art_prompt"], p)
    if not p:
        p = get_image("thumb", th.get("image_prompt"), img_dir)
    if p:
        im = Image.open(p).convert("RGB")
        s = max(tw / im.width, thh / im.height)
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
        im = im.crop(((im.width - tw) // 2, (im.height - thh) // 2, (im.width - tw) // 2 + tw, (im.height - thh) // 2 + thh))
        im = ImageEnhance.Brightness(im).enhance(th.get("brightness", 1.12))
        im = ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.3)).enhance(1.12)
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    else:
        im = gfx.vertical_gradient(tw, thh, gfx.BG_TOP, gfx.BG_BOTTOM)
    # 비네트(가장자리) + 글자 자리(아래쪽)만 짙게 — 전체를 어둡게 하지 않는다
    ys = np.arange(thh, dtype=np.float32)[:, None] / thh
    xs = np.arange(tw, dtype=np.float32)[None, :] / tw
    vig = np.clip(((xs - 0.5) ** 2 * 1.6 + (ys - 0.45) ** 2 * 1.2) * 1.1, 0, 0.45)
    bottom = np.clip((ys - 0.40) / 0.60, 0, 1) ** 1.3 * 0.92
    shade = np.clip(np.maximum(vig, bottom), 0, 0.95)
    im = Image.composite(Image.new("RGB", (tw, thh), (0, 0, 0)), im, Image.fromarray((shade * 255).astype(np.uint8)))
    im = im.convert("RGBA")
    cols = {"green": (34, 170, 84), "red": (225, 35, 35), "yellow": (245, 190, 0), "navy": (18, 36, 84), "dark": (16, 20, 30)}
    for t in th.get("tags", []):  # 그림 속 팻말(벤치마크의 환율 전광판·숫자 라벨 역할)
        tf = tfont(t.get("size", 52))
        tmp = ImageDraw.Draw(im)
        x, y = int(t["x"] * tw), int(t["y"] * thh)
        w = tmp.textlength(t["text"], font=tf) + 48
        h = tf.size + 30
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([x - w / 2 + 6, y + 8, x + w / 2 + 6, y + h + 8], radius=16, fill=(0, 0, 0, 200))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([x - w / 2, y, x + w / 2, y + h], radius=16, fill=cols.get(t.get("color", "red"), cols["red"]), outline=(255, 255, 255), width=5)
        d.text((x, y + h / 2 + 2), t["text"], font=tf, fill=(255, 255, 255), anchor="mm")
    d = ImageDraw.Draw(im)
    lines = th.get("lines", [meta.get("youtube_title", "")[:14]])
    scale = th.get("line_scale", [0.72, 1.0] if len(lines) == 2 else [1.0] * len(lines))
    fonts = [tfit(d, ln, tw - 96, int(176 * sc)) for ln, sc in zip(lines, scale)]
    gap = 4
    y = thh - 40 - sum(f.size + gap for f in fonts)
    if th.get("badge"):
        bf = tfont(46)
        bw = d.textlength(th["badge"], font=bf) + 44
        d.rounded_rectangle([46, y - 74, 46 + bw, y - 12], radius=8, fill=(226, 30, 30), outline=(255, 255, 255), width=3)
        d.text((46 + bw / 2, y - 43), th["badge"], font=bf, fill=(255, 255, 255), anchor="mm")
    hi, warn = th.get("hi", (255, 222, 0)), th.get("warn", (255, 56, 48))
    for ln, f in zip(lines, fonts):
        # 1) 넓게 흐린 검은 그림자(글자를 배경에서 띄움) 2) 두꺼운 검은 테두리 3) 본 글자
        sh = _rich_layer(im.size, (48 + 6, y + 9), ln, f, ((0, 0, 0, 255), (0, 0, 0, 255), (0, 0, 0, 255)), 22, (0, 0, 0, 255))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(9)))
        im = Image.alpha_composite(im, _rich_layer(im.size, (48, y), ln, f, ((255, 255, 255, 255), hi + (255,), warn + (255,)), 13, (0, 0, 0, 255)))
        y += f.size + gap
    d = ImageDraw.Draw(im)
    if th.get("logo"):
        lf = gfx.font(30)
        lw = d.textlength(BRAND, font=lf) + 36
        d.rounded_rectangle([tw - lw - 26, 26, tw - 26, 26 + 52], radius=26, fill=(10, 14, 22), outline=GOLD, width=3)
        d.text((tw - lw - 8, 33), BRAND, font=lf, fill=GOLD)
    im.convert("RGB").save(out)


def make_thumb(meta, img_dir, out):
    if str(meta.get("script_version", "")).startswith("v3"):
        return make_thumb_v3(meta, img_dir, out)
    th = meta.get("thumbnail", {})
    tw, thh = 1280, 720
    p = get_image("thumb", th.get("image_prompt"), img_dir)
    if p:
        im = Image.open(p).convert("RGB")
        s = max(tw / im.width, thh / im.height)
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
        im = ImageEnhance.Brightness(im.crop(((im.width - tw) // 2, (im.height - thh) // 2, (im.width - tw) // 2 + tw, (im.height - thh) // 2 + thh))).enhance(0.5)
    else:
        im = gfx.vertical_gradient(tw, thh, gfx.BG_TOP, gfx.BG_BOTTOM)
    d = ImageDraw.Draw(im)
    lines = th.get("lines", [meta.get("youtube_title", "")[:14]])
    f = fit(d, lines, tw - 90, 132, 70)
    y = thh - 70 - len(lines) * (f.size + 18)
    for ln in lines:
        draw_rich(d, (48, y), ln, f, (255, 255, 255), hi=(255, 214, 0), warn=(255, 70, 70), stroke=10, stroke_fill=(0, 0, 0))
        y += f.size + 18
    if th.get("badge"):
        bf = gfx.font(52)
        bw = d.textlength(th["badge"], font=bf) + 56
        d.rounded_rectangle([40, 36, 40 + bw, 36 + 86], radius=18, fill=(226, 36, 36))
        d.text((68, 46), th["badge"], font=bf, fill=(255, 255, 255))
    lf = gfx.font(34)
    lw = d.textlength(BRAND, font=lf) + 40
    d.rounded_rectangle([tw - lw - 30, 36, tw - 30, 36 + 58], radius=29, fill=(10, 14, 22), outline=GOLD, width=3)
    d.text((tw - lw - 10, 44), BRAND, font=lf, fill=GOLD)
    im.save(out)


def validate(meta):
    chs = meta.get("chapters") or []
    if len(chs) < 3:
        raise ValueError("chapters는 3개 이상(유튜브 챕터 조건)")
    for ci, ch in enumerate(chs):
        if not ch.get("title") or not ch.get("scenes"):
            raise ValueError(f"chapter {ci}: title/scenes 누락")
        for si, sc in enumerate(ch["scenes"]):
            where = f"chapter {ci} scene {si}"
            if sc.get("kind") not in KINDS:
                raise ValueError(f"{where}: kind는 {KINDS} 중 하나 ({sc.get('kind')})")
            if not str(sc.get("voice", "")).strip():
                raise ValueError(f"{where}: voice 누락")
            need = {"art": ["image_prompt"], "title": ["title"], "cards": ["cards"], "number": ["amount"], "checklist": ["items"],
                    "compare": ["left", "right"], "timeline": ["points"], "photo": ["caption"], "quote": ["text"]}[sc["kind"]]
            for k in need:
                if k not in sc:
                    raise ValueError(f"{where}: {k} 누락")


DISCLAIMER = ("⚠️ 유의사항\n이 영상은 정보 제공을 목적으로 하며 세무·법률 자문이 아닙니다. 세법과 제도는 바뀔 수 있고 개인 상황에 따라 "
              "적용이 달라지니, 실제 거래·신고 전에는 세무서·세무사·관할 시군구청에 꼭 확인하세요. 영상 속 금액은 이해를 돕기 위한 예시입니다.")
SIGNATURE = "도장은 천천히, 팩트는 먼저 🔴 도장찍기전에 — 부동산 세금, 아는 만큼 아낍니다"
BASE_HASHTAGS = ["#도장찍기전에", "#부동산", "#부동산세금", "#재테크"]


def build_upload(meta, out_dir):
    """벤치마크(경제해적단·머니클래스·집구석·부자의 경제학, 10/29 분석) 공통 형식으로 업로드 정보를 만든다.
    설명 순서: 훅 2~3줄 → 📌 다루는 내용 → ⏱ 타임라인(챕터) → [기준일] → 출처 → ⚠️ 유의사항 → 댓글 질문·구독 → 서명 → 해시태그 15~25개.
    태그 30~40개, 카테고리 27(교육), 한국어 지정, 공개는 평일 저녁 19~20시(벤치마크 업로드 시각 최빈값)."""
    up = meta.get("upload", {})
    chapters_p = os.path.join(out_dir, "chapters.txt")
    chapters = open(chapters_p, encoding="utf-8").read().strip() if os.path.exists(chapters_p) else ""
    v3 = str(meta.get("script_version", "")).startswith("v3")
    parts = [up.get("hook", "").strip()]
    if up.get("covers"):
        head = "" if v3 else "📌 이번 영상에서 다루는 내용\n"  # v3: 경제해적단처럼 머리말 없이 ▶ 목록 자체를 떡밥으로
        parts.append(head + "\n".join(f"▶ {c}" for c in up["covers"]))
    if chapters:
        parts.append("⏱ 타임라인\n" + chapters)
    if up.get("as_of"):
        parts.append(f"[{up['as_of']} 기준으로 제작된 영상입니다]")
    if up.get("sources"):
        parts.append("📚 출처\n" + "\n".join(f"· {x}" for x in up["sources"]))
    parts.append(DISCLAIMER)
    if up.get("comment_question"):
        parts.append(f"💬 {up['comment_question']}\n댓글로 남겨 주시면 하나하나 읽어 보겠습니다." if v3 else
                     f"💬 {up['comment_question']}\n댓글로 남겨 주시면 다음 영상 주제에 반영할게요.")
    parts.append("👍 도움이 되셨다면 좋아요, 🔔 구독과 알림 설정 부탁드려요.\n" + SIGNATURE)
    tags_h = list(dict.fromkeys(up.get("hashtags", []) + BASE_HASHTAGS))[:25]
    parts.append(" ".join(tags_h))
    if v3:  # 경제해적단 설명란: 덩어리 사이를 ━━━ 줄로 나눈다
        sep = "\n\n━━━\n\n"
        cq = [p for p in parts if p.startswith("💬")]
        groups = [parts[0], parts[1] if up.get("covers") else "", "⏱ 타임라인\n" + chapters if chapters else "",
                  "\n\n".join(p for p in parts if p.startswith(("[", "📚", "⚠️"))),
                  "\n\n".join(cq + [parts[-2]]), parts[-1]]
        desc = sep.join(g for g in groups if g)
    else:
        desc = "\n\n".join(x for x in parts if x)
    if len(desc) > 4900:  # 유튜브 설명 한도 5,000자
        desc = desc[:4900]
    tags = list(dict.fromkeys(up.get("tags", meta.get("tags", []))))
    while len(",".join(tags)) > 480 and tags:  # 유튜브 태그 합계 500자 한도
        tags.pop()
    info = {"title": up.get("title", meta.get("youtube_title", ""))[:100], "description": desc, "tags": tags,
            "category": "27", "language": "ko", "privacy": meta.get("privacy", "private"),
            "publish_slot": up.get("publish_slot", "평일 19:00~20:00 KST"), "thumbnail": os.path.join(out_dir, "thumb.png"),
            "synthetic": True}
    with open(os.path.join(out_dir, "upload.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "description.txt"), "w", encoding="utf-8") as f:
        f.write(info["title"] + "\n\n" + desc + "\n\n[태그] " + ", ".join(tags) + "\n")
    return info


def fmt_chapter(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--fresh-voice", action="store_true")
    ap.add_argument("--only-thumb", action="store_true")
    ap.add_argument("--only-upload-meta", action="store_true", help="렌더 없이 upload.json·description.txt만 다시 만든다(chapters.txt 필요)")
    args = ap.parse_args()
    with open(args.meta, encoding="utf-8") as f:
        meta = json.load(f)
    validate(meta)
    rate = meta.get("rate", "+10%")
    out_dir = args.out_dir
    work = os.path.join(out_dir, "_work")
    img_dir = os.path.join(work, "images")
    frames_dir = os.path.join(out_dir, "frames")
    for p in (work, img_dir, frames_dir):
        os.makedirs(p, exist_ok=True)
    if args.only_upload_meta:
        print(build_upload(meta, out_dir)["description"])
        return
    make_thumb(meta, img_dir, os.path.join(out_dir, "thumb.png"))
    if args.only_thumb:
        print("thumb only")
        return

    # 1) 장별 음성 → 이어 붙이기
    t0 = time.time()
    voices, all_words, chapter_starts, scene_spans = [], [], [], []
    cursor, sr = 0.0, None
    for ci, ch in enumerate(meta["chapters"]):
        wav, words = chapter_voice(ci, ch, work, rate, args.fresh_voice, meta.get("voice_style", "M3"))
        y, sr_ = sf.read(wav, dtype="float32")
        if y.ndim > 1:
            y = y.mean(axis=1)
        sr = sr or sr_
        counts = [len(s["voice"].strip().split(" ")) for s in ch["scenes"]]
        if sum(counts) != len(words):
            raise RuntimeError(f"chapter {ci} 음성 단어 수 불일치: 대본 {sum(counts)} vs 타이밍 {len(words)}")
        dur = len(y) / sr + CHAPTER_GAP
        chapter_starts.append(cursor)
        idx = 0
        starts = []
        for c in counts:
            starts.append(cursor + (words[idx][0] if idx else 0.0))
            idx += c
        ends = starts[1:] + [cursor + dur]
        scene_spans += list(zip(starts, ends))
        all_words += [(s + cursor, e + cursor, w) for s, e, w in words]
        voices.append(np.concatenate([y, np.zeros(int(CHAPTER_GAP * sr), dtype=np.float32)]))
        cursor += dur
    voice = np.concatenate(voices)
    total = len(voice) / sr
    print(f"voice {total:.1f}s ({time.time() - t0:.0f}s)", flush=True)

    # 2) 장면 렌더
    clips, report, k, used_imgs = [], [], 0, []
    for ci, ch in enumerate(meta["chapters"]):
        ctx = {"tag": ch.get("tag", ch["title"]), "source": ch.get("source", "")}
        cur_title, cur_en = ch.get("art_title", ""), ch.get("art_en", "")
        for si, sc in enumerate(ch["scenes"]):
            s, e = scene_spans[k]
            if sc["kind"] == "art":
                if "title" in sc:  # 제목은 바뀔 때만 적고, 없으면 앞 장면 제목을 이어받는다
                    cur_title, cur_en = sc["title"], sc.get("en", "")
                p = os.path.join(img_dir, "art_" + hashlib.md5(sc["image_prompt"].encode("utf-8")).hexdigest()[:12] + ".png")  # 문구 기준 캐시(장면 순서가 바뀌어도 그림 유지)
                img = p if os.path.exists(p) else gen_art(sc["image_prompt"], p)
                if img:
                    used_imgs.append(img)
                elif used_imgs:  # 그날 한도(429) 등으로 실패하면 앞에서 쓴 그림을 돌려 쓴다(빈 배경보다 낫다)
                    img = used_imgs[-(1 + k % min(len(used_imgs), 7))]
                    print(f"  앞 그림 재사용: {os.path.basename(img)}", flush=True)
                clip, final = render_art(work, k, sc, img, max(e - s, 0.4), cur_title, cur_en)
                final.save(os.path.join(frames_dir, f"{k:03d}_art.png"))
                clips.append(clip)
                report.append({"i": k, "chapter": ci, "kind": "art", "start": round(s, 2), "end": round(e, 2), "image": bool(img)})
                print(f"scene {k:>3} ch{ci} art       {s:6.1f}-{e:6.1f}s", flush=True)
                k += 1
                continue
            img = get_image(f"c{ci:02d}s{si:02d}", sc.get("image_prompt"), img_dir) if sc["kind"] == "photo" else None
            sctx = {**ctx, "source": sc.get("source", ctx["source"])}
            clip, final = render_scene(work, k, sc, sctx, img, max(e - s, 0.4))
            final.save(os.path.join(frames_dir, f"{k:03d}_{sc['kind']}.png"))
            clips.append(clip)
            report.append({"i": k, "chapter": ci, "kind": sc["kind"], "start": round(s, 2), "end": round(e, 2),
                           "image": bool(img) if sc["kind"] == "photo" else None})
            print(f"scene {k:>3} ch{ci} {sc['kind']:<9} {s:6.1f}-{e:6.1f}s", flush=True)
            k += 1

    lst = os.path.join(work, "concat.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{os.path.basename(c)}'\n")
    video = os.path.join(work, "video_only.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", video])

    # 3) 소리·자막 합치기
    mixed = os.path.join(work, "mixed.wav")
    mix(voice, sr, [s for s, _ in scene_spans], chapter_starts, mixed)
    ass = os.path.join(work, "subs.ass")
    n_subs = write_subs(all_words, ass)
    ass_esc = ass.replace("\\", "/").replace(":", "\\:")
    out = os.path.join(out_dir, "long.mp4")
    run(["ffmpeg", "-y", "-i", video, "-i", mixed, "-vf", f"ass='{ass_esc}'", "-map", "0:v", "-map", "1:a",
         *ENC, "-c:a", "aac", "-b:a", "192k", "-shortest", out])

    chapters = "\n".join(f"{fmt_chapter(s)} {ch['title']}" for s, ch in zip(chapter_starts, meta["chapters"]))
    with open(os.path.join(out_dir, "chapters.txt"), "w", encoding="utf-8") as f:
        f.write(chapters + "\n")
    with open(os.path.join(out_dir, "long_report.json"), "w", encoding="utf-8") as f:
        json.dump({"duration": round(total, 2), "chars": sum(len(s["voice"]) for ch in meta["chapters"] for s in ch["scenes"]),
                   "subtitles": n_subs, "chapters": chapters.split("\n"), "scenes": report}, f, ensure_ascii=False, indent=1)
    build_upload(meta, out_dir)
    print(f"done: {out} ({base.get_duration(out):.1f}s, {time.time() - t0:.0f}s)\n{chapters}", flush=True)


if __name__ == "__main__":
    main()
