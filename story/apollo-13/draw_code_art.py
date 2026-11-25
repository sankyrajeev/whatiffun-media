"""Free code-drawn props for apollo-13: moon.png, earth.png, splashdown.png (ink-outline cartoon look)."""
from PIL import Image, ImageDraw
import math, random
INK=(28,22,18,255); S=4
def canvas(w,h): return Image.new("RGBA",(w*S,h*S),(0,0,0,0))
def fin(im,name,w,h): im.resize((w,h),Image.LANCZOS).save(f"art/raw/{name}.png")
def circ(d,cx,cy,r,fill,ow=7):
    d.ellipse([(cx-r)*S,(cy-r)*S,(cx+r)*S,(cy+r)*S],fill=fill,outline=INK,width=ow*S)
# moon
im=canvas(800,800); d=ImageDraw.Draw(im)
circ(d,400,400,370,(214,205,186,255),9)
random.seed(3)
for cx,cy,r in [(270,280,70),(500,230,45),(520,470,95),(300,540,55),(420,360,30),(200,420,35),(610,330,28),(420,640,40)]:
    circ(d,cx,cy,r,(178,168,150,255),5); d.arc([(cx-r+10)*S,(cy-r+10)*S,(cx+r-6)*S,(cy+r-6)*S],200,330,fill=(238,232,218,255),width=5*S)
fin(im,"moon",800,800)
# earth
im=canvas(600,600); d=ImageDraw.Draw(im)
circ(d,300,300,270,(84,140,186,255),9)
for pts in [[(170,140),(260,110),(300,170),(250,240),(280,300),(210,330),(160,260),(130,190)],
            [(350,300),(440,280),(480,350),(430,440),(360,470),(330,400)],[(330,90),(400,100),(390,140),(340,130)]]:
    d.polygon([(x*S,y*S) for x,y in pts],fill=(132,168,98,255),outline=INK,width=5*S)
d.arc([90*S,90*S,480*S,480*S],200,260,fill=(236,230,212,255),width=10*S)
fin(im,"earth",600,600)
# splashdown: capsule under 3 parachutes, sea splash
W,H=700,1000; im=canvas(W,H); d=ImageDraw.Draw(im)
cx=350; top=560; base=780
for i,(px,col) in enumerate([(170,(236,228,210,255)),(350,(206,92,60,255)),(530,(236,228,210,255))]):
    py=170 if i==1 else 220; r=150
    d.pieslice([(px-r)*S,(py-r*0.8)*S,(px+r)*S,(py+r*0.8)*S],180,360,fill=col,outline=INK,width=7*S)
    for k in (1,2,3):
        x=px-r+k*r/2; yy=py-r*0.8*math.sqrt(max(0,1-((x-px)/r)**2))
        d.line([x*S,yy*S,x*S,py*S],fill=INK,width=3*S)
    for k in range(5):
        x=px-r+k*r/2; d.line([x*S,py*S,cx*S,(top-20)*S],fill=INK,width=3*S)
cap=[(cx-45,top),(cx+45,top),(cx+150,base),(cx-150,base)]
d.polygon([(x*S,y*S) for x,y in cap],fill=(220,214,200,255),outline=INK,width=8*S)
d.rectangle([(cx-20)*S,(top-25)*S,(cx+20)*S,top*S],fill=(180,170,150,255),outline=INK,width=6*S)
circ(d,cx-50,top+110,20,(60,80,100,255),6); circ(d,cx+50,top+110,20,(60,80,100,255),6)
sea=[(40,base-30)]
for k in range(13): sea.append((40+k*52,base-30+(14 if k%2 else -6)))
sea+= [(660,base-30),(660,960),(40,960)]
d.polygon([(x*S,y*S) for x,y in sea],fill=(84,140,186,255),outline=INK,width=7*S)
for sx,sy,r in [(170,base-55,34),(530,base-55,34),(110,base-100,20),(590,base-95,20),(210,base-120,14),(490,base-120,14)]:
    circ(d,sx,sy,r,(236,232,220,255),5)
for y in (860,910):
    d.arc([120*S,(y-10)*S,260*S,(y+10)*S],0,180,fill=(236,232,220,255),width=5*S)
    d.arc([420*S,(y-10)*S,560*S,(y+10)*S],0,180,fill=(236,232,220,255),width=5*S)
fin(im,"splashdown",W,H)
