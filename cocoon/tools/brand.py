"""AstraLabs tokens and drawing helpers shared by the Cocoon theme renders.

The dot field, the Sea idle and the scope beam are ports of the astralabs.dev home page, scaled up 1.5x
for handheld screens (a 1080p panel at 4 to 7 inches is much denser than a desktop monitor).
"""
import io
import math
from pathlib import Path

import cairo
import cairosvg
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / 'astralabs'
BRANDING = ROOT / 'branding'
FONT = Path(__file__).resolve().parent / 'fonts' / 'MartianMono[wdth,wght].ttf'

VOID = (0x0A, 0x09, 0x09)
PLATE = (0x13, 0x12, 0x12)
RULE = (0x2C, 0x2A, 0x29)
BONE = (0xED, 0xE6, 0xE1)
ASH = (0x8E, 0x83, 0x80)
ACID = (0xB6, 0xFF, 0x2E)

S = 1.5                    # handheld scale
SPACING = 21               # 14px grid x 1.5
EDGE = 36                  # corner inset, 24px x 1.5
REG = 27                   # plus mark size, 18px x 1.5


def rgb01(c):
    return tuple(v / 255 for v in c)


# ---------------------------------------------------------------- dot field

class DotField:
    """The 14px dot grid (21px here). Each dot is a 2.25px square on a pixel center, drawn with an exact
    coverage kernel, so a frame is a few numpy slices rather than thousands of draw calls."""

    # wavelength (px at 1x), direction (deg), weight. Speeds come from the loop length so the video loops.
    WAVES = [(620, 18, .34), (430, 112, .26), (300, 205, .2), (760, 290, .2)]

    def __init__(self, w, h, loop=48.0, cycles=(1, 1, 2, 1), center=None):
        self.w, self.h = w, h
        self.x0 = (w % SPACING) // 2 + SPACING // 2
        self.y0 = (h % SPACING) // 2 + SPACING // 2
        xs = np.arange(self.x0, w, SPACING, dtype=np.float64)
        ys = np.arange(self.y0, h, SPACING, dtype=np.float64)
        self.gx, self.gy = np.meshgrid(xs, ys)
        cx, cy = center or (w / 2, h / 2)
        far = max(math.hypot(cx, cy), math.hypot(w - cx, cy), math.hypot(cx, h - cy), math.hypot(w - cx, h - cy))
        self.rest = .12 + np.maximum(0, 1 - np.hypot(self.gx - cx, self.gy - cy) / far) * .2
        self.phase = []
        for i, (l, deg, a) in enumerate(self.WAVES):
            k = 2 * math.pi / (l * S)
            th = math.radians(deg)
            self.phase.append((self.gx * math.cos(th) * k + self.gy * math.sin(th) * k + i * 1.7, a))
        self.omega = [2 * math.pi * n / loop for n in cycles]
        k1 = np.array([.625, 1, .625])
        self.kernel = np.outer(k1, k1)

    def alpha(self, t, amp=.14):
        h = sum(a * np.sin(ph - t * om) for (ph, a), om in zip(self.phase, self.omega))
        return np.maximum(.04, self.rest + h * amp)

    def coverage(self, t, amp=.14):
        """Per-pixel bone coverage (0..1) for time t."""
        a = self.alpha(t, amp)
        img = np.zeros((self.h, self.w), np.float32)
        ny, nx = a.shape
        for dy in range(3):
            for dx in range(3):
                ys, xs = self.y0 - 1 + dy, self.x0 - 1 + dx
                sl = img[ys:ys + ny * SPACING:SPACING, xs:xs + nx * SPACING:SPACING]
                sl += (a * self.kernel[dy, dx])[:sl.shape[0], :sl.shape[1]]
        return np.clip(img, 0, 1)


