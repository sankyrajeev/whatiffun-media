"""Code-drawn props for thai-cave (free): an air tank and a smiling stick-figure head."""
from PIL import Image, ImageDraw
S = 4
def tank():
    W, H = 300 * S, 900 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lw = 12 * S
    d.rounded_rectangle((40*S, 170*S, 260*S, 880*S), radius=105*S, fill=(232, 182, 52, 255), outline=(25, 20, 15, 255), width=lw)
    d.rounded_rectangle((80*S, 260*S, 115*S, 800*S), radius=16*S, fill=(250, 226, 150, 255))
    for y in (330, 700):
        d.rectangle((48*S, y*S, 252*S, (y+40)*S), fill=(40, 34, 28, 255))
    d.rectangle((120*S, 90*S, 180*S, 180*S), fill=(150, 150, 150, 255), outline=(25, 20, 15, 255), width=lw)
    d.rounded_rectangle((70*S, 40*S, 230*S, 100*S), radius=20*S, fill=(110, 110, 110, 255), outline=(25, 20, 15, 255), width=lw)
    return im.resize((W // S, H // S), Image.LANCZOS)
def head():
    W = 400 * S
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((30*S, 30*S, 370*S, 370*S), fill=(246, 240, 228, 255), outline=(20, 16, 12, 255), width=16*S)
    for x in (140, 260): d.ellipse(((x-20)*S, 140*S, (x+20)*S, 190*S), fill=(20, 16, 12, 255))
    d.arc((110*S, 150*S, 290*S, 300*S), 20, 160, fill=(20, 16, 12, 255), width=16*S)
    return im.resize((W // S, W // S), Image.LANCZOS)
tank().save("art/raw/air-tank.png"); head().save("art/raw/smiley-head.png")
