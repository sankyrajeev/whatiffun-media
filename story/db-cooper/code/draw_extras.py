"""Code-drawn cut-outs (free): a $20 bill and a parachute, in the cartoon ink style."""
from PIL import Image, ImageDraw, ImageFont
import math, sys
out = sys.argv[1]
S = 4
# $20 bill
W, H = 520*S, 230*S
im = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(im)
d.rounded_rectangle([8*S, 8*S, W-8*S, H-8*S], 18*S, fill=(150,170,120,255), outline=(25,22,18,255), width=9*S)
d.rounded_rectangle([34*S, 32*S, W-34*S, H-32*S], 12*S, outline=(70,95,60,255), width=5*S)
d.ellipse([W/2-70*S, H/2-78*S, W/2+70*S, H/2+78*S], fill=(205,210,175,255), outline=(25,22,18,255), width=6*S)
d.ellipse([W/2-34*S, H/2-48*S, W/2+34*S, H/2+18*S], fill=(110,130,90,255))
d.pieslice([W/2-56*S, H/2+6*S, W/2+56*S, H/2+110*S], 180, 360, fill=(110,130,90,255))
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64*S)
for x, y in [(50, 40), (W/S-140, H/S-120)]:
    d.text((x*S, y*S), "20", font=f, fill=(40,60,35,255))
# a few stains (rotting)
for (x, y, r) in [(120, 170, 26), (420, 60, 20), (380, 180, 14)]:
    d.ellipse([(x-r)*S, (y-r)*S, (x+r)*S, (y+r)*S], fill=(120,110,60,140))
im.resize((W//S, H//S), Image.LANCZOS).save(f"{out}/bill-20.png")
# parachute
W, H = 600*S, 640*S
im = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(im)
cx, top, r = W/2, 40*S, 270*S
cols = [(214,200,170), (190,120,60), (214,200,170), (190,120,60), (214,200,170), (190,120,60)]
n = 6
for i in range(n):
    a0, a1 = 180 + i*180/n, 180 + (i+1)*180/n
    d.pieslice([cx-r, top, cx+r, top+2*r], a0, a1, fill=cols[i]+(255,), outline=(25,22,18,255), width=8*S)
d.rectangle([cx-r-10*S, top+r, cx+r+10*S, top+r+40*S], fill=(0,0,0,0))
# lines to pack
px, py = cx, 560*S
for i in range(n+1):
    a = math.radians(180 + i*180/n)
    x = cx + r*math.cos(a); y = top + r + r*math.sin(a)*0 
    d.line([(x, top+r), (px, py)], fill=(30,26,22,255), width=5*S)
d.rounded_rectangle([px-50*S, py-10*S, px+50*S, py+70*S], 14*S, fill=(85,90,55,255), outline=(25,22,18,255), width=8*S)
im.resize((W//S, H//S), Image.LANCZOS).save(f"{out}/parachute.png")
