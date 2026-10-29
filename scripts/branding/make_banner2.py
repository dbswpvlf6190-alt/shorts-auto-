import os, sys
sys.argv=['x']
exec(open('make_profiles5.py',encoding='utf-8').read().split('fns = [')[0])
from PIL import ImageEnhance
W,H=2560,1440
src=os.path.expanduser(r"~\ShortsAutoRender\longform\02_올해끝나는세금혜택3가지_롱\_work\images\art_38b545d7ae30.png")
bg=Image.open(src).convert("RGB"); s=max(W/bg.width,H/bg.height)
bg=bg.resize((int(bg.width*s)+1,int(bg.height*s)+1),Image.LANCZOS); bg=bg.crop(((bg.width-W)//2,(bg.height-H)//2,(bg.width-W)//2+W,(bg.height-H)//2+H))
im=ImageEnhance.Brightness(bg).enhance(0.5).convert("RGBA")
sh=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([W/2-880,H/2-260,W/2+880,H/2+260],radius=80,fill=(0,0,0,150)); im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(70)))
sx0,sy0=(W-1546)//2,(H-423)//2
disc=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(disc).ellipse([sx0+20,sy0+36,sx0+370,sy0+386],fill=CREAM+(255,)); im.alpha_composite(disc)
im.alpha_composite(round_seal(350,["도장"]),(sx0+20,sy0+36))
d=ImageDraw.Draw(im); tx=sx0+430
d.text((tx+8,sy0+30+10),"도장찍기전에",font=F(178),fill=(0,0,0))
d.text((tx,sy0+30),"도장찍기전에",font=F(178),fill=(255,255,255),stroke_width=5,stroke_fill=(0,0,0))
x=tx
for seg,col in (("부동산 세금, ",(255,255,255)),("아는 만큼 아낍니다",(255,214,0))):
    d.text((x,sy0+250),seg,font=F(78),fill=col,stroke_width=4,stroke_fill=(0,0,0)); x+=d.textlength(seg,font=F(78))
d.text((tx+4,sy0+352),"양도세 · 종부세 · 취득세 · 대출 · 청약   |   매일 쇼츠 · 매주 롱폼",font=ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf",36),fill=(230,230,230))
im.convert("RGB").save(os.path.join(OUT,"banner.png"))
pv=im.convert("RGB").resize((1280,720)); ImageDraw.Draw(pv).rectangle([sx0/2,sy0/2,(sx0+1546)/2,(sy0+423)/2],outline=(0,255,0),width=2); pv.save(os.path.join(OUT,"_banner_preview.png"))
print('ok')
