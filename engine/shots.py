"""Stage 03, first half: write shots.md from the script. python3 engine/shots.py <slug>

Reads  script.md (before/during/after/action prose), timeline.json, the voice clips
Writes stages/03-storyboard/output/shots.md (then run stills.py to draw it)

How the prose becomes keys:
  before:  part `value` pairs become the block's starting state
  during:  part `value` on "phrase" lands where the phrase is spoken (word times from
           the voice clip); without a phrase, changes are spread across the line
  after:   lands just after the line ends; "then" steps 0.6 s later; "blink" is a forced blink
  action:  (silent beats) phases split on "then", spread across the beat
  Each block starts from the character's default face; a look that should continue
  across a cut is restated in the next block's before:.
Anything it cannot read is printed, and the line is kept as a comment in shots.md.
Re-running overwrites shots.md; hand edits there belong in the script instead.
"""
import difflib
import hashlib
import json
import re
import sys
import unicodedata
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import frame as F  # noqa: E402
import script as S  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
if len(sys.argv) != 2:
    sys.exit(__doc__.split("\n", 1)[0])
slug = sys.argv[1]
V = F.Video(slug)
OUT = V.dir / "stages/03-storyboard/output"
OUT.mkdir(parents=True, exist_ok=True)
CLIPS = V.dir / "stages/02-voice/output/clips"
WORDS = OUT / "words.json"

PARTS = ("eyes", "brows", "mouth", "head", "hands")
PEOPLE = V.people
NAMES = {p: p for p in PEOPLE}
for line in (V.dir / "video.md").read_text().splitlines():
    m = re.match(r"^([a-z_]+):\s*([^,.]+)", line)
    if m and m.group(1) in PEOPLE:
        NAMES[m.group(2).strip().lower()] = m.group(1)
DEFAULT_HANDS = {p: ("knees" if i == 0 else "pen_ready") for i, p in enumerate(PEOPLE)}
notes = []


# ---------- word times from the clips ----------
_asr = None
_cache = json.loads(WORDS.read_text()) if WORDS.exists() else {}


def clip_words(block_id):
    """[(word, start_s, end_s)] for a block's clip, cached by clip content."""
    global _asr
    wav = CLIPS / f"{block_id}.wav"
    if not wav.exists():
        return None
    key = hashlib.md5(wav.read_bytes()).hexdigest()
    if _cache.get(block_id, {}).get("key") == key:
        return _cache[block_id]["words"]
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    if _asr is None:
        _asr = WhisperModel("small.en", device="cpu", compute_type="int8")
    with wave.open(str(wav)) as w:
        rate, n = w.getframerate(), w.getnframes()
        a = np.frombuffer(w.readframes(n), np.int16).astype(np.float32) / 32768
    x = np.interp(np.arange(0, len(a), rate / 16000), np.arange(len(a)), a).astype(np.float32)
    pad = 0.2
    segs, _ = _asr.transcribe(np.pad(x, int(pad * 16000)), language="en", beam_size=5, word_timestamps=True)
    words = [(w.word.strip(), round(max(0.0, w.start - pad), 2), round(max(0.0, w.end - pad), 2)) for s in segs for w in s.words]
    _cache[block_id] = {"key": key, "words": words}
    WORDS.write_text(json.dumps(_cache, indent=1))
    return words


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "twenty thirty forty fifty sixty seventy eighty ninety".split()


