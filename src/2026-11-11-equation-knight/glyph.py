import numpy as np, sys
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
def contours(ch, path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
    f = TTFont(path); cmap = f.getBestCmap(); gs = f.getGlyphSet()
    name = cmap.get(ord(ch)); 
    if name is None: return None
    p = RecordingPen(); gs[name].draw(p)
    cs, cur, start = [], [], None
    def q(p0, p1, p2, n=12):
        t = np.linspace(0, 1, n)[1:, None]; return (1-t)**2*p0 + 2*(1-t)*t*p1 + t*t*p2
    for op, args in p.value:
        if op == "moveTo": cur = [np.array(args[0], float)]
        elif op == "lineTo": cur.append(np.array(args[0], float))
        elif op == "qCurveTo":
            pts = [np.array(a, float) for a in args]; p0 = cur[-1]
            # implied on-curve points
            for i in range(len(pts) - 1):
                c = pts[i]; e = pts[i+1] if i == len(pts) - 2 else (pts[i] + pts[i+1]) / 2
                cur.extend(q(p0, c, e)); p0 = e
        elif op == "curveTo":
            p0 = cur[-1]; c1, c2, e = [np.array(a, float) for a in args]
            t = np.linspace(0, 1, 16)[1:, None]
            cur.extend((1-t)**3*p0 + 3*(1-t)**2*t*c1 + 3*(1-t)*t*t*c2 + t**3*e)
        elif op in ("closePath", "endPath"):
            cs.append(np.array(cur)); cur = []
    return cs
if __name__ == "__main__":
    for ch in sys.argv[1]:
        cs = contours(ch)
        if cs is None: print(ch, "missing"); continue
        areas = [abs(np.sum(c[:,0]*np.roll(c[:,1],-1) - np.roll(c[:,0],-1)*c[:,1]))/2 for c in cs]
        print(ch, len(cs), [int(a) for a in areas])
