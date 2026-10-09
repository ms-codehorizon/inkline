"""Read the block format used by script.md and shots.md."""
import re
from pathlib import Path


def load(path):
    blocks, cur = [], None
    for raw in Path(path).read_text().splitlines():
        line = raw.rstrip()
        m = re.match(r"^##\s+(\S+)", line)
        if m:
            cur = {"id": m.group(1)}
            blocks.append(cur)
            continue
        if cur is None or not line.strip():
            continue
        m = re.match(r"^([a-z_][a-z0-9_]*):\s*(.*)$", line)
        if m:
            cur[m.group(1)] = m.group(2).strip()
    return blocks


def num(block, key, default=0.0):
    try:
        return float(block.get(key, default))
    except ValueError:
        return default


def sfx(block):
    """'chime' -> [('chime', 0.0)], 'chime@2.4' -> [('chime', 2.4)]."""
    out = []
    for part in filter(None, (p.strip() for p in block.get("sfx", "").split(","))):
        name, _, at = part.partition("@")
        out.append((name, float(at) if at else 0.0))
    return out


def kv(text):
    """'a=1, b=two, three, c=4' -> {'a': '1', 'b': 'two, three', 'c': '4'}.
    Commas split only where the next piece starts a new key=value."""
    out = {}
    for part in re.split(r",\s*(?=[A-Za-z_][A-Za-z0-9_]*=)", text):
        k, _, v = part.strip().partition("=")
        if k:
            out[k.strip()] = v.strip()
    return out


def config(path, section="Voices"):
    """'name: k=v, k=v' lines under '## <section>' -> {name: {k: v}}."""
    out, active = {}, section is None
    for line in Path(path).read_text().splitlines():
        if line.startswith("## "):
            active = section is None or line[3:].strip().lower() == section.lower()
            continue
        m = re.match(r"^([a-z_][a-z0-9_]*):\s*(.*=.*)$", line)
        if m and active:
            out[m.group(1)] = kv(m.group(2))
    return out


def manifest(path):
    """Top-level 'key: value' lines of video.md (above the first '## ')."""
    out = {}
    for line in Path(path).read_text().splitlines():
        if line.startswith("## "):
            break
        m = re.match(r"^([a-z_][a-z0-9_]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out
