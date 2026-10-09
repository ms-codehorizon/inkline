"""The loft office from each camera. Room lines are thin and soft;
anything near the characters is drawn in ink."""
import math
import random

from engine.ink import ACCENT, INK, PAPER, SOFT, WASH, W, H


def _window(c, x0, y0, x1, y1, cols=3, rows=5):
    c.stroke([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 1.8, SOFT, smooth=False, closed=True)
    c.stroke([(x0 + 12, y0 + 12), (x1 - 12, y0 + 12), (x1 - 12, y1 - 12), (x0 + 12, y1 - 12)], 1.2, SOFT, smooth=False, closed=True)
    for i in range(1, cols):
        x = x0 + (x1 - x0) * i / cols
        c.stroke([(x, y0 + 12), (x, y1 - 12)], 1.4, SOFT, smooth=False)
    for j in range(1, rows):
        y = y0 + (y1 - y0) * j / rows
        c.stroke([(x0 + 12, y), (x1 - 12, y)], 1.4, SOFT, smooth=False)
    for k in range(3):
        gx = x0 + 60 + k * 26
        c.stroke([(gx, y0 + 60 + k * 10), (gx + 70, y0 + 10 + k * 10)], 1.0, SOFT)
    c.stroke([(x0 - 22, y1 + 4), (x1 + 22, y1 + 4), (x1 + 22, y1 + 18), (x0 - 22, y1 + 18)], 1.6, SOFT, smooth=False)


def _bricks(c, cx, cy, n, seed):
    rng = random.Random(seed)
    bw, bh = 76, 30
    for _ in range(n):
        r = rng.randint(-2, 2)
        k = rng.randint(-3, 3)
        x = cx + k * bw + (bw / 2 if r % 2 else 0)
        y = cy + r * bh
        c.stroke([(x, y + bh - 6), (x, y), (x + bw - 6, y)], 1.1, SOFT, smooth=False)


def _leaf(c, x, y, size, angle, seed):
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)

    def rot(px, py):
        return (x + (px * ca - py * sa) * size, y + (px * sa + py * ca) * size)
    outline = [(0, 0), (0.12, -0.36), (0.42, -0.52), (0.5, -0.22), (0.62, -0.5), (0.86, -0.42), (0.84, -0.18),
               (0.98, -0.3), (1.25, 0.0), (0.98, 0.3), (0.84, 0.18), (0.86, 0.42), (0.62, 0.5), (0.5, 0.22),
               (0.42, 0.52), (0.12, 0.36)]
    pts = [rot(px, py) for px, py in outline]
    c.fill(pts, PAPER, smooth=False)
    c.stroke(pts + pts[:2], 1.8, SOFT, smooth=False)
    c.stroke([rot(0.02, 0), rot(0.6, 0.02), rot(1.15, 0.0)], 1.4, SOFT)


def monstera(c, x, y, s=1.0, seed=3):
    pot = [(x - 70 * s, y), (x + 70 * s, y), (x + 55 * s, y + 120 * s), (x - 55 * s, y + 120 * s)]
    leaves = [(-120, -330, 150, -150), (40, -420, 160, -95), (110, -250, 140, -30), (-200, -170, 130, 190),
              (150, -110, 120, 20), (-60, -230, 120, -120)]
    for i, (lx, ly, ls, la) in enumerate(leaves):
        c.stroke([(x, y), (x + lx * s * 0.4, y + ly * s * 0.55), (x + lx * s, y + ly * s)], 1.4, SOFT)
    for i, (lx, ly, ls, la) in enumerate(leaves):
        _leaf(c, x + lx * s, y + ly * s, ls * s, la, seed + i)
    c.fill(pot, PAPER, smooth=False)
    c.stroke(pot, 1.8, SOFT, smooth=False, closed=True)


