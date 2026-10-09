"""Bring script.md in line with an edited dialogue.md: python3 engine/sync.py <slug> [--dry]

Walks input/dialogue.md and output/script.md side by side (by position, with a
text check) and rewrites script.md so it says what the dialogue says:

  unchanged line  block kept exactly, directions and voice settings included
  edited line     block kept, only `say` replaced (`tts` dropped); warns when
                  more than a third of the words changed, in case the pairing is wrong
  new line        bare block added (camera from the speaker, no acting yet)
  removed line    block removed and listed
  new direction   a silent beat block, only next to new lines; directions next
                  to lines that already exist are assumed to be directed already
  (On screen: "A" Then: "B")   at the end: closing card text on the last beat block

Blocks are renumbered and `opening: block=` in video.md follows the title block.
Then run voice.py, stills.py, render.py as usual; only new or changed lines are synthesised.
"""
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import script as S

ROOT = Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) != 1:
    sys.exit(__doc__.split("\n", 1)[0])
VIDEO = ROOT / "videos" / args[0]
DIALOGUE = VIDEO / "stages/01-script/input/dialogue.md"
SCRIPT = VIDEO / "stages/01-script/output/script.md"
for p in (DIALOGUE, SCRIPT):
    if not p.exists():
        sys.exit(f"missing {p.relative_to(ROOT)}" + ("" if p is DIALOGUE else " (run stage 01 once first; sync only updates a script that exists)"))

QUOTES = {"‘": "'", "’": "'", "“": '"', "”": '"'}


def straight(s):
    for a, b in QUOTES.items():
        s = s.replace(a, b)
    return s.strip()


def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", straight(s).lower())
    return " ".join(s.split())


def characters():
    """{key: Name} from the ## Characters section of video.md, in order."""
    out, active = {}, False
    for line in (VIDEO / "video.md").read_text().splitlines():
        if line.startswith("## "):
            active = line[3:].strip().lower() == "characters"
            continue
        m = re.match(r"^([a-z_]+):\s*([^,.]+)", line)
        if active and m:
            out[m.group(1)] = m.group(2).strip()
    return out


CHARS = characters()
if not CHARS:
    sys.exit("video.md has no ## Characters section")
BY_NAME = {v.lower(): k for k, v in CHARS.items()} | {k: k for k in CHARS}
CAM = dict(zip(CHARS, "AB"))  # first character sits left (A), second right (B)


def read_dialogue():
    """[('say', who, text) | ('dir', text)], title line skipped."""
    items = []
    for raw in DIALOGUE.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^([A-Za-z][\w ]*?):\s*(.+)$", line)
        if m and m.group(1).strip().lower() in BY_NAME:
            items.append(("say", BY_NAME[m.group(1).strip().lower()], straight(m.group(2))))
        elif line.startswith("(") and line.endswith(")"):
            items.append(("dir", straight(line[1:-1])))
        elif not items:
            continue  # title line
        else:
            print(f"  ? skipped (not 'Name: line' or a (direction)): {line[:60]}")
    return items


def write_blocks(blocks, header):
    out = [header.rstrip(), ""]
    for b in blocks:
        out.append(f"## {b['id']}")
        out += [f"{k}: {v}" for k, v in b.items() if k != "id"]
        out.append("")
    return "\n".join(out)


items = read_dialogue()
old = S.load(SCRIPT)
header = SCRIPT.read_text().split("\n## ", 1)[0]
spoken_old = [i for i, b in enumerate(old) if b.get("who", "-") != "-"]
say_new = [i for i, it in enumerate(items) if it[0] == "say"]

# align spoken dialogue lines with spoken script blocks
sm = difflib.SequenceMatcher(None, [norm(items[i][2]) for i in say_new], [norm(old[j]["say"]) for j in spoken_old], autojunk=False)
pair = {}  # dialogue item index -> old block index (kept or edited)
for tag, a1, a2, b1, b2 in sm.get_opcodes():
    if tag == "equal":
        for k in range(a2 - a1):
            pair[say_new[a1 + k]] = spoken_old[b1 + k]
    elif tag == "replace":
        for k in range(min(a2 - a1, b2 - b1)):
            pair[say_new[a1 + k]] = spoken_old[b1 + k]
paired_old = set(pair.values())

kept = edited = added = 0
removed, warnings, fresh = [], [], []  # fresh: blocks created this run
out_blocks, cursor, pending_dirs = [], 0, []


def flush_to(j):
    """Emit old blocks before index j: silent beats stay, unpaired spoken blocks are removed."""
    global cursor
    while cursor < j:
        b = old[cursor]
        if b.get("who", "-") == "-":
            out_blocks.append(dict(b))
        elif cursor not in paired_old:
            removed.append(f"{b['id']} {b['who']}: {b['say']}")
        cursor += 1


def beat(text):
    who = next((k for k, v in CHARS.items() if v.lower() in text.lower()), None)
    b = {"id": "?", "cam": CAM.get(who, "C"), "who": "-", "beat": "2.0", "action": text}
    if re.search(r"chime|phone (rings|buzz)", text, re.I):
        b["sfx"] = "chime"
    b["cut"] = "keep"
    return b


