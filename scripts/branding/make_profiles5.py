"""도장찍기전에 — 프로필 사진 5종(800x800, 원형으로 잘려 보임)."""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = r"C:\shorts_auto\assets\branding"
os.makedirs(OUT, exist_ok=True)
BHS = r"C:\shorts_auto\assets\fonts\BlackHanSans-Regular.ttf"
RED = (200, 16, 30)
CREAM = (247, 240, 226)
NAVY = (13, 19, 33)
GOLD = (212, 175, 90)
S = 1600  # 2배로 그리고 줄인다(가장자리 매끈)


def F(size):
    return ImageFont.truetype(BHS, size)


def paper(w, h, base=CREAM, amp=5):
    n = np.random.default_rng(1).normal(0, amp, (h, w, 1)).astype(np.float32)
    arr = np.clip(np.array(base, np.float32)[None, None, :] + n, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB").filter(ImageFilter.GaussianBlur(0.7)).convert("RGBA")


def ink_layer(mask, color=RED, seed=3):
    """진한 인주: 거의 꽉 찬 색 + 아주 옅은 빠짐 자국 + 살짝 번진 가장자리."""
    m = np.array(mask.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    rng = np.random.default_rng(seed)
    speck = Image.fromarray((rng.random(m.shape) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5))
    sp = np.array(speck).astype(np.float32) / 255
    m = m * np.clip(0.80 + (sp - 0.5) * 0.9, 0.78, 1.0)
    lay = Image.new("RGBA", mask.size, color + (0,))
    lay.putalpha(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)))
    return lay


def text_block(d, cx, cy, lines, max_w, max_h, fill=255, lh=1.0):
    fs = int(max_h / len(lines) / lh)
    while fs > 20:
        f = F(fs)
        if max(d.textlength(t, font=f) for t in lines) <= max_w:
            break
        fs -= 6
    total = fs * lh * len(lines)
    y = cy - total / 2 + fs * lh / 2
    for t in lines:
        d.text((cx, y), t, font=f, fill=fill, anchor="mm")
        y += fs * lh


