"""Stage 05: a thumbnail from any block, with an optional title drawn on the paper.

python3 engine/thumb.py <slug> --block 17 --title "The AI Founder Interview" [--sub "a fictional sketch"] [--at 1.2] [--out file.png]
No caption band, no label clutter: the frame, the title, and the small sketch label.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import frame as F  # noqa: E402
from ink import ACCENT, INK, PAPER, W  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("--block", required=True)
ap.add_argument("--title", default="")
ap.add_argument("--sub", default="")
ap.add_argument("--at", type=float, default=None, help="seconds into the block (default: mid-speech)")
ap.add_argument("--out", default=None)
a = ap.parse_args()

v = F.Video(a.slug)
e = next(x for x in v.timeline["blocks"] if x["id"] == a.block)
t = a.at if a.at is not None else ((e["speech_start"] + e["speech_end"]) / 2 - e["start"] if "say" in e else (e["end"] - e["start"]) * 0.7)
c = F.draw_title_card(v, a.block, t, a.title, a.sub)
out = Path(a.out) if a.out else v.dir / "stages/05-post/output/thumbnail.png"
out.parent.mkdir(parents=True, exist_ok=True)
c.finish().save(out)
print("wrote", out)