def table(c, x0, x1, y, phone_x=None, laptop=(None, None), lit=False, flip=False):
    top = [(x0, y + 4), (x1, y - 6), (x1, y + 44), (x0, y + 56)]
    c.fill(top, WASH, smooth=False)
    c.stroke(top, 2.4, smooth=False, closed=True)
    c.stroke([(x0 + 10, y + 18), (x1 - 10, y + 8)], 1.0, SOFT)
    for lx in (x0 + 40, x1 - 40):
        c.stroke([(lx, y + 52), (lx + 4, H + 20)], 2.6)
    lx0, lx1 = laptop
    if lx0 is not None:
        lap = [(lx0, y - 22), (lx1, y - 26), (lx1 + 10, y - 4), (lx0 - 8, y + 2)]
        c.fill(lap, PAPER, smooth=False)
        c.stroke(lap, 2.2, smooth=False, closed=True)
        c.stroke([(lx0 - 8, y + 2), (lx0 - 8, y + 8), (lx1 + 10, y + 2), (lx1 + 10, y - 4)], 1.6, smooth=False)
    if phone_x is not None:
        px = phone_x
        ph = [(px, y - 10), (px + 74, y - 12), (px + 80, y + 4), (px - 4, y + 6)]
        c.fill(ph, ACCENT if lit else INK, smooth=False)
        c.stroke(ph, 2.0, smooth=False, closed=True)
        if lit:
            for k, (dx, dy) in enumerate(((-10, -40), (38, -52), (86, -40))):
                c.stroke([(px + 38 + dx * 0.3, y - 20), (px + 38 + dx, y + dy)], 2.2, ACCENT)


def label(c):
    c.text(W - 40, 36, "Fictional sketch", 22, SOFT, anchor="ra")


def room_a(c, lit=False):
    """Behind Theo: window left, brick, monstera right, table with laptop and phone."""
    c.stroke([(0, 742), (W, 734)], 1.4, SOFT)
    _window(c, 90, 40, 540, 690)
    _bricks(c, 1200, 150, 14, 1)
    _bricks(c, 620, 610, 8, 2)
    monstera(c, 1600, 640, 1.0)
    table(c, 1310, 1960, 812, phone_x=1790, laptop=(1440, 1740), lit=lit)


def room_b(c, lit=False):
    """Behind Dana: window far left, monstera, shelf right, table foreground left."""
    c.stroke([(0, 738), (W, 744)], 1.4, SOFT)
    _window(c, 60, 50, 430, 690)
    _bricks(c, 1260, 120, 10, 4)
    monstera(c, 620, 650, 0.85, seed=11)
    x0, x1 = 1520, 1840
    for x in (x0, x1):
        c.stroke([(x, 90), (x, 735)], 1.6, SOFT)
    rng = random.Random(9)
    for sy in (240, 420, 600):
        c.stroke([(x0, sy), (x1, sy)], 1.6, SOFT)
        bx = x0 + 20
        while bx < x1 - 60:
            bw = rng.randint(14, 26)
            bh = rng.randint(70, 120)
            if rng.random() < 0.75:
                c.stroke([(bx, sy), (bx, sy - bh), (bx + bw, sy - bh), (bx + bw, sy)], 1.2, SOFT, smooth=False)
            bx += bw + rng.randint(2, 18)
    c.stroke([(1640, 240), (1660, 140), (1700, 140), (1720, 240)], 1.4, SOFT, smooth=False)
    c.ellipse(1680, 120, 46, 26, 1.4, SOFT, a0=180, a1=360)
    table(c, -40, 600, 812, phone_x=470, laptop=(90, 400), lit=lit)


def room_c(c, lit=False):
    """Wide two-shot: both chairs in profile, table between, phone and laptop on it."""
    c.stroke([(0, 760), (W, 756)], 1.4, SOFT)
    _window(c, 60, 60, 420, 700, cols=2, rows=5)
    _window(c, 1500, 60, 1860, 700, cols=2, rows=5)
    _bricks(c, 960, 170, 16, 5)
    _bricks(c, 700, 560, 6, 6)
    _bricks(c, 1240, 520, 6, 7)
    monstera(c, 960, 690, 0.8, seed=21)
    # the low table, seen from the side, between the chairs
    top = [(700, 816), (1220, 816), (1240, 850), (680, 850)]
    c.fill(top, WASH, smooth=False)
    c.stroke(top, 2.4, smooth=False, closed=True)
    for lx in (730, 1190):
        c.stroke([(lx, 850), (lx, 1000)], 2.6)
    lap = [(820, 796), (1000, 796), (1010, 814), (812, 814)]
    c.fill(lap, PAPER, smooth=False)
    c.stroke(lap, 2.0, smooth=False, closed=True)
    ph = [(1080, 804), (1150, 804), (1154, 816), (1078, 816)]
    c.fill(ph, ACCENT if lit else INK, smooth=False)
    c.stroke(ph, 1.8, smooth=False, closed=True)
    if lit:
        for dx, dy in ((-14, -40), (0, -54), (14, -40)):
            c.stroke([(1116 + dx * 0.3, 796), (1116 + dx, 804 + dy)], 2.2, ACCENT)


