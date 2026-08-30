import argparse
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

W, H = 1080, 1920
BG_TOP = (15, 27, 46)      # 짙은 네이비 (밝은 쪽)
BG_BOTTOM = (6, 10, 18)    # 짙은 네이비 (어두운 쪽)
ACCENT = (242, 193, 78)    # 골드
ACCENT_DIM = (120, 96, 40)
WHITE = (247, 248, 250)
GRAY = (146, 156, 172)

FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
FONT_REG = "C:/Windows/Fonts/malgun.ttf"


def font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def vertical_gradient(w, h, top, bottom):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        d.line(
            [(0, y), (w, y)],
            fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
        )
    return img


def add_glow(img, center, radius, color=ACCENT, opacity=90):
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=color + (opacity,),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius // 2))
    base = img.convert("RGBA")
    return Image.alpha_composite(base, glow).convert("RGB")


def base_canvas(glow_center=(W // 2, H // 2 - 200), glow_radius=420):
    img = vertical_gradient(W, H, BG_TOP, BG_BOTTOM)
    img = add_glow(img, glow_center, glow_radius, ACCENT, opacity=55)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 14, H], fill=ACCENT)
    d.line([(W - 100, 90), (W - 40, 90)], fill=ACCENT_DIM, width=4)
    d.line([(W - 40, 90), (W - 40, 150)], fill=ACCENT_DIM, width=4)
    return img, d


def kicker(d, text, x=64, y=90):
    f = font(38)
    tw = d.textlength(text, font=f)
    pad_x, pad_y = 26, 14
    box = [x, y, x + tw + pad_x * 2, y + f.size + pad_y * 2]
    d.rounded_rectangle(box, radius=30, outline=ACCENT, width=3)
    d.text((x + pad_x, y + pad_y - 4), text, font=f, fill=ACCENT)


def watermark(d):
    f = font(30, bold=False)
    text = "daily.factlab"
    tw = d.textlength(text, font=f)
    d.text((W - tw - 50, H - 80), text, font=f, fill=(90, 98, 112))


def make_logo_badge(out="logo.png", text="daily.factlab"):
    """우측 상단 고정용 반투명 로고 배지 (알파 채널 포함 PNG)."""
    pad_x, pad_y = 30, 18
    f = font(42)
    tmp = Image.new("RGBA", (10, 10))
    d0 = ImageDraw.Draw(tmp)
    tw = d0.textlength(text, font=f)
    w, h = int(tw + pad_x * 2), int(f.size + pad_y * 2)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(10, 14, 22, 185), outline=ACCENT + (255,), width=3)
    d.text((pad_x, pad_y - 4), text, font=f, fill=ACCENT + (255,))
    img.save(out)
    return w, h


