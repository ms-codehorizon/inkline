"""Ink on paper: hand-drawn strokes, flat fills and hatching.

All coordinates are 1920x1080 frame pixels. The canvas draws at a higher
resolution and scales down at the end, which smooths every edge.
"""
import math
import random
import zlib
from contextlib import contextmanager
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
PAPER = (243, 237, 224)
INK = (42, 38, 34)
SOFT = (163, 154, 139)
WASH = (230, 222, 205)
ACCENT = (200, 70, 60)


def catmull(pts, closed=False, steps=10):
    """Smooth curve through the given points."""
    if len(pts) < 3:
        return list(pts)
    p = list(pts)
    if closed:
        p = [p[-1]] + p + [p[0], p[1]]
    else:
        p = [p[0]] + p + [p[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for s in range(steps):
            t = s / steps
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t
                       + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                       + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
                for k in (0, 1)))
    out.append(p[-2])
    return out


def ellipse_pts(cx, cy, rx, ry, a0=0, a1=360, rot=0, n=None):
    n = n or max(12, int(abs(a1 - a0) / 6))
    r = math.radians(rot)
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * math.cos(r) - y * math.sin(r),
                    cy + x * math.sin(r) + y * math.cos(r)))
    return out


def _resample(pts, step):
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if seg == 0:
            continue
        t = step - acc
        while t <= seg:
            out.append((a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg))
            t += step
        acc = seg - (t - step)
    if math.dist(out[-1], pts[-1]) > 0.5:
        out.append(pts[-1])
    return out


