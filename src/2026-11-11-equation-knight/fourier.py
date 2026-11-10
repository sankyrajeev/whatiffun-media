import numpy as np
from glyph import contours
M = 4096
def outline(ch="♞"):
    cs = contours(ch); c = max(cs, key=lambda c: abs(np.sum(c[:,0]*np.roll(c[:,1],-1) - np.roll(c[:,0],-1)*c[:,1])))
    # dedupe, resample by arc length
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(np.vstack([c, c[:1]]), axis=0).T))]
    cc = np.vstack([c, c[:1]]); s = np.linspace(0, d[-1], M, endpoint=False)
    x = np.interp(s, d, cc[:, 0]); y = np.interp(s, d, cc[:, 1])
    z = x + 1j * y
    # orient counter-clockwise, centre, normalise height to 1
    if np.sum(x*np.roll(y,-1) - np.roll(x,-1)*y) < 0: z = z[::-1]
    z = z - (z.real.min() + z.real.max()) / 2 - 1j * (z.imag.min() + z.imag.max()) / 2
    z = z / (z.imag.max() - z.imag.min())
    return z
def coeffs(z):
    C = np.fft.fft(z) / len(z); k = np.fft.fftfreq(len(z), 1 / len(z)).astype(int)
    order = np.argsort(-np.abs(C)); order = order[k[order] != 0]   # DC is the hub
    return C[0], C[order], k[order]
if __name__ == "__main__":
    from PIL import Image, ImageDraw
    z = outline(); c0, C, K = coeffs(z)
    t = np.linspace(0, 2*np.pi, 4096, endpoint=False)
    ims = []
    for N in [1, 4, 16, 64, 256, 1024]:
        p = c0 + (C[:N, None] * np.exp(1j * K[:N, None] * t)).sum(0)
        im = Image.new("RGB", (400, 400), (20, 16, 12)); dr = ImageDraw.Draw(im)
        q = [(200 + 330 * v.real, 200 - 330 * v.imag) for v in p]
        dr.line(q + q[:1], fill=(240, 190, 90), width=2); dr.text((10, 10), str(N), fill=(255,255,255)); ims.append(im)
    big = Image.new("RGB", (1200, 800)); [big.paste(im, (400*(i%3), 400*(i//3))) for i, im in enumerate(ims)]
    big.save("prev.png"); print(np.abs(C[:8]), K[:12], z.real.min(), z.real.max())
