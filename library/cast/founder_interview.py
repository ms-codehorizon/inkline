"""Theo and Dana, drawn in ink. Both are designed facing right with the
neck base at (0, 0); place them with Canvas.at(x, y, scale, flip)."""
import math
import random

from engine.ink import INK, PAPER, SOFT, WASH, catmull, ellipse_pts

DEFAULT = {"eyes": "open", "brows": "neutral", "mouth": "rest", "talk": 0.0,
           "head": "level", "hands": None, "blink": False, "breath": 0.0}

HEAD_OFFSET = {"level": (0, 0), "tilt": (6, 4), "lean": (14, 8), "down": (6, 12)}
LEAN_POSES = {"elbows_knees": (26, 14), "gesture": (6, 0)}


def capsule(p0, p1, r0, r1, n=8):
    """A tapered limb from p0 to p1 with rounded ends."""
    (x0, y0), (x1, y1) = p0, p1
    a = math.atan2(y1 - y0, x1 - x0)
    pts = []
    for k in range(n + 1):
        t = a + math.pi / 2 + math.pi * k / n
        pts.append((x0 + r0 * math.cos(t), y0 + r0 * math.sin(t)))
    for k in range(n + 1):
        t = a - math.pi / 2 + math.pi * k / n
        pts.append((x1 + r1 * math.cos(t), y1 + r1 * math.sin(t)))
    return pts


def _part(c, pts, hatch=None, w=3.0, open_top=False):
    """Fill and outline a limb. open_top leaves the shoulder end unlined so
    the arm grows out of the body instead of sitting on it."""
    c.fill(pts, PAPER, smooth=False)
    if hatch is not None:
        c.hatch(pts, hatch, 11, 1.3, smooth=False)
    if open_top:
        n = len(pts) // 2
        c.stroke(pts[n - 1:] + pts[:1], w, smooth=False)
    else:
        c.stroke(pts + pts[:2], w, smooth=False)


def _band(c, p0, p1, r0, r1, t, w=2.0):
    (x0, y0), (x1, y1) = p0, p1
    a = math.atan2(y1 - y0, x1 - x0)
    cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
    r = r0 + (r1 - r0) * t
    nx, ny = -math.sin(a), math.cos(a)
    bx, by = math.cos(a) * 6, math.sin(a) * 6
    c.stroke([(cx - nx * r, cy - ny * r), (cx + bx, cy + by), (cx + nx * r, cy + ny * r)], w)


def chair(c):
    back = [(-305, -60), (0, -88), (305, -58), (330, 120), (335, 330), (-335, 330), (-330, 120)]
    c.fill(back, WASH)
    c.stroke(back, 2.6, closed=True)
    c.stroke([(-250, -40), (-262, 150), (-255, 300)], 1.2, SOFT)
    c.stroke([(250, -40), (262, 150), (255, 300)], 1.2, SOFT)
    for sx in (-1, 1):
        arm = [(sx * 420, 250), (sx * 300, 236), (sx * 255, 262), (sx * 262, 330), (sx * 300, 520), (sx * 430, 520), (sx * 440, 300)]
        c.fill(arm, WASH)
        c.stroke(arm, 2.6, closed=True)
        c.stroke([(sx * 300, 260), (sx * 410, 270)], 1.2, SOFT)


