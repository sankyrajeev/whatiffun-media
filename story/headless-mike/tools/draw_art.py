"""Code-drawn props for headless-mike (free): a 25-cent coin and an old glass syringe."""
from PIL import Image, ImageDraw, ImageFont
S = 4
INK = (25, 20, 15, 255)
def coin():
    W = 500 * S
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((20*S, 20*S, 480*S, 480*S), fill=(196, 196, 190, 255), outline=INK, width=14*S)
    d.ellipse((70*S, 70*S, 430*S, 430*S), outline=(150, 150, 144, 255), width=8*S)
    d.arc((90*S, 90*S, 300*S, 300*S), 200, 280, fill=(245, 245, 240, 255), width=14*S)
    f = ImageFont.truetype("/home/claude/whatiffun-media/fonts/InstrumentSerif-Regular.ttf", 230*S)
    d.text((250*S, 255*S), "25¢", font=f, fill=INK, anchor="mm")
    return im.resize((W // S, W // S), Image.LANCZOS)
def syringe():
    W, H = 1000 * S, 300 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lw = 12 * S
    d.rectangle((60*S, 130*S, 200*S, 170*S), fill=(150, 150, 150, 255), outline=INK, width=lw)   # plunger rod
    d.rounded_rectangle((20*S, 70*S, 70*S, 230*S), radius=12*S, fill=(150, 150, 150, 255), outline=INK, width=lw)
    d.rounded_rectangle((200*S, 90*S, 720*S, 210*S), radius=20*S, fill=(214, 232, 236, 255), outline=INK, width=lw)
    d.rectangle((215*S, 140*S, 520*S, 195*S), fill=(240, 230, 200, 255))
    for x in range(300, 700, 60): d.line((x*S, 92*S, x*S, 130*S), fill=INK, width=6*S)
    d.rectangle((720*S, 125*S, 790*S, 175*S), fill=(190, 190, 190, 255), outline=INK, width=lw)
    d.line((790*S, 150*S, 980*S, 150*S), fill=INK, width=10*S)
    return im.resize((W // S, H // S), Image.LANCZOS)
coin().save("art/raw/coin-25c.png"); syringe().save("art/raw/glass-syringe.png")