def wrap_draw(draw, text, f, max_width, y, fill, center_x=W // 2, line_gap=14, align="center"):
    lines, cur = [], ""
    for ch in text:
        test = cur + ch
        if draw.textlength(test, font=f) > max_width and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    for line in lines:
        w = draw.textlength(line, font=f)
        x = center_x - w / 2 if align == "center" else center_x - max_width / 2
        draw.text((x, y), line, font=f, fill=fill)
        y += f.size + line_gap
    return y


def title_card(text, subtitle=None, kicker_text=None, out="out.png"):
    img, d = base_canvas()
    if kicker_text:
        kicker(d, kicker_text)
    y = H // 2 - 180
    y = wrap_draw(d, text, font(96), 880, y, WHITE)
    if subtitle:
        y += 34
        wrap_draw(d, subtitle, font(48, bold=False), 800, y, ACCENT)
    watermark(d)
    img.save(out)


def stat_card(number, label, sub=None, kicker_text=None, out="out.png"):
    img, d = base_canvas(glow_center=(W // 2, H // 2 - 260), glow_radius=460)
    if kicker_text:
        kicker(d, kicker_text)
    size = 260
    f_num = font(size)
    while d.textlength(number, font=f_num) > 960 and size > 80:
        size -= 10
        f_num = font(size)
    w = d.textlength(number, font=f_num)
    d.text((W / 2 - w / 2 + 4, H // 2 - 280 + 4), number, font=f_num, fill=ACCENT_DIM)
    d.text((W / 2 - w / 2, H // 2 - 280), number, font=f_num, fill=ACCENT)
    y = H // 2 + 60
    d.line([(W / 2 - 60, y - 30), (W / 2 + 60, y - 30)], fill=ACCENT, width=4)
    y = wrap_draw(d, label, font(66), 860, y, WHITE)
    if sub:
        y += 20
        wrap_draw(d, sub, font(40, bold=False), 800, y, GRAY)
    watermark(d)
    img.save(out)


def compare_card(title, left_label, left_text, right_label, right_text, kicker_text=None, out="out.png"):
    img, d = base_canvas(glow_center=(W // 2, 480), glow_radius=380)
    if kicker_text:
        kicker(d, kicker_text)
    y = 240
    y = wrap_draw(d, title, font(66), 900, y, WHITE)

    mid_y = 760
    card_pad = 50
    left_box = [card_pad, mid_y, W // 2 - 30, H - 260]
    d.rounded_rectangle(left_box, radius=28, fill=(20, 32, 52))
    right_box = [W // 2 + 30, mid_y, W - card_pad, H - 260]
    d.rounded_rectangle(right_box, radius=28, fill=(24, 36, 26), outline=ACCENT, width=3)

    lw = d.textlength(left_label, font=font(46))
    d.text(((left_box[0] + left_box[2]) / 2 - lw / 2, mid_y + 50), left_label, font=font(46), fill=GRAY)
    wrap_draw(d, left_text, font(52), 380, mid_y + 130, WHITE, center_x=(left_box[0] + left_box[2]) / 2)

    rw = d.textlength(right_label, font=font(46))
    d.text(((right_box[0] + right_box[2]) / 2 - rw / 2, mid_y + 50), right_label, font=font(46), fill=ACCENT)
    wrap_draw(d, right_text, font(52), 380, mid_y + 130, WHITE, center_x=(right_box[0] + right_box[2]) / 2)

    ay = mid_y + 100
    d.line([(left_box[2] - 10, ay), (right_box[0] + 10, ay)], fill=ACCENT, width=6)
    d.polygon(
        [(right_box[0] + 10, ay - 16), (right_box[0] + 10, ay + 16), (right_box[0] + 40, ay)],
        fill=ACCENT,
    )
    watermark(d)
    img.save(out)


def checklist_card(title, items, kicker_text=None, out="out.png"):
    img, d = base_canvas(glow_center=(W // 2, 420), glow_radius=380)
    if kicker_text:
        kicker(d, kicker_text)
    y = 240
    y = wrap_draw(d, title, font(70), 900, y, WHITE)
    y += 70
    f_item = font(50, bold=False)
    for item in items:
        r = 26
        cy = y + f_item.size / 2 - 6
        d.ellipse([80 - r, cy - r, 80 + r, cy + r], fill=(24, 36, 26), outline=ACCENT, width=3)
        d.line([(80 - 10, cy + 2), (80 - 2, cy + 12), (80 + 14, cy - 12)], fill=ACCENT, width=5)
        y = wrap_draw(d, item, f_item, 760, y, WHITE, center_x=W // 2 + 60, align="left")
        y += 46
    watermark(d)
    img.save(out)


def cta_card(main_text, sub_text, button_text="+ 팔로우", kicker_text=None, out="out.png"):
    img, d = base_canvas(glow_center=(W // 2, H // 2 - 100), glow_radius=460)
    if kicker_text:
        kicker(d, kicker_text)
    y = H // 2 - 260
    y = wrap_draw(d, main_text, font(76), 860, y, WHITE)
    y += 36
    y = wrap_draw(d, sub_text, font(46, bold=False), 800, y, ACCENT)
    btn_w, btn_h = 380, 116
    bx = W // 2 - btn_w // 2
    by = y + 80
    d.rounded_rectangle([bx, by, bx + btn_w, by + btn_h], radius=btn_h // 2, fill=ACCENT)
    f_btn = font(50)
    tw = d.textlength(button_text, font=f_btn)
    d.text((W / 2 - tw / 2, by + btn_h / 2 - f_btn.size / 2 - 6), button_text, font=f_btn, fill=(18, 18, 22))
    watermark(d)
    img.save(out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("title")
    p1.add_argument("--text", required=True)
    p1.add_argument("--subtitle", default=None)
    p1.add_argument("--kicker", default=None)
    p1.add_argument("--out", required=True)

    p2 = sub.add_parser("stat")
    p2.add_argument("--number", required=True)
    p2.add_argument("--label", required=True)
    p2.add_argument("--sub", default=None)
    p2.add_argument("--kicker", default=None)
    p2.add_argument("--out", required=True)

    p3 = sub.add_parser("compare")
    p3.add_argument("--title", required=True)
    p3.add_argument("--left-label", required=True)
    p3.add_argument("--left-text", required=True)
    p3.add_argument("--right-label", required=True)
    p3.add_argument("--right-text", required=True)
    p3.add_argument("--kicker", default=None)
    p3.add_argument("--out", required=True)

    p4 = sub.add_parser("checklist")
    p4.add_argument("--title", required=True)
    p4.add_argument("--items", required=True, help="세미콜론(;)으로 구분")
    p4.add_argument("--kicker", default=None)
    p4.add_argument("--out", required=True)

    p5 = sub.add_parser("cta")
    p5.add_argument("--main-text", required=True)
    p5.add_argument("--sub-text", required=True)
    p5.add_argument("--button-text", default="+ 팔로우")
    p5.add_argument("--kicker", default=None)
    p5.add_argument("--out", required=True)

    p6 = sub.add_parser("logo")
    p6.add_argument("--text", default="daily.factlab")
    p6.add_argument("--out", required=True)

    args = ap.parse_args()
    if args.cmd == "title":
        title_card(args.text, args.subtitle, args.kicker, args.out)
    elif args.cmd == "stat":
        stat_card(args.number, args.label, args.sub, args.kicker, args.out)
    elif args.cmd == "compare":
        compare_card(args.title, args.left_label, args.left_text, args.right_label, args.right_text, args.kicker, args.out)
    elif args.cmd == "checklist":
        checklist_card(args.title, args.items.split(";"), args.kicker, args.out)
    elif args.cmd == "cta":
        cta_card(args.main_text, args.sub_text, args.button_text, args.kicker, args.out)
    elif args.cmd == "logo":
        make_logo_badge(args.out, args.text)
    print(f"saved: {args.out}")


if __name__ == "__main__":
    main()