for i, it in enumerate(items):
    if it[0] == "dir":
        pending_dirs.append(it[1])
        continue
    _, who, text = it
    if i in pair:
        j = pair[i]
        flush_to(j)
        b = dict(old[j])
        if b.get("who") != who:
            warnings.append(f"block {b['id']}: speaker changed {b['who']} -> {who}, check the pairing")
            b["who"], b["cam"] = who, CAM.get(who, b.get("cam"))
        if norm(b["say"]) == norm(text):
            kept += 1
        else:
            ratio = difflib.SequenceMatcher(None, norm(b["say"]).split(), norm(text).split()).ratio()
            if 1 - ratio > 1 / 3:
                warnings.append(f"block {b['id']}: more than a third of the words changed, check it is the same line\n      was: {b['say']}\n      now: {text}")
            b["say"] = text
            b.pop("tts", None)
            edited += 1
        pending_dirs.clear()  # directions beside existing lines were directed in stage 01 already
        out_blocks.append(b)
        cursor = j + 1
    else:
        for d in pending_dirs:
            out_blocks.append(beat(d))
            fresh.append(out_blocks[-1])
            added += 1
        pending_dirs.clear()
        out_blocks.append({"id": "?", "cam": CAM.get(who, "A"), "who": who, "say": text, "cut": "keep"})
        fresh.append(out_blocks[-1])
        added += 1
ON_SCREEN = re.compile(r'^on screen:\s*"([^"]+)"(?:\s*then:\s*"([^"]+)")?\s*$', re.I)
cards = [m for m in map(ON_SCREEN.match, pending_dirs) if m]
pending_dirs = [d for d in pending_dirs if not ON_SCREEN.match(d)]
if out_blocks and out_blocks[-1] in fresh:  # closing directions after a new last line
    for d in pending_dirs:
        out_blocks.append(beat(d))
        fresh.append(out_blocks[-1])
        added += 1
flush_to(len(old))  # old trailing beats (the closing shot) stay last
if cards:  # closing card: text on the last silent block, or a new one
    text, text2 = cards[-1].group(1), cards[-1].group(2)
    last = out_blocks[-1] if out_blocks and out_blocks[-1].get("who") == "-" else None
    if last is None:
        last = {"id": "?", "cam": "C", "who": "-", "beat": "5", "action": "both hold. Fade to black from 4.0 s", "cut": "keep"}
        out_blocks.append(last)
        fresh.append(last)
        added += 1
    if last.get("text") != text or last.get("text2", None) != text2:
        need = 5.0 if text2 else 4.0
        if S.num(last, "beat", 0) < need:
            old_beat, old_fade = last.get("beat", "0"), re.search(r"from ([\d.]+)\s*s", last.get("action", ""))
            last["beat"] = f"{need:g}"
            if old_fade:
                last["action"] = last["action"].replace(f"from {old_fade.group(1)} s", f"from {need - 1.0:g} s")
        rest = {k: last.pop(k) for k in ("action", "cut") if k in last}
        last["text"] = text
        if text2:
            last["text2"] = text2
        else:
            last.pop("text2", None)
        last.update(rest)
        if last not in fresh:
            edited += 1
            print(f"  ~ closing card on block {last['id']}: {text}" + (f" / {text2}" if text2 else ""))

# renumber everything; old trailing silent beats (the closing shot) keep their place at the end
width = max(2, len(str(len(out_blocks))))
mapping = {}
for n, b in enumerate(out_blocks, 1):
    new_id = str(n).zfill(width)
    if b["id"] != "?":
        mapping[b["id"]] = new_id
    b["id"] = new_id
renumbered = {k: v for k, v in mapping.items() if k != v}

header = re.sub(r"\d+ blocks:[^\n]*", f"{len(out_blocks)} blocks: {sum(1 for b in out_blocks if b.get('who') != '-')} spoken lines, {sum(1 for b in out_blocks if b.get('who') == '-')} silent beats.", header)
text = write_blocks(out_blocks, header)

print(f"{'would keep' if DRY else 'kept'} {kept}, changed {edited}, added {added}, removed {len(removed)}")
for r in removed:
    print(f"  - removed {r}")
for b in fresh:
    print(f"  + new {b['id']} {b['who']}: {b.get('say') or '(' + b['action'] + ')'}")
for w in warnings:
    print(f"  ! {w}")
if renumbered:
    print("  renumbered: " + ", ".join(f"{k}->{v}" for k, v in renumbered.items()))
    if (VIDEO / "stages/03-storyboard/output/shots.md").exists():
        print("  ! stages/03-storyboard/output/shots.md uses the old numbers; redo stage 03")
    for p in (VIDEO / "stages/02-voice/input").glob("*.*"):
        if p.stem in renumbered:
            print(f"  ! imported clip stages/02-voice/input/{p.name} now belongs to block {renumbered[p.stem]}; rename it")

if DRY:
    sys.exit(0)
SCRIPT.write_text(text)
manifest = VIDEO / "video.md"
m = re.search(r"^opening:.*?block=(\d+)", manifest.read_text(), re.M)
if m and m.group(1) in renumbered:
    manifest.write_text(manifest.read_text().replace(f"block={m.group(1)}", f"block={renumbered[m.group(1)]}", 1))
    print(f"  video.md opening block={m.group(1)} -> {renumbered[m.group(1)]}")
if added or edited or removed:
    print(f"\nNext: python3 engine/voice.py {args[0]}" + ("\nNew blocks have no acting yet (how/before/after). Ask an agent to direct them once the words are right." if added else ""))
else:
    print("script.md already matches dialogue.md")