def _diff_lines(c, x0, y0, x1, y1, scroll, seed=3):
    """A code diff scrolling by too fast to read: ruled lines of varying length,
    a few marked with the accent (removed) or a solid ink bar (added)."""
    rng = random.Random(seed)
    rows = []
    for i in range(200):
        kind = rng.choices(("ctx", "add", "del"), (6, 3, 2))[0]
        rows.append((kind, rng.randint(2, 7), rng.uniform(0.25, 0.95)))
    lh = 26
    k = int(scroll // lh)
    off = scroll % lh
    y = y0 - off
    i = k
    while y < y1:
        kind, indent, ln = rows[i % len(rows)]
        xa = x0 + 60 + indent * 14
        xb = xa + (x1 - x0 - 120) * ln * 0.6
        if y > y0 - lh:
            if kind == "del":
                c.rect(x0 + 4, y + 4, x1 - 4, y + lh - 4, (240, 215, 208))
                c.stroke([(xa, y + lh / 2), (xb, y + lh / 2)], 2.2, ACCENT, smooth=False, wob=0.3)
                c.text(x0 + 18, y + 5, "-", 20, ACCENT)
            elif kind == "add":
                c.rect(x0 + 4, y + 4, x1 - 4, y + lh - 4, WASH)
                c.stroke([(xa, y + lh / 2), (xb, y + lh / 2)], 2.2, INK, smooth=False, wob=0.3)
                c.text(x0 + 18, y + 5, "+", 20, INK)
            else:
                c.stroke([(xa, y + lh / 2), (xb, y + lh / 2)], 1.4, SOFT, smooth=False, wob=0.3)
        y += lh
        i += 1


def room_d(c, lit=False, t=0.0):
    """Laptop screen insert: the open laptop on Theo's knees, a diff flying past."""
    c.stroke([(0, 300), (W, 280)], 1.2, SOFT)
    c.stroke([(0, 940), (W, 920)], 1.6, SOFT)
    # trousers under the laptop
    lap = [(0, 1080), (0, 900), (600, 870), (1500, 880), (W, 930), (W, 1080)]
    c.fill(lap, PAPER, smooth=False)
    c.hatch(lap, -55, 11, 1.3, smooth=False)
    c.stroke([(0, 900), (600, 870), (1500, 880), (W, 930)], 2.6, smooth=False)
    # lid and screen
    lid = [(380, 120), (1560, 120), (1600, 820), (340, 820)]
    c.fill(lid, PAPER, smooth=False)
    c.stroke(lid, 3.4, smooth=False, closed=True)
    scr = (430, 170, 1510, 770)
    c.rect(*scr, (248, 244, 236))
    c.stroke([(scr[0], scr[1]), (scr[2], scr[1]), (scr[2], scr[3]), (scr[0], scr[3])], 2.0, SOFT, smooth=False, closed=True)
    c.rect(scr[0], scr[1], scr[2], scr[1] + 34, WASH)
    for i, x in enumerate((452, 476, 500)):
        c.ellipse(x, scr[1] + 17, 7, 7, 1.6, SOFT)
    c.text(560, scr[1] + 8, "4,000 files changed", 18, SOFT)
    # the scrolling diff, clipped to the screen
    c.push_clip(scr[0], scr[1] + 34, scr[2], scr[3])
    _diff_lines(c, scr[0], scr[1] + 34, scr[2], scr[3], scroll=t * 1400)
    c.pop_clip()
    # hinge and base edge
    base = [(300, 820), (1640, 820), (1700, 880), (240, 880)]
    c.fill(base, WASH, smooth=False)
    c.stroke(base, 2.6, smooth=False, closed=True)


# Camera letter -> how to draw the room and where each seat is.
# seats: seat name -> (x, y, scale, flip). Characters are designed facing right.
CAMERAS = {
    "A": {"draw": room_a, "seats": {"left": (800, 545, 1.0, False)}, "about": "close-up of the left seat"},
    "B": {"draw": room_b, "seats": {"right": (1120, 545, 1.0, True)}, "about": "close-up of the right seat"},
    "C": {"draw": room_c, "seats": {"left": (430, 690, 0.52, False), "right": (1490, 690, 0.52, True)}, "about": "wide two-shot"},
    "D": {"draw": room_d, "seats": {}, "about": "laptop screen insert, Theo's hand may hover"},
}
