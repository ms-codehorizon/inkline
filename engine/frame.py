"""One frame of a video: room from a camera, characters in their seats, props,
caption band and label. Shared by stills.py (one frame per block) and
render.py (every frame).

State vocabulary is in reference/engine.md. Characters' own vocabulary is in
their cast sheet.
"""
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "engine")]
import script as S  # noqa: E402
from ink import ACCENT, INK, PAPER, SOFT, Canvas, H, W  # noqa: E402

CAPTION_BAND = 128  # px, bottom of frame


class Video:
    def __init__(self, slug, cut=None):
        self.dir = ROOT / "videos" / slug
        self.manifest = S.manifest(self.dir / "video.md")
        self.cast = importlib.import_module(f"library.cast.{self.manifest['cast']}")
        self.room = importlib.import_module(f"library.rooms.{self.manifest['room']}")
        self.blocks = {b["id"]: b for b in S.load(self.dir / "stages/01-script/output/script.md")}
        tl_name = "timeline-short.json" if cut == "short" else "timeline.json"
        self.timeline = json.loads((self.dir / "stages/02-voice/output" / tl_name).read_text())
        shots_file = self.dir / "stages/03-storyboard/output/shots.md"
        self.shots = load_shots(shots_file) if shots_file.exists() else {}
        self.people = list(self.cast.CHARACTERS)  # seat order: first = left seat

    def seat_of(self, who):
        return "left" if self.people.index(who) == 0 else "right"


def load_shots(path):
    """shots.md: per block, a starting state and timed changes.

    ## 17
    theo: eyes=open, mouth=smile, hands=knees, head=down
    phone: lit
    at 0.9: theo.head=level
    """
    shots, cur = {}, None
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        m = re.match(r"^##\s+(\S+)", line)
        if m:
            cur = {"start": {}, "changes": []}
            shots[m.group(1)] = cur
            continue
        if cur is None or not line or line.startswith("#"):
            continue
        m = re.match(r"^at\s+([\d.]+)\s*:\s*(.*)$", line)
        if m:
            for kv in m.group(2).split(","):
                k, _, v = kv.strip().partition("=")
                cur["changes"].append((float(m.group(1)), k.strip(), v.strip()))
            continue
        m = re.match(r"^([a-z_][a-z0-9_]*):\s*(.*)$", line)
        if m:
            key, rest = m.group(1), m.group(2)
            if "=" in rest:
                for kv in rest.split(","):
                    k, _, v = kv.strip().partition("=")
                    cur["start"][f"{key}.{k.strip()}"] = v.strip()
            else:
                cur["start"][key] = rest.strip()
    return shots


def state_at(shot, t):
    """Flat dict like {'theo.eyes': 'closed', 'phone': 'lit'} at t seconds into the block."""
    st = dict(shot.get("start", {}))
    for when, k, v in sorted(shot.get("changes", []), key=lambda c: c[0]):
        if when <= t:
            st[k] = v
    return st


def character_state(flat, who):
    pre = who + "."
    return {k[len(pre):]: v for k, v in flat.items() if k.startswith(pre)}


def draw_caption(c, who, text, color=ACCENT):
    c.rect(0, H - CAPTION_BAND, W, H, INK)
    size = 40
    while c.text_width(text, size) > W - 160 and size > 26:
        size -= 2
    y = H - CAPTION_BAND + 18
    if who:
        c.text(W / 2, y, who.upper(), 20, color, anchor="ma", bold=True)
        y += 30
    else:
        y += 14
    c.text(W / 2, y + 2, text, size, PAPER, anchor="ma")


def draw_frame(video, cam, flat, t=0.0, speaking=None, talk=0.0, caption=None, boil=0, blink=None, breath=None):
    """Draw one frame. flat: state dict; caption: (who, text) or None."""
    c = Canvas(boil=boil)
    spec = video.room.CAMERAS[cam]
    lit = flat.get("phone") == "lit"
    try:
        spec["draw"](c, lit=lit, t=t)
    except TypeError:
        spec["draw"](c, lit=lit)
    for who in video.people:
        seat = video.seat_of(who)
        if seat not in spec["seats"]:
            continue
        x, y, scale, flip = spec["seats"][seat]
        st = dict(video.cast.DEFAULT_FACE.get(who, {}))
        st.update(character_state(flat, who))
        st["talk"] = talk if who == speaking else 0.0
        st["blink"] = bool(blink and who in blink)
        st["breath"] = (breath or {}).get(who, 0.0)
        with c.at(x, y, scale, flip):
            video.cast.CHARACTERS[who](c, st)
    if cam == "D" and flat.get("hand") == "hover":
        video.cast.hover_hand(c)
    if caption:
        draw_caption(c, *caption)
    for i, key in enumerate(("text", "text2")):
        if flat.get(key):
            draw_title(c, flat[key], i)
    c.text(W - 40, 36, video.manifest.get("label", "Fictional sketch"), 22, SOFT, anchor="ra")
    return c


def draw_title(c, text, line=0):
    """Centred on-screen text (the closing lines), not a caption."""
    size = 44
    y = 150 + line * 72
    c.rect(W / 2 - c.text_width(text, size) / 2 - 24, y - 10, W / 2 + c.text_width(text, size) / 2 + 24, y + size + 12, PAPER)
    c.text(W / 2, y, text, size, INK, anchor="ma")


def draw_title_card(video, block, at, title, sub="", boil=0):
    """The thumbnail: a quiet frame from one block with the title on it.
    Used by thumb.py and as the opening card of the render."""
    e = next(x for x in video.timeline["blocks"] if x["id"] == block)
    b = video.blocks[block]
    flat = state_at(video.shots.get(block, {}), at)
    c = draw_frame(video, b["cam"], flat, t=at, speaking=None, talk=0.0, caption=None, boil=boil)
    if title:
        size = 76
        while c.text_width(title, size, bold=True) > W - 200 and size > 40:
            size -= 4
        tw = c.text_width(title, size, bold=True)
        x0, y0 = W / 2 - tw / 2 - 36, 60
        c.rect(x0, y0, x0 + tw + 72, y0 + size + 44, INK)
        c.text(W / 2, y0 + 20, title, size, PAPER, anchor="ma", bold=True)
        if sub:
            c.text(W / 2, y0 + size + 62, sub, 30, ACCENT, anchor="ma", bold=True)
    return c