class Canvas:
    def __init__(self, boil=0, ss=2, bg=PAPER):
        self.ss = ss
        self.boil = boil
        self.img = Image.new("RGB", (W * ss, H * ss), bg)
        self.d = ImageDraw.Draw(self.img)
        self._t = [(0.0, 0.0, 1.0, False)]  # x, y, scale, flip

    # -- placement ---------------------------------------------------------
    @contextmanager
    def at(self, x, y, scale=1.0, flip=False):
        ox, oy, s, f = self._t[-1]
        fx = -x if f else x
        self._t.append((ox + fx * s, oy + y * s, s * scale, f != flip))
        try:
            yield
        finally:
            self._t.pop()

    def _map(self, pts):
        ox, oy, s, f = self._t[-1]
        m = -1 if f else 1
        return [((ox + m * x * s) * self.ss, (oy + y * s) * self.ss) for x, y in pts]

    @property
    def scale(self):
        return self._t[-1][2]

    # -- strokes -----------------------------------------------------------
    def _rng(self, pts, salt):
        x0, y0 = pts[0]
        key = "|".join(f"{x - x0:.0f},{y - y0:.0f}" for x, y in pts[1:5])
        key += f"|{len(pts)}|{self.boil}|{salt}"
        return random.Random(zlib.crc32(key.encode()))

    def stroke(self, pts, w=3.0, color=INK, smooth=True, closed=False, wob=1.0, taper=True, salt=0):
        """A pen line: wobbles, tapers at both ends, boils with the frame."""
        if len(pts) < 2:
            return
        if closed:
            pts = list(pts) + [pts[0]]
        if smooth and len(pts) > 2:
            pts = catmull(pts[:-1] if closed else pts, closed=closed)
            if closed:
                pts = pts + pts[1:4]  # a pen overlaps where it started
        dev = self._map(pts)
        rng = self._rng(pts, salt)
        sc = self.scale * self.ss
        step = 4 * self.ss
        dev = _resample(dev, step)
        n = len(dev)
        amp = 1.2 * wob * self.ss * max(0.5, min(1.5, self.scale))
        f1, f2 = rng.uniform(0.04, 0.08) / self.ss, rng.uniform(0.15, 0.25) / self.ss
        p1, p2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
        wf, wp = rng.uniform(0.02, 0.05) / self.ss, rng.uniform(0, 6.3)
        pts2, widths = [], []
        s = 0.0
        for i, (x, y) in enumerate(dev):
            a = dev[max(0, i - 1)]
            b = dev[min(n - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dx, dy) or 1
            nx, ny = -dy / ln, dx / ln
            if i:
                s += math.dist(dev[i - 1], dev[i])
            off = amp * (0.65 * math.sin(f1 * s + p1) + 0.35 * math.sin(f2 * s + p2))
            pts2.append((x + nx * off, y + ny * off))
            t = i / max(1, n - 1)
            tp = min(1.0, t / 0.12, (1 - t) / 0.12) if taper and n > 6 else 1.0
            tp = 0.35 + 0.65 * math.sin(tp * math.pi / 2)
            widths.append(max(1.0, w * sc * tp * (1 + 0.12 * math.sin(wf * s + wp))))
        d = self.d
        for i in range(len(pts2) - 1):
            d.line([pts2[i], pts2[i + 1]], fill=color, width=max(1, round((widths[i] + widths[i + 1]) / 2)))
        for (x, y), wd in zip(pts2, widths):
            r = wd / 2
            if r > 1:
                d.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def ellipse(self, cx, cy, rx, ry, w=3.0, color=INK, a0=0, a1=360, rot=0, **kw):
        full = abs(a1 - a0) >= 360
        pts = ellipse_pts(cx, cy, rx, ry, a0, a1 + (12 if full else 0), rot)
        self.stroke(pts, w, color, smooth=False, **kw)

    def dot(self, x, y, r=2.5, color=INK):
        (px, py), = self._map([(x, y)])
        r = r * self.scale * self.ss
        self.d.ellipse([px - r, py - r, px + r, py + r], fill=color)

    # -- fills -------------------------------------------------------------
    def fill(self, pts, color=PAPER, smooth=True):
        if smooth and len(pts) > 2:
            pts = catmull(pts, closed=True)
        self.d.polygon(self._map(pts), fill=color)

    def fill_ellipse(self, cx, cy, rx, ry, color=PAPER, rot=0):
        self.d.polygon(self._map(ellipse_pts(cx, cy, rx, ry, rot=rot, n=48)), fill=color)

    def hatch(self, pts, angle=60, gap=12, w=1.4, color=INK, smooth=True, salt=0):
        """Parallel pen lines clipped to a shape: reads as a dark fabric."""
        if smooth and len(pts) > 2:
            pts = catmull(pts, closed=True)
        dev = self._map(pts)
        mask = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(mask).polygon(dev, fill=255)
        box = mask.getbbox()
        if not box:
            return
        layer = Image.new("RGB", self.img.size, color)
        lines = Image.new("L", self.img.size, 0)
        ld = ImageDraw.Draw(lines)
        x0, y0, x1, y1 = box
        a = math.radians(angle)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        g = gap * self.scale * self.ss
        diag = math.hypot(x1 - x0, y1 - y0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rng = random.Random(zlib.crc32(f"{len(pts)}|{self.boil}|{salt}".encode()))
        k = -diag / 2
        lw = max(1, round(w * self.scale * self.ss))
        while k < diag / 2:
            j = rng.uniform(-0.25, 0.25) * g
            px, py = cx + nx * (k + j), cy + ny * (k + j)
            ld.line([(px - dx * diag, py - dy * diag), (px + dx * diag, py + dy * diag)], fill=255, width=lw)
            k += g
        from PIL import ImageChops
        self.img.paste(layer, (0, 0), ImageChops.multiply(lines, mask))

    # -- text --------------------------------------------------------------
    def text(self, x, y, s, size=28, color=INK, anchor="la", bold=False):
        f = font(size * self.ss, bold)
        (px, py), = self._map([(x, y)])
        self.d.text((px, py), s, font=f, fill=color, anchor=anchor)

    def push_clip(self, x0, y0, x1, y1):
        """Everything drawn until pop_clip is kept inside this box."""
        (a, b), (c, d) = self._map([(x0, y0), (x1, y1)])
        self._clips = getattr(self, "_clips", [])
        self._clips.append((self.img.copy(), (int(min(a, c)), int(min(b, d)), int(max(a, c)), int(max(b, d)))))

    def pop_clip(self):
        before, box = self._clips.pop()
        inside = self.img.crop(box)
        self.img = before
        self.img.paste(inside, box[:2])
        self.d = ImageDraw.Draw(self.img)

    def text_width(self, s, size=28, bold=False):
        return self.d.textlength(s, font=font(size * self.ss, bold)) / self.ss

    def rect(self, x0, y0, x1, y1, color):
        (a, b), (c, d) = self._map([(x0, y0), (x1, y1)])
        self.d.rectangle([min(a, c), min(b, d), max(a, c), max(b, d)], fill=color)

    def finish(self):
        return self.img.resize((W, H), Image.LANCZOS) if self.ss != 1 else self.img


_FONT_CACHE = {}
_FONT_PATHS = [
    Path(__file__).parent / "fonts",
    Path("/System/Library/Fonts/Supplemental"),
    Path("/Library/Fonts"),
    Path("/usr/share/fonts/truetype/inter"),
    Path("/usr/share/fonts/truetype/dejavu"),
    Path("/usr/share/fonts/opentype/inter"),
]
_FONT_NAMES = {False: ["Inter-Regular.ttf", "Inter-Regular.otf", "Inter-Medium.otf", "Arial.ttf", "DejaVuSans.ttf"],
               True: ["Inter-SemiBold.ttf", "Inter-SemiBold.otf", "Inter-Bold.otf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]}


def font(size, bold=False):
    key = (round(size), bold)
    if key not in _FONT_CACHE:
        for d in _FONT_PATHS:
            for n in _FONT_NAMES[bold]:
                if (d / n).exists():
                    _FONT_CACHE[key] = ImageFont.truetype(str(d / n), key[0])
                    break
            if key in _FONT_CACHE:
                break
        else:
            _FONT_CACHE[key] = ImageFont.load_default(key[0])
    return _FONT_CACHE[key]
