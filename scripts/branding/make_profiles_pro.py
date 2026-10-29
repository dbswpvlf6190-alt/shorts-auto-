"""도장찍기전에 — 프리미엄 프로필 5종. 높이맵(heightmap) 조명으로 입체감(엠보싱·왁스·금속)을 만든다."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = r"C:\shorts_auto\assets\branding"
BHS = r"C:\shorts_auto\assets\fonts\BlackHanSans-Regular.ttf"
S = 1600
rng = np.random.default_rng(11)


def F(size):
    return ImageFont.truetype(BHS, size)


def L(mask):
    return np.array(mask).astype(np.float32) / 255


def _box(a, k, axis):
    if k < 1:
        return a
    pad = [(0, 0), (0, 0)]
    pad[axis] = (k + 1, k)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, range(2 * k + 1, 2 * k + 1 + n), axis=axis)
    lo = np.take(c, range(0, n), axis=axis)
    return ((hi - lo) / (2 * k + 1)).astype(np.float32)


def blur(a, r):
    """실수 정밀도 가우시안 근사(상자 흐림 3번). 8비트로 흐리면 입체 표면에 계단 줄무늬가 생긴다."""
    a = np.clip(a, 0, 1).astype(np.float32)
    k = max(0, int(round(np.sqrt(12 * r * r / 3 + 1) / 2 - 0.5))) if r > 0 else 0
    for _ in range(3):
        a = _box(_box(a, k, 0), k, 1)
    return a


def shade(h, light=(-0.55, -0.65, 0.52), strength=6.0):
    """높이맵 → (난반사, 정반사) 조명값."""
    gy, gx = np.gradient(h * strength)
    n = np.dstack([-gx, -gy, np.ones_like(h)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    l = np.array(light, np.float32)
    l /= np.linalg.norm(l)
    diff = np.clip((n * l).sum(2), 0, 1)
    hvec = l + np.array([0, 0, 1], np.float32)
    hvec /= np.linalg.norm(hvec)
    spec = np.clip((n * hvec).sum(2), 0, 1) ** 40
    return diff, spec


def rgba(rgb, alpha):
    a = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha, 0, 1)[..., None] * 255]).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def text_mask(lines, box_w, box_h, cx=S / 2, cy=S / 2, lh=1.0, size=S):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    fs = int(box_h / len(lines) / lh)
    while fs > 20:
        f = F(fs)
        if max(d.textlength(t, font=f) for t in lines) <= box_w:
            break
        fs -= 6
    y = cy - fs * lh * len(lines) / 2 + fs * lh / 2
    for t in lines:
        d.text((cx, y), t, font=f, fill=255, anchor="mm")
        y += fs * lh
    return m


def ring_mask(r_out, width, cx=S / 2, cy=S / 2):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([cx - r_out, cy - r_out, cx + r_out, cy + r_out], outline=255, width=width)
    return m


def disc(r, cx=S / 2, cy=S / 2, fill=255):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)
    return m


def radial_bg(c_in, c_out, cx=0.42, cy=0.38, power=1.3):
    ys, xs = np.mgrid[0:S, 0:S].astype(np.float32) / S
    t = np.clip(np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / 0.85, 0, 1) ** power
    return np.array(c_in, np.float32) * (1 - t[..., None]) + np.array(c_out, np.float32) * t[..., None]


def drop_shadow(alpha, off=(18, 30), r=34, k=0.55):
    a = np.roll(np.roll(alpha, off[1], 0), off[0], 1)
    return blur(a, r) * k


def compose(bg_rgb, layers):
    out = Image.fromarray(np.clip(bg_rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    for lay in layers:
        out.alpha_composite(lay)
    return out


# ---------------- 1. 왁스 실링 도장 (붉은 밀랍에 '도장'이 눌린 모양) ----------------
def wax():
    ys, xs = np.mgrid[0:S, 0:S].astype(np.float32)
    ang = np.arctan2(ys - S / 2, xs - S / 2)
    wob = sum(np.sin(ang * k + rng.random() * 6.28) * a for k, a in ((3, 14), (5, 10), (7, 8), (11, 6), (17, 4)))
    rr = np.sqrt((xs - S / 2) ** 2 + (ys - S / 2) ** 2)
    blob = (rr < 640 + wob).astype(np.float32)
    dome = blur(blob, 60) * blob
    plate = (rr < 470).astype(np.float32)
    press = blur(plate, 6) * 0.35  # 도장판이 눌린 오목한 면
    design = L(text_mask(["도장"], 560, 360)) + L(ring_mask(420, 26))
    h = dome * 1.0 - press + blur(np.clip(design, 0, 1), 3) * 0.22 * plate
    diff, spec = shade(blur(h, 2), strength=90)
    base = np.array((150, 8, 18), np.float32)
    rgb = base * (0.35 + 0.9 * diff[..., None]) + 255 * spec[..., None] * 0.85
    a = blur(blob, 1.2)
    bg = radial_bg((40, 44, 56), (8, 9, 14))
    return compose(bg, [rgba(np.zeros((S, S, 3)), drop_shadow(a, (20, 34), 40, 0.7)), rgba(rgb, a)])


# ---------------- 2. 앱 아이콘형 빨강 엠블럼 (흰 글자가 튀어나온 입체) ----------------
def app_red():
    bg = radial_bg((236, 52, 52), (120, 6, 16), 0.35, 0.28, 1.1)
    tm = L(text_mask(["도장", "찍기전에"], 980, 900, cy=S / 2 + 10, lh=1.02))
    # 두 번째 줄을 작게: 다시 그린다
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    d.text((S / 2, S / 2 - 120), "도장", font=F(600), fill=255, anchor="mm")
    d.text((S / 2, S / 2 + 330), "찍기전에", font=F(230), fill=255, anchor="mm")
    tm = L(m)
    h = blur(tm, 7)
    diff, spec = shade(h, strength=60)
    white = np.array((255, 255, 255), np.float32)
    rgb = white * (0.78 + 0.25 * diff[..., None]) + 60 * spec[..., None]
    # 둘째 줄은 금색으로
    gold_zone = np.zeros((S, S), np.float32)
    gold_zone[S // 2 + 200:, :] = 1
    gold = np.array((255, 214, 90), np.float32) * (0.75 + 0.35 * diff[..., None]) + 80 * spec[..., None]
    rgb = rgb * (1 - gold_zone[..., None]) + gold * gold_zone[..., None]
    ring = L(ring_mask(700, 30))
    rh = blur(ring, 4)
    rdiff, rspec = shade(rh, strength=40)
    ring_rgb = np.array((255, 236, 236), np.float32) * (0.7 + 0.35 * rdiff[..., None]) + 90 * rspec[..., None]
    gloss = np.zeros((S, S), np.float32)
    ys = np.arange(S, dtype=np.float32)[:, None] / S
    gloss += np.clip(0.42 - ys, 0, 1) * 0.35 * L(disc(760))
    return compose(bg, [
        rgba(np.zeros((S, S, 3)), drop_shadow(tm, (16, 26), 26, 0.55)),
        rgba(ring_rgb, ring),
        rgba(rgb, blur(tm, 0.8)),
        rgba(np.full((S, S, 3), 255.0), gloss),
    ])


# ---------------- 3. 블랙 & 골드 금속 엠블럼 ----------------
def gold_emblem():
    bg = radial_bg((38, 34, 30), (6, 6, 8), 0.5, 0.42, 1.2)
    design = np.clip(L(ring_mask(690, 40)) + L(ring_mask(600, 12)) + L(text_mask(["도장"], 760, 470)), 0, 1)
    h = blur(design, 9)
    diff, spec = shade(h, strength=70)
    t = np.clip(0.15 + 0.95 * diff, 0, 1)
    ramp_x = np.array([0, 0.35, 0.65, 0.85, 1.0])
    ramp = np.array([(70, 42, 12), (150, 104, 40), (222, 182, 96), (250, 226, 160), (255, 250, 230)], np.float32)
    rgb = np.dstack([np.interp(t, ramp_x, ramp[:, c]) for c in range(3)]) + 255 * spec[..., None] * 0.6
    # 가운데 빨간 원판(인주색)
    plate = L(disc(585))
    pd, ps = shade(blur(plate, 30), strength=25)
    prgb = np.array((160, 14, 24), np.float32) * (0.55 + 0.6 * pd[..., None]) + 120 * ps[..., None]
    return compose(bg, [
        rgba(prgb, plate * (1 - design)),
        rgba(np.zeros((S, S, 3)), drop_shadow(design, (10, 16), 14, 0.6)),
        rgba(rgb, blur(design, 0.8)),
    ])


# ---------------- 4. 실사풍 도장 찍힌 계약서 (종이 질감 + 진한 인주) ----------------
def contract():
    bg = radial_bg((34, 52, 92), (8, 12, 24), 0.4, 0.3, 1.2)
    paper_m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(paper_m).rounded_rectangle([300, 190, 1300, 1430], radius=36, fill=255)
    paper_m = paper_m.rotate(-6, resample=Image.BICUBIC, center=(S / 2, S / 2))
    pa = L(paper_m)
    noise = rng.normal(0, 4, (S, S, 1)).astype(np.float32)
    ys = np.arange(S, dtype=np.float32)[:, None, None] / S
    prgb = np.array((250, 247, 238), np.float32) - ys * 18 + noise
    lines = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(lines)
    d.rounded_rectangle([410, 300, 900, 380], radius=18, fill=255)
    for k in range(8):
        y = 470 + k * 92
        d.rounded_rectangle([410, y, 1190 - (220 if k % 3 == 2 else 0), y + 30], radius=15, fill=150)
    lines = L(lines.rotate(-6, resample=Image.BICUBIC, center=(S / 2, S / 2)))
    prgb = prgb * (1 - lines[..., None] * 0.55) + np.array((24, 34, 64), np.float32) * lines[..., None] * 0.55
    seal = np.clip(L(ring_mask(300, 30, 1010, 1080)) + L(ring_mask(255, 10, 1010, 1080)) + L(text_mask(["도장"], 330, 210, 1010, 1088)), 0, 1)
    seal = L(Image.fromarray((seal * 255).astype(np.uint8)).rotate(-16, resample=Image.BICUBIC, center=(1010, 1080)))
    sp = blur(rng.random((S, S)).astype(np.float32), 2.5)
    sa = seal * np.clip(0.82 + (sp - 0.5) * 0.8, 0.75, 1) * pa
    srgb = np.full((S, S, 3), (196, 14, 28), np.float32)
    return compose(bg, [
        rgba(np.zeros((S, S, 3)), drop_shadow(pa, (22, 36), 46, 0.75)),
        rgba(prgb, pa),
        rgba(srgb, blur(sa, 0.9)),
    ])


# ---------------- 5. 네온 레드 (다크 + 빛나는 도장, 젊고 강한 느낌) ----------------
def neon():
    bg = radial_bg((26, 16, 22), (4, 4, 8), 0.5, 0.5, 1.0)
    design = np.clip(L(ring_mask(640, 34)) + L(text_mask(["도장"], 720, 440)), 0, 1)
    glow1 = blur(design, 40) * 1.3
    glow2 = blur(design, 12) * 1.1
    col = np.array((255, 40, 60), np.float32)
    core = np.array((255, 225, 225), np.float32)
    layers = [rgba(np.broadcast_to(col, (S, S, 3)).copy(), np.clip(glow1, 0, 0.85)),
              rgba(np.broadcast_to(col, (S, S, 3)).copy(), np.clip(glow2, 0, 1)),
              rgba(np.broadcast_to(core, (S, S, 3)).copy(), blur(design, 1.5) * 0.95)]
    sub = L(text_mask(["찍기전에"], 520, 130, cy=S / 2 + 470))
    layers += [rgba(np.broadcast_to(np.array((255, 210, 80), np.float32), (S, S, 3)).copy(), np.clip(blur(sub, 14) * 1.0, 0, 0.7)),
               rgba(np.broadcast_to(np.array((255, 240, 200), np.float32), (S, S, 3)).copy(), blur(sub, 1))]
    return compose(bg, layers)


fns = [("A_왁스실링", wax), ("B_레드앱아이콘", app_red), ("C_블랙골드", gold_emblem), ("D_계약서실사", contract), ("E_네온레드", neon)]
imgs = []
for name, fn in fns:
    im = fn().convert("RGB").resize((800, 800), Image.LANCZOS)
    im.save(os.path.join(OUT, f"pro_{name}.png"))
    imgs.append((name, im))
    print(name, flush=True)

pv = Image.new("RGB", (5 * 300 + 20, 520), (255, 255, 255))
pd = ImageDraw.Draw(pv)
lf = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)


def circ(im, sz):
    c = im.resize((sz, sz), Image.LANCZOS)
    m = Image.new("L", (sz * 4, sz * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, sz * 4 - 1, sz * 4 - 1], fill=255)
    return c, m.resize((sz, sz), Image.LANCZOS)


for k, (name, im) in enumerate(imgs):
    x = 20 + k * 300
    for sz, xy in ((260, (x, 20)), (120, (x + 10, 300)), (48, (x + 160, 336))):
        c, m = circ(im, sz)
        pv.paste(c, xy, m)
    pd.text((x + 130, 470), name.replace("_", ". ", 1), font=lf, fill=(30, 30, 30), anchor="mm")
pv.save(os.path.join(OUT, "_pro5_preview.png"))
print("ok")
