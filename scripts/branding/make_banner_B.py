"""도장찍기전에 배너(2560x1440) — 프로필 B(레드 앱 아이콘)와 같은 디자인. 안전 영역(가운데 1546x423)에 모두 넣는다."""
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

OUT = r"C:\shorts_auto\assets\branding"
BHS = r"C:\shorts_auto\assets\fonts\BlackHanSans-Regular.ttf"
MALGUN = r"C:\Windows\Fonts\malgunbd.ttf"
W, H = 2560, 1440
SX, SY = (W - 1546) // 2, (H - 423) // 2


def F(s, p=BHS):
    return ImageFont.truetype(p, s)


src = os.path.expanduser(r"~\ShortsAutoRender\longform\02_올해끝나는세금혜택3가지_롱\_work\images\art_38b545d7ae30.png")
bg = Image.open(src).convert("RGB")
s = max(W / bg.width, H / bg.height)
bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1), Image.LANCZOS)
bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
im = ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(1.15)).enhance(0.42).convert("RGBA")
# 붉은 빛 번짐(채널 색) + 글자 뒤 어둡게
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([SX - 260, SY - 260, SX + 700, SY + 700], fill=(220, 30, 40, 120))
im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle([SX + 360, SY - 20, SX + 1620, SY + 440], radius=80, fill=(0, 0, 0, 140))
im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(70)))
# 프로필 B 엠블럼(원형) + 그림자
emb = Image.open(os.path.join(OUT, "pro_B_레드앱아이콘.png")).convert("RGBA").resize((400, 400), Image.LANCZOS)
m = Image.new("L", (1600, 1600), 0)
ImageDraw.Draw(m).ellipse([0, 0, 1599, 1599], fill=255)
emb.putalpha(m.resize((400, 400), Image.LANCZOS))
esh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(esh).ellipse([SX + 14, SY + 30, SX + 414, SY + 430], fill=(0, 0, 0, 200))
im.alpha_composite(esh.filter(ImageFilter.GaussianBlur(24)))
im.alpha_composite(emb, (SX, SY + 12))
d = ImageDraw.Draw(im)
tx = SX + 450
tf = F(176)
sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sl).text((tx + 8, SY + 20 + 12), "도장찍기전에", font=tf, fill=(0, 0, 0, 230))
im.alpha_composite(sl.filter(ImageFilter.GaussianBlur(8)))
d = ImageDraw.Draw(im)
d.text((tx, SY + 20), "도장찍기전에", font=tf, fill=(255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0))
x = tx
sf = F(80)
for seg, col in (("부동산 세금, ", (255, 255, 255)), ("아는 만큼 아낍니다", (255, 214, 90))):
    d.text((x, SY + 240), seg, font=sf, fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
    x += d.textlength(seg, font=sf)
pf = F(40, MALGUN)
px = tx + 2
for tag in ("양도세", "종부세", "취득세", "대출", "청약"):
    w = d.textlength(tag, font=pf) + 40
    d.rounded_rectangle([px, SY + 350, px + w, SY + 404], radius=27, fill=(200, 20, 30), outline=(255, 255, 255), width=2)
    d.text((px + w / 2, SY + 377), tag, font=pf, fill=(255, 255, 255), anchor="mm")
    px += w + 14
im.convert("RGB").save(os.path.join(OUT, "banner_B.png"), quality=95)
pv = im.convert("RGB").resize((1280, 720))
ImageDraw.Draw(pv).rectangle([SX / 2, SY / 2, (SX + 1546) / 2, (SY + 423) / 2], outline=(0, 255, 0), width=2)
pv.save(os.path.join(OUT, "_banner_B_preview.png"))
print("ok", px)