def norm(s):
    """one word, comparable: lower, no accents or punctuation, digits as words"""
    s = unicodedata.normalize("NFKD", s.lower())
    s = re.sub(r"\b(\d{1,2})\b", lambda m: ONES[int(m.group(1))] if int(m.group(1)) < 20 else TENS[int(m.group(1)) // 10 - 2] + ONES[int(m.group(1)) % 10] * (int(m.group(1)) % 10 > 0), s)
    return re.sub(r"[^a-z0-9]", "", s)


def phrase_time(block, phrase, speech_len):
    """Seconds into the speech where the phrase starts; falls back to its position in the text."""
    target = [norm(w) for w in phrase.split()]
    target = [t for t in target if t]
    words = clip_words(block["id"])
    if words and target:
        seq = [norm(w) for w, _, _ in words]
        close = lambda a, b: a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.8  # fiance ~ fiancee
        for i in range(len(seq) - len(target) + 1):
            if all(close(seq[i + k], target[k]) for k in range(len(target))):
                return words[i][1]
        for i, w in enumerate(seq):  # first word only, tolerant of a transcription slip
            if close(w, target[0]) and (len(target) == 1 or (i + 1 < len(seq) and close(seq[i + 1], target[1]))):
                return words[i][1]
    say = block.get("say", "")
    pos = say.lower().find(phrase.lower())
    if pos < 0:
        notes.append(f"{block['id']}: phrase \"{phrase}\" not in the line; placed at the middle")
        return speech_len * 0.5
    notes.append(f"{block['id']}: phrase \"{phrase}\" not found in the clip; estimated")
    return speech_len * pos / max(1, len(say))


# ---------- prose -> keys ----------
def parse_clause(text, who, last_part=None):
    """One clause of direction prose -> (who, [(key, value)], extras, last_part)."""
    keys, extras = [], {}
    low = text.lower()
    for name, p in NAMES.items():
        if re.search(rf"\b{re.escape(name)}\b", low):
            who = p
    for m in re.finditer(r"(?:\b(eyes|brows|mouth|head|hands)\b[^`]{0,12})?`([a-z_]+)`", low):
        part, val = m.group(1), m.group(2)
        if part is None:
            part = last_part
        if part is None:
            continue
        keys.append((f"{who}.{part}", val))
        last_part = part
    if "blink" in low and not re.search(r"no blink|without blink", low):
        extras["blink"] = who
    if re.search(r"into the (camera|lens)", low):
        keys.append((f"{who}.eyes", "camera"))
    if re.search(r"phone.*(lights|lit|chime)|lights up", low):
        extras["phone"] = "lit"
    if re.search(r"phone.*(off|dark|dims)", low):
        extras["phone"] = "off"
    m = re.search(r"fade.*?([\d.]+)\s*s", low)
    if m:
        extras["fade"] = float(m.group(1))
    if re.search(r"hand (hovers|`hover`)|hands? `hover`", low):
        extras["hand"] = "hover"
    return who, keys, extras, last_part


def clauses(text):
    """Split prose on commas and semicolons, but keep parentheses and quotes together."""
    out, depth, cur, q = [], 0, "", False
    for ch in text:
        if ch == '"':
            q = not q
        depth += (ch == "(") - (ch == ")")
        if ch in ",;" and depth == 0 and not q:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [c.strip() for c in out if c.strip()]


def steps(text):
    """Split a clause on 'then' into ordered sub-steps."""
    return [s.strip() for s in re.split(r"\b[Tt]hen\b", text) if s.strip()]


# ---------- build ----------
state = {p: {} for p in PEOPLE}
lines = ["# Written by engine/shots.py from script.md. Edit the script and re-run rather than editing here.", ""]
tl = {e["id"]: e for e in V.timeline["blocks"]}

for b in V.blocks.values():
    cam = b.get("cam", "C")
    seats = V.room.CAMERAS.get(cam, {}).get("seats", {})
    present = [p for p in PEOPLE if V.seat_of(p) in seats]
    who = b.get("who", "-")
    speaker = who if who != "-" else (present[0] if present else PEOPLE[0])
    e = tl.get(b["id"], {})
    start = e.get("start", 0.0)
    sp0 = e.get("speech_start", start) - start
    sp1 = e.get("speech_end", e.get("end", start)) - start
    length = e.get("end", start) - start
    changes, props = [], {}
    state = {p: {} for p in PEOPLE}  # each block starts from the default face

    def apply(at, keys, extras):
        for k, v in keys:
            p, part = k.split(".")
            if at <= 0.0:
                state[p][part] = v
            else:
                changes.append((round(at, 2), k, v))
        if "blink" in extras:
            changes.extend([(round(max(at, 0.1), 2), f"{extras['blink']}.blink", "1"), (round(max(at, 0.1) + 0.4, 2), f"{extras['blink']}.blink", "0")])
        if "phone" in extras:
            if at <= 0.0:
                props["phone"] = extras["phone"]
            else:
                changes.append((round(at, 2), "phone", extras["phone"]))
        if "hand" in extras:
            props["hand"] = extras["hand"]
        if "fade" in extras:
            changes.append((extras["fade"], "fade", "out"))

    def direct(field, default_at):
        """Apply one prose field. default_at(i, n) gives the time of the i-th untimed clause."""
        cl = clauses(b.get(field, ""))
        untimed, w, part, prev = 0, speaker, None, 0.0
        for c in cl:
            m = re.search(r'\bon\s+"([^"]+)"', c)
            if m:
                at, text = sp0 + phrase_time(b, m.group(1), sp1 - sp0), c[: m.start()] + c[m.end():]
            elif re.match(r"(?i)then\b", c):  # ", then `open`" continues the previous clause
                at, text = prev + 0.6, c
            else:
                at, text = default_at(untimed, len(cl)), c
                untimed += 1
            for i, st in enumerate(steps(text)):
                w, keys, extras, part = parse_clause(st, w, part)
                apply(at + 0.6 * i, keys, extras)
                prev = at + 0.6 * i

    direct("before", lambda i, n: 0.0)
    direct("during", lambda i, n: sp0 + (sp1 - sp0) * (i + 1) / (n + 1))
    direct("after", lambda i, n: sp1 + 0.15)

    # action: silent beats (and extra business on spoken blocks)
    if who == "-":
        phases = steps(b.get("action", ""))
        for i, ph in enumerate(phases):
            at = 0.0 if i == 0 else min(1.2 * i, max(0.0, length - 0.8))
            w, part = speaker, None
            for c in clauses(ph):
                w, keys, extras, part = parse_clause(c, w, part)
                apply(at, keys, extras)
        # closing cards
        shown = re.findall(r"at ([\d.]+)\s*s", b.get("action", ""))
        if b.get("text"):
            changes.append((float(shown[0]) if shown else 0.3, "text", b["text"]))
        if b.get("text2"):
            changes.append((float(shown[1]) if len(shown) > 1 else 1.8, "text2", b["text2"]))
    elif b.get("text"):
        changes.append((round(sp1 + 0.3, 2), "text", b["text"]))
        if b.get("text2"):
            changes.append((round(sp1 + 1.8, 2), "text2", b["text2"]))

    # chime: the phone lights with the sound unless the script says otherwise
    for name, at in S.sfx(b):
        if name == "chime" and "phone" not in props and not any(k == "phone" for _, k, _ in changes):
            if at <= 0.0:
                props["phone"] = "lit"
            else:
                changes.append((at, "phone", "lit"))
            changes.append((round(at + 1.4, 2), "phone", "off"))

    lines.append(f"## {b['id']}")
    for p in present:
        st = dict(state[p])
        st.setdefault("eyes", "open")
        st.setdefault("mouth", V.cast.DEFAULT_FACE.get(p, {}).get("mouth", "rest"))
        st.setdefault("hands", DEFAULT_HANDS[p])
        order = [k for k in PARTS if k in st] + [k for k in st if k not in PARTS]
        lines.append(f"{p}: " + ", ".join(f"{k}={st[k]}" for k in order))
    for k, v in props.items():
        lines.append(f"{k}: {v}")
    by_time = {}
    for at, k, v in sorted(changes, key=lambda c: c[0]):
        by_time.setdefault(at, []).append(f"{k}={v}")
        if "." in k and k.split(".")[1] != "blink":
            p, part = k.split(".")
            state[p][part] = v
    for at, kvs in by_time.items():
        lines.append(f"at {at:g}: " + ", ".join(kvs))
    # blink keys should not persist
    lines.append("")

(OUT / "shots.md").write_text("\n".join(lines))
print(f"wrote stages/03-storyboard/output/shots.md: {len(V.blocks)} blocks")
for n in notes:
    print(f"  ? {n}")
print(f"Next: python3 engine/stills.py {slug}  (then look at output/contact.png)")