def _hand(c, x, y, s=1.0, a=0.0):
    """A relaxed hand, knuckles toward angle a (radians, 0 = right)."""
    ca, sa = math.cos(a), math.sin(a)

    def r(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    pts = [r(-26, -20), r(-4, -26), r(22, -22), r(34, -6), r(32, 14), r(12, 24), r(-18, 22), r(-30, 4)]
    c.fill(pts, PAPER)
    c.stroke(pts, 2.8, closed=True)
    for k in (-6, 6, 18):
        c.stroke([r(k, 8), r(k + 10, 20)], 1.5)
    c.stroke([r(-10, -14), r(6, -8), r(10, 2)], 1.6)


def _eyes(c, st, near, far, lid=False):
    eyes = "closed" if st["blink"] else st["eyes"]
    dx, dy = {"up_side": (-5, -7), "camera": (-7, 1)}.get(eyes, (2, 0))
    if st["head"] == "down" and eyes == "open":
        dx, dy = 2, 4
    for i, (x, y, rx, ry) in enumerate((near, far)):
        e = eyes
        if e == "one_open":
            e = "open" if i == 0 else "closed"
        if e in ("open", "up_side", "camera"):
            grow = 1.15 if e == "camera" else 1.0
            c.fill_ellipse(x + dx, y + dy, rx * grow, ry * grow, INK)
            if lid:
                c.stroke([(x - rx * 2.4, y - ry * 0.8), (x, y - ry * 1.5), (x + rx * 2.4, y - ry * 0.8)], 2.0)
        elif e == "half":
            c.stroke([(x - rx * 2.2, y - 1), (x + rx * 2.2, y - 2)], 2.4)
            c.fill_ellipse(x + dx, y + ry * 0.45, rx * 0.9, ry * 0.5, INK)
        else:
            c.stroke([(x - rx * 2.0, y - 1), (x, y + ry * 0.7), (x + rx * 2.0, y - 1)], 2.4)


def _brows(c, st, near, far, w):
    up = {"raised": -10, "knit": 3}.get(st["brows"], 0)
    knit = 7 if st["brows"] == "knit" else 0
    arch = 4 if st["brows"] == "raised" else 0
    for (x0, x1, y), inner_right in ((near, True), (far, False)):
        yl = y + up + (knit if not inner_right else -knit * 0.4)
        yr = y + up + (knit if inner_right else -knit * 0.4)
        c.stroke([(x0, yl), ((x0 + x1) / 2, y + up - 5 - arch), (x1, yr)], w)


def _mouth(c, st, cx, cy, wide):
    if st["talk"] > 0.08:
        c.fill_ellipse(cx, cy + 2, wide * 0.4, 2.5 + 10 * st["talk"], INK)
        return
    m, h = st["mouth"], wide / 2
    if m == "smile":
        c.stroke([(cx - h, cy - 3), (cx, cy + 5), (cx + h, cy - 3)], 2.6)
    elif m == "flat":
        c.stroke([(cx - h, cy), (cx + h, cy)], 2.6)
    elif m == "open":
        c.fill_ellipse(cx, cy + 2, wide * 0.28, 6, INK)
    else:
        c.stroke([(cx - h, cy), (cx, cy + 2), (cx + h, cy)], 2.6)


def _legs(c, angle):
    legs = [(-190, 292), (-300, 350), (-362, 402), (-372, 442), (-338, 480), (-180, 474), (0, 492),
            (180, 474), (338, 480), (372, 442), (362, 402), (300, 350), (185, 292)]
    c.fill(legs, PAPER)
    c.hatch(legs, angle, 11, 1.3)
    c.stroke(legs, 3.0, closed=True)
    c.stroke([(-336, 470), (-100, 455), (130, 500)], 2.2)
    c.stroke([(336, 470), (100, 455), (-130, 500)], 2.2)


# ---------------------------------------------------------------------------
THEO_HEAD_DROP = 24


def theo(c, state=None, with_chair=True):
    st = dict(DEFAULT, **(state or {}))
    b = st["breath"]
    if with_chair:
        chair(c)
    _legs(c, -58)
    with c.at(0, b):
        torso = [(-45, -8), (-150, 18), (-200, 70), (-206, 180), (-190, 300), (185, 300), (200, 170), (195, 65), (140, 15), (50, -4)]
        c.fill(torso, PAPER)
        c.stroke(torso, 3.0, closed=True)
        c.stroke([(14, 16), (20, 150), (24, 298)], 1.8)
        c.stroke([(30, 14), (36, 150), (40, 298)], 1.8)
        for y in (45, 105, 165, 225):
            c.dot(27 + y * 0.02, y, 3.2)
        for w in ([(-130, 120), (-95, 150)], [(100, 205), (138, 232)], [(-70, 250), (-30, 270)], [(120, 95), (150, 120)]):
            c.stroke(w, 1.3, SOFT)
        _theo_arms(c, st)
        c.stroke([(-45, -8), (-150, 18), (-200, 66), (-218, 112)], 3.0)
        c.stroke([(50, -4), (140, 15), (195, 62), (216, 108)], 3.0)
        d = THEO_HEAD_DROP
        neck = [(-40, -96 + d), (42, -66 + d), (46, 2), (-42, 2)]
        c.fill(neck, PAPER, smooth=False)
        c.stroke([(-40, -96 + d), (-43, -6)], 3.0)
        c.stroke([(42, -66 + d), (46, -4)], 3.0)
        c.stroke([(-50, -2), (6, 16), (58, 2)], 2.8)
        c.stroke([(-48, -18), (6, -4), (54, -14)], 2.4)
        hx, hy = HEAD_OFFSET[st["head"]]
        with c.at(hx, hy + d - b * 0.3):
            _theo_head(c, st)


def _theo_arms(c, st):
    hands = st["hands"] or "knees"
    for sx in (-1, 1):
        sh, el = (sx * 170, 96), (sx * 236, 262)
        _part(c, capsule(sh, el, 40, 33), open_top=True)
        _band(c, sh, el, 40, 33, 0.74)
        _band(c, sh, el, 40, 33, 0.86, 1.5)
        right = sx > 0
        pose = hands if right else ("knees" if hands not in ("frame", "heart") else hands)
        if pose == "knees":
            wr = (sx * 282, 384)
            _part(c, capsule(el, wr, 31, 25))
            _hand(c, sx * 292, 412, 1.25, math.pi / 2 - sx * 0.5)
        elif pose in ("palm_up", "finger_up", "chop", "paste", "frame"):
            wr = (sx * 300, 168)
            _part(c, capsule(el, wr, 31, 25))
            if pose == "finger_up":
                _hand(c, sx * 304, 140, 1.1, -math.pi / 2)
                c.stroke([(sx * 300, 116), (sx * 304, 64)], 10.0)
            elif pose == "palm_up":
                _hand(c, sx * 318, 150, 1.15, -0.2 if right else math.pi + 0.2)
            else:
                _hand(c, sx * 312, 146, 1.15, -math.pi / 2)
        elif pose == "heart":
            wr = (sx * 120, 150)
            _part(c, capsule(el, wr, 31, 25))
            _hand(c, sx * 96, 132, 1.2, math.pi)
        elif pose == "hover":
            wr = (sx * 320, 300)
            _part(c, capsule(el, wr, 31, 25))
            _hand(c, sx * 345, 300, 1.2, 0)


def _theo_head(c, st):
    head = [(-10, -335), (60, -322), (100, -278), (112, -218), (110, -160), (100, -112), (82, -76),
            (46, -58), (5, -70), (-45, -100), (-86, -132), (-108, -200), (-102, -276), (-62, -322)]
    c.fill(head, PAPER)
    c.stroke(head, 3.4, closed=True)
    c.ellipse(-62, -186, 15, 25, 2.8, a0=80, a1=290)
    c.stroke([(-64, -200), (-70, -186), (-62, -172)], 1.6)
    rng = random.Random(7)
    for _ in range(34):
        t = rng.random()
        x = -36 + t * 118
        jaw = -96 + t * 24 + 16 * math.sin(t * math.pi) * 0.4
        c.dot(x, jaw - rng.uniform(6, 30), 1.0)
    c.stroke([(104, -210), (116, -182), (129, -162), (123, -151), (108, -149)], 2.8)
    _eyes(c, st, (30, -203, 5.5, 7), (91, -202, 4.5, 6.5))
    c.ellipse(28, -205, 31, 29, 3.0)
    c.ellipse(90, -203, 20, 27, 2.6)
    c.stroke([(59, -211), (64, -216), (70, -211)], 2.4)
    c.stroke([(-3, -210), (-55, -197)], 2.6)
    _brows(c, st, (6, 48, -250), (76, 106, -248), 3.2)
    _mouth(c, st, 72, -108, 32)


# ---------------------------------------------------------------------------
DANA_HEAD_DROP = 36
HAIR = [(-20, -362), (60, -358), (122, -326), (152, -276), (150, -228), (126, -210), (122, -150),
        (118, -86), (100, -40), (66, -26), (30, -40), (-10, -40), (-40, -10), (-95, 22), (-150, -8),
        (-176, -100), (-174, -220), (-146, -306), (-92, -350)]


def dana(c, state=None, with_chair=True):
    st = dict(DEFAULT, **(state or {}))
    if st["hands"] is None:
        st["hands"] = "pen_ready"
    b = st["breath"]
    if with_chair:
        chair(c)
    _legs(c, -52)
    lx, ly = LEAN_POSES.get(st["hands"], (0, 0))
    with c.at(lx, b + ly):
        hx, hy = HEAD_OFFSET[st["head"]]
        d = DANA_HEAD_DROP
        with c.at(hx, hy + d - b * 0.3):
            c.fill(HAIR, PAPER)
            _curls(c, HAIR, 0)
        torso = [(-40, -6), (-165, 18), (-205, 60), (-210, 180), (-198, 300), (190, 300), (200, 170), (192, 58), (160, 16), (52, -2)]
        c.fill(torso, PAPER)
        c.hatch(torso, 64, 11, 1.3)
        c.stroke(torso, 3.0, closed=True)
        tee = [(-38, -2), (50, 0), (44, 60), (12, 214), (-14, 140), (-34, 50)]
        c.fill(tee, PAPER, smooth=False)
        c.stroke([(-36, 8), (6, 34), (48, 10)], 2.0)
        c.stroke([(-38, 0), (-56, 80), (-82, 98), (-62, 122), (-30, 170), (10, 218)], 3.0, smooth=False)
        c.stroke([(50, 0), (68, 78), (94, 92), (76, 116), (44, 165), (12, 218)], 3.0, smooth=False)
        c.stroke([(-82, 98), (-58, 108)], 2.2)
        c.stroke([(94, 92), (70, 102)], 2.2)
        c.dot(14, 250, 4.5)
        _dana_arms(c, st)
        c.stroke([(-40, -6), (-165, 18), (-205, 58), (-220, 100)], 3.0)
        c.stroke([(52, -2), (160, 16), (192, 56), (210, 96)], 3.0)
        neck = [(-16, -98 + d), (42, -86 + d), (46, 2), (-20, 2)]
        c.fill(neck, PAPER, smooth=False)
        c.stroke([(-16, -98 + d), (-19, -2)], 3.0)
        c.stroke([(42, -86 + d), (46, -2)], 3.0)
        with c.at(hx, hy + d - b * 0.3):
            _dana_head(c, st)


def _dana_arms(c, st):
    hands = st["hands"]
    sh, el = (-174, 94), (-232, 262)
    _part(c, capsule(sh, el, 38, 30), 64, open_top=True)
    book = [(-70, 318), (150, 300), (168, 352), (-52, 372)]
    if hands == "notebook_flat":
        book = [(-80, 350), (150, 340), (160, 372), (-70, 384)]
    wr = (-92, 338)
    _part(c, capsule(el, wr, 28, 22), 20)
    c.fill(book, PAPER, smooth=False)
    c.stroke(book + book[:1], 2.8, smooth=False)
    c.stroke([(-52, 372), (-50, 381), (168, 360), (168, 352)], 2.0, smooth=False)
    for k in range(4):
        y0 = 330 + k * 9
        c.stroke([(-30, y0 + 2), (120, y0 - 10)], 1.0, SOFT)
    _hand(c, -70, 340, 1.0, -0.3)
    sh, el = (168, 92), (224, 252)
    _part(c, capsule(sh, el, 38, 30), 64, open_top=True)
    wr = (122, 318)
    _part(c, capsule(el, wr, 28, 22), -20)
    _hand(c, 100, 314, 0.95, math.pi * 0.85)
    if hands == "pen_ready":
        c.stroke([(84, 326), (122, 270)], 4.4)
    elif hands == "writing":
        c.stroke([(70, 336), (104, 290)], 4.4)
    elif hands == "cross_out":
        c.stroke([(70, 336), (104, 290)], 4.4)
        c.stroke([(-10, 352), (60, 334)], 3.2, salt=3)
        c.stroke([(-6, 342), (58, 342)], 3.0, salt=4)


def _dana_head(c, st):
    face = [(5, -285), (70, -280), (102, -245), (108, -200), (104, -160), (96, -128), (80, -98),
            (55, -82), (25, -88), (-5, -108), (-30, -140), (-40, -190), (-30, -250)]
    c.fill(face, PAPER)
    c.stroke(face[1:-2], 3.2)
    rng = random.Random(41)
    for k in range(8):
        t = k / 7
        x = -36 + t * 150
        y = -262 - 22 * math.sin(t * math.pi) + rng.uniform(-4, 4)
        c.fill_ellipse(x, y, 15, 13, PAPER)
    for k in range(8):
        t = k / 7
        x = -36 + t * 150
        y = -262 - 22 * math.sin(t * math.pi) + rng.uniform(-4, 4)
        c.ellipse(x, y, 13, 12, 2.2, SOFT if k in (3, 4) else INK, a0=-20 + rng.uniform(-20, 20), a1=200)
    c.stroke([(102, -200), (112, -170), (114, -156), (104, -150), (95, -152)], 2.6)
    _eyes(c, st, (32, -190, 5, 6.5), (86, -188, 4, 6), lid=True)
    c.stroke([(18, -194), (11, -199)], 1.8)
    _brows(c, st, (16, 48, -216), (74, 98, -215), 2.6)
    _mouth(c, st, 76, -118, 28)


def _inside(x, y, poly):
    n, j, ins = len(poly), len(poly) - 1, False
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            ins = not ins
        j = i
    return ins


def _curls(c, poly, seed):
    """Loose C-shaped curls inside the hair shape and a scalloped edge.
    A streak near the front is drawn in soft ink: the silver."""
    rng = random.Random(100 + seed)
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    sp = 30
    y = min(ys) + 10
    row = 0
    while y < max(ys):
        x = min(xs) + (sp / 2 if row % 2 else 0)
        while x < max(xs):
            px, py = x + rng.uniform(-7, 7), y + rng.uniform(-7, 7)
            if _inside(px, py, poly) and rng.random() > 0.18:
                r = rng.uniform(8, 14)
                a0 = rng.uniform(0, 360)
                silver = (20 < px < 110 and py < -270) or rng.random() < 0.08
                c.ellipse(px, py, r, r * rng.uniform(0.8, 1.1), 2.0, SOFT if silver else INK,
                          a0=a0, a1=a0 + rng.uniform(200, 290))
            x += sp
        y += sp * 0.85
        row += 1
    edge = catmull(poly, closed=True, steps=6)
    from engine.ink import _resample
    edge = _resample(edge, 24)
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    for (x0, y0), (x1, y1) in zip(edge, edge[1:]):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        a = math.degrees(math.atan2(my - cy, mx - cx))
        c.ellipse(mx, my, 14, 12, 2.4, a0=a - 95, a1=a + 95)


CHARACTERS = {"theo": theo, "dana": dana}
DEFAULT_FACE = {"theo": {"mouth": "smile"}, "dana": {"mouth": "flat"}}


def hover_hand(c):
    """Theo's right hand seen from above, palm down, fingers spread, hovering
    over the laptop (camera D). Frame px. The forearm leaves the frame bottom right."""
    with c.at(1290, 760, 1.3):
        arm = [(60, 40), (120, -20), (420, 160), (380, 300), (240, 300)]
        c.fill(arm, PAPER, smooth=False)
        c.stroke([(120, -20), (420, 160)], 3.0)
        c.stroke([(60, 40), (300, 300)], 3.0)
        c.stroke([(250, 112), (300, 156)], 2.2)
        c.stroke([(262, 98), (314, 142)], 1.6)
        palm = [(-80, -50), (40, -90), (120, -30), (100, 60), (-20, 80), (-110, 30)]
        c.fill(palm, PAPER)
        # fingers grow out of the left edge of the palm
        for i, (ang, ln, w) in enumerate(((-158, 150, 22), (-176, 172, 22), (-196, 160, 20), (-218, 122, 18))):
            a = math.radians(ang)
            bx = (-60 + i * 6, -40 + i * 34)
            tip = (bx[0] + ln * math.cos(a), bx[1] + ln * math.sin(a))
            pts = capsule(bx, tip, w, w * 0.8)
            c.fill(pts, PAPER, smooth=False)
            n = len(pts) // 2
            c.stroke(pts[n - 1:] + pts[:1], 2.8, smooth=False)  # open where it meets the palm
            mid = (bx[0] + (tip[0] - bx[0]) * 0.55, bx[1] + (tip[1] - bx[1]) * 0.55)
            c.stroke([(mid[0] - 7, mid[1] - 11), (mid[0] + 4, mid[1] + 9)], 1.4)
        thumb = capsule((30, -70), (-30, -160), 24, 18)
        c.fill(thumb, PAPER, smooth=False)
        n = len(thumb) // 2
        c.stroke(thumb[n - 1:] + thumb[:1], 2.8, smooth=False)
        c.stroke([(40, -90), (120, -30), (100, 60), (-20, 80), (-110, 30)], 3.0)  # palm edge, not over the fingers
        c.stroke([(-50, 30), (10, 20), (60, 40)], 1.6)