def round_seal(diam, lines, double=True, rot=-8):
    mask = Image.new("L", (diam, diam), 0)
    d = ImageDraw.Draw(mask)
    w = int(diam * 0.06)
    d.ellipse([w // 2, w // 2, diam - w // 2, diam - w // 2], outline=255, width=w)
    if double:
        g = int(diam * 0.1)
        d.ellipse([g, g, diam - g, diam - g], outline=255, width=max(4, w // 3))
    inner = diam * (0.58 if double else 0.66)
    text_block(d, diam / 2, diam / 2 + diam * 0.01, lines, inner, inner * (0.62 if len(lines) == 1 else 0.95))
    return ink_layer(mask).rotate(rot, resample=Image.BICUBIC)


def square_seal(side, lines, rot=-5):
    mask = Image.new("L", (side, side), 0)
    d = ImageDraw.Draw(mask)
    w = int(side * 0.07)
    d.rounded_rectangle([w // 2, w // 2, side - w // 2, side - w // 2], radius=int(side * 0.07), outline=255, width=w)
    text_block(d, side / 2, side / 2, lines, side * 0.72, side * 0.78, lh=1.0)
    return ink_layer(mask, seed=5).rotate(rot, resample=Image.BICUBIC)


def shadow(im, box, radius, blur=30, alpha=150, ellipse=False, off=(14, 22)):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    b = [x0 + off[0], y0 + off[1], x1 + off[0], y1 + off[1]]
    dr = ImageDraw.Draw(sh)
    (dr.ellipse if ellipse else (lambda bb, fill: dr.rounded_rectangle(bb, radius=radius, fill=fill)))(b, fill=(0, 0, 0, alpha))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))


def p1():  # 1. 클래식 인감: 크림 한지 + 이중 테두리 원형 도장 '도장'
    im = paper(S, S)
    im.alpha_composite(round_seal(1340, ["도장"]), (130, 130))
    return im


def p2():  # 2. 전통 사각 인감(낙관) '도장/찍기/전에'
    im = paper(S, S)
    im.alpha_composite(square_seal(1180, ["도장", "찍기", "전에"]), (210, 210))
    return im


def p3():  # 3. 계약서 + 도장: 남색 배경, 기울어진 흰 계약서, 오른쪽 아래 빨간 도장
    im = Image.new("RGBA", (S, S), NAVY + (255,))
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([200, 200, 1400, 1400], fill=(60, 90, 160, 90))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    doc = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(doc)
    box = [330, 220, 1270, 1380]
    dd.rounded_rectangle(box, radius=40, fill=(252, 250, 244, 255))
    dd.rounded_rectangle([430, 320, 900, 400], radius=20, fill=(30, 40, 70, 255))  # 제목 막대
    for k in range(7):
        y = 480 + k * 95
        dd.rounded_rectangle([430, y, 1170 - (180 if k % 3 == 2 else 0), y + 34], radius=17, fill=(205, 208, 216, 255))
    doc = doc.rotate(-7, resample=Image.BICUBIC, center=(800, 800))
    shadow(im, (330, 220, 1270, 1380), 40, blur=40, alpha=170)
    im.alpha_composite(doc)
    im.alpha_composite(round_seal(620, ["도장"], rot=-14), (820, 820))
    return im


def p4():  # 4. 빨간 바탕 모던: 흰 글자 '도장' 크게 + '찍기전에', 흰 원 테두리
    im = Image.new("RGBA", (S, S), (210, 22, 32, 255))
    g = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([-300, -400, 1300, 1000], fill=(255, 90, 80, 90))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(220)))
    d = ImageDraw.Draw(im)
    d.ellipse([150, 150, 1450, 1450], outline=(255, 255, 255, 255), width=34)
    f1, f2 = F(560), F(210)
    d.text((806, 700), "도장", font=f1, fill=(120, 0, 10, 255), anchor="mm")
    d.text((800, 690), "도장", font=f1, fill=(255, 255, 255, 255), anchor="mm")
    d.text((800, 1080), "찍기전에", font=f2, fill=(255, 226, 120, 255), anchor="mm")
    return im


def p5():  # 5. 프리미엄: 검정 바탕 + 금색 바깥 고리 + 빨간 이중 원형 도장(믿음직한 느낌)
    im = Image.new("RGBA", (S, S), (12, 12, 14, 255))
    g = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([250, 250, 1350, 1350], fill=(120, 20, 25, 140))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(170)))
    d = ImageDraw.Draw(im)
    d.ellipse([90, 90, 1510, 1510], outline=GOLD + (255,), width=26)
    d.ellipse([150, 150, 1450, 1450], fill=CREAM + (255,))
    im.alpha_composite(round_seal(1180, ["도장"], rot=-6), (210, 210))
    return im


fns = [("1_클래식인감", p1), ("2_사각인감", p2), ("3_계약서도장", p3), ("4_빨강모던", p4), ("5_프리미엄", p5)]
imgs = []
for name, fn in fns:
    im = fn().convert("RGB").resize((800, 800), Image.LANCZOS)
    im.save(os.path.join(OUT, f"profile_{name}.png"))
    imgs.append((name, im))

# 실제 보이는 모양(원형) 미리보기: 큰 원 + 채널 페이지 크기(160) + 댓글 크기(48)
W = 5 * 300 + 20
pv = Image.new("RGB", (W, 520), (255, 255, 255))
pd = ImageDraw.Draw(pv)
lf = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 26)


def circ(im, sz):
    c = im.resize((sz, sz), Image.LANCZOS)
    m = Image.new("L", (sz * 4, sz * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, sz * 4 - 1, sz * 4 - 1], fill=255)
    return c, m.resize((sz, sz), Image.LANCZOS)


for k, (name, im) in enumerate(imgs):
    x = 20 + k * 300
    c, m = circ(im, 260)
    pv.paste(c, (x, 20), m)
    c, m = circ(im, 120)
    pv.paste(c, (x + 10, 300), m)
    c, m = circ(im, 48)
    pv.paste(c, (x + 160, 336), m)
    pd.text((x + 130, 470), name.replace("_", ". ", 1), font=lf, fill=(30, 30, 30), anchor="mm")
pv.save(os.path.join(OUT, "_profiles5_preview.png"))
print("ok")