def compose(base_cov, layers=()):
    """Void background, bone dots by coverage, then premultiplied RGBA layers (from cairo) on top."""
    out = np.empty((*base_cov.shape, 3), np.float32)
    for i in range(3):
        out[..., i] = VOID[i] + (BONE[i] - VOID[i]) * base_cov
    for layer in layers:
        a = layer[..., 3:4] / 255
        out = layer[..., :3] + out * (1 - a)
    return np.clip(out + .5, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- cairo layers

def surface(w, h):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    return s, cairo.Context(s)


def to_rgba(s):
    """Cairo ARGB32 (premultiplied BGRA in memory) to a premultiplied RGBA float array."""
    buf = np.ndarray((s.get_height(), s.get_stride() // 4, 4), np.uint8, s.get_data())[:, :s.get_width()]
    return buf[..., [2, 1, 0, 3]].astype(np.float32)


def plus_marks(ctx, w, h, corners=('tl', 'br')):
    """The registration plus marks in Acid, as on the home page."""
    ctx.set_source_rgb(*rgb01(ACID))
    lw = 1.5
    for c in corners:
        x = EDGE if 'l' in c else w - EDGE - REG
        y = EDGE if 't' in c else h - EDGE - REG
        ctx.rectangle(x + REG / 2 - lw / 2, y, lw, REG)
        ctx.rectangle(x, y + REG / 2 - lw / 2, REG, lw)
    ctx.fill()


def svg_image(path, width):
    png = cairosvg.svg2png(url=str(path), output_width=width)
    return Image.open(io.BytesIO(png)).convert('RGBA')


def paste_premul(ctx, img, x, y):
    """Paint a PIL RGBA image onto a cairo context."""
    arr = np.asarray(img, np.float32)
    a = arr[..., 3:4] / 255
    bgra = np.dstack([arr[..., 2:3] * a, arr[..., 1:2] * a, arr[..., 0:1] * a, arr[..., 3:4]]).astype(np.uint8)
    w, h = img.size
    stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, w)
    data = np.zeros((h, stride // 4, 4), np.uint8)
    data[:, :w] = bgra
    src = cairo.ImageSurface.create_for_data(memoryview(data), cairo.FORMAT_ARGB32, w, h, stride)
    ctx.set_source_surface(src, x, y)
    ctx.paint()


# ---------------------------------------------------------------- scope beam

MARK = [
    [(0, 519.62), (300, 0), (542.84, 420.62), (466.63, 420.62), (300, 132), (76.21, 519.62)],
    [(114.32, 519.62), (300, 198), (338.11, 264), (228.63, 453.62), (561.89, 453.62), (600, 519.62)],
]
COLLAPSE, BLINKS, END = 260, ((300, 360), (420, 520)), 700


def _blanked(t):
    return any(a < t < b for a, b in BLINKS)


def lissajous_samples(t0, cx, cy, A, fa, fb, play=7000):
    """Beam samples (t ms, x, y) or None for a blanked gap. Same envelope as the home page."""
    out, phi, delta, amp = [], 0.0, math.pi / 4, 0.0
    for t in range(1, play + END + 1):
        o = t - play
        amp = min(1, amp + 1 / 1400) if o < 0 else max(0, amp - 1 / COLLAPSE)
        phi += 2 * math.pi / 520
        delta += .00025
        if t % 2:
            continue
        if o > 0 and _blanked(o):
            out.append(None)
            continue
        out.append((t0 + t, cx + A * amp * math.sin(fa * phi + delta), cy + A * .82 * amp * math.sin(fb * phi)))
    return out


def mark_samples(t0, cx, cy, A, slow=2400, fast=1100, play=6500):
    subs = []
    for pts in MARK:
        P = [((x - 300) / 300, (y - 259.81) / 300) for x, y in pts + [pts[0]]]
        cum = [0.0]
        for i in range(1, len(P)):
            cum.append(cum[-1] + math.dist(P[i], P[i - 1]))
        subs.append((P, cum))
    lap_len = sum(c[-1] for _, c in subs)

    def point_at(sub, d):
        P, cum = sub
        i = 1
        while i < len(cum) - 1 and cum[i] < d:
            i += 1
        f = (d - cum[i - 1]) / ((cum[i] - cum[i - 1]) or 1)
        return P[i - 1][0] + (P[i][0] - P[i - 1][0]) * f, P[i - 1][1] + (P[i][1] - P[i - 1][1]) * f

    om, zeta = 2 * math.pi * 55, .35
    d, lap, sub, amp = 0.0, 0, 0, 1.0

    def place(p, amp):
        k = A * .95 * amp
        return cx + p[0] * k, cy + p[1] * k

    bx, by = place(subs[0][0][0], 1)
    vx = vy = 0.0
    out = []
    for t in range(1, play + END + 1):
        o = t - play
        if o > 0:
            amp = max(0, amp - 1 / COLLAPSE)
        d += lap_len / (slow if lap == 0 else fast)
        if d >= lap_len:
            d -= lap_len
            lap += 1
        local, si = d, 0
        while si < len(subs) - 1 and local > subs[si][1][-1]:
            local -= subs[si][1][-1]
            si += 1
        tx, ty = place(point_at(subs[si], min(local, subs[si][1][-1])), amp)
        if si != sub:
            sub, bx, by, vx, vy = si, tx, ty, 0.0, 0.0
            out.append(None)
        ax = om * om * (tx - bx) - 2 * zeta * om * vx
        ay = om * om * (ty - by) - 2 * zeta * om * vy
        vx += ax / 1000
        vy += ay / 1000
        bx += vx / 1000
        by += vy / 1000
        if t % 2:
            continue
        if o > 0 and _blanked(o):
            out.append(None)
            continue
        out.append((t0 + t, bx, by))
    return out


def draw_beam(ctx, samples, now, tau, gain):
    """Phosphor trail: every 2ms sample fades with age; slow stretches of the beam glow brighter."""
    cutoff = now - tau * 4
    N = 6
    buckets = [[] for _ in range(N)]
    for p, q in zip(samples, samples[1:]):
        if not p or not q or q[0] > now or p[0] < cutoff:
            continue
        seg = math.dist(p[1:], q[1:])
        a = math.exp(-(now - q[0]) / tau) * min(1, math.sqrt(2.4 * S / max(seg, .35 * S))) * gain
        if a < .03:
            continue
        buckets[min(N - 1, int(a * N))].append((p, q))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    r, g, b = rgb01(ACID)
    for i, segs in enumerate(buckets):
        if not segs:
            continue
        a = (i + .5) / N
        for width, alpha in ((4 * S, a * .14), (1.25 * S, a)):
            for p, q in segs:
                ctx.move_to(p[1], p[2])
                ctx.line_to(q[1], q[2])
            ctx.set_source_rgba(r, g, b, alpha)
            ctx.set_line_width(width)
            ctx.stroke()
