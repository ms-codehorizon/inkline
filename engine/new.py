"""Start a new video: python3 engine/new.py <slug> --title "..." --cast <name> --room <name>

Copies the stage contracts from _templates/video/, writes video.md, and lists what to do next.
"""
import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("--title", required=True)
ap.add_argument("--cast", required=True, help="name of a library/cast/<name>.py")
ap.add_argument("--room", required=True, help="name of a library/rooms/<name>.py")
a = ap.parse_args()

video = ROOT / "videos" / a.slug
if video.exists():
    sys.exit(f"{video} already exists")
for kind, name in (("cast", a.cast), ("rooms", a.room)):
    if not (ROOT / "library" / kind / f"{name}.py").exists():
        sys.exit(f"no library/{kind}/{name}.py. Add it first, with a .md sheet beside it.")

shutil.copytree(ROOT / "_templates/video/stages", video / "stages")
for st in sorted((video / "stages").iterdir()):
    (st / "output").mkdir(exist_ok=True)
    (st / "output" / ".gitkeep").touch()
(video / "stages/02-voice/input").mkdir(exist_ok=True)

import re
sheet = (ROOT / "library/cast" / f"{a.cast}.md").read_text()
chars = re.findall(r"^## (\w+) - (.*)$", sheet, re.M)
char_lines = "\n".join(f"{k.lower()}: {k}, {d}." for k, d in chars) or "name: One line about them."
voice_lines = "\n".join(f"{k.lower()}: model=en_US-joe-medium, length=1.05, gap=0.35, licence=CC0" for k, _ in chars) or "name: model=..., length=1.0, gap=0.3, licence=..."
# reuse the voices of the latest video with the same cast, so a series keeps its voices
for other in sorted((ROOT / "videos").glob("*/video.md"), key=lambda p: p.stat().st_mtime, reverse=True):
    txt = other.read_text()
    if f"cast: {a.cast}" in txt and "## Voices" in txt:
        block = txt.split("## Voices", 1)[1].split("\n## ", 1)[0].strip()
        voice_lines = block.split("\n", 1)[1].strip() if block.startswith("Clips dropped") else block
        break
(video / "video.md").write_text(f"""# {a.title}

slug: {a.slug}
cast: {a.cast}
room: {a.room}
label: Fictional sketch

## Characters
{char_lines}

## Voices
Clips dropped into `stages/02-voice/input/<block>.mp3` (or .wav) are used first. Local text-to-speech fills any block without a clip.
{voice_lines}
""")
print(f"""Created videos/{a.slug}/

Next:
1. Check videos/{a.slug}/video.md: the voices were copied from the latest video with this cast, and
   the title must use straight quotes. Add an opening: line for a title card if you want one.
2. Drop the dialogue in videos/{a.slug}/stages/01-script/input/dialogue.md.
3. Ask an agent: "run stage 01 for videos/{a.slug}".
4. python3 engine/voice.py {a.slug}, then shots.py, stills.py, render.py, thumb.py (see README).
5. Add the video to the table in CONTEXT.md.""")
