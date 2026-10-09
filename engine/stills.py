"""Stage 03: one still per block plus a contact sheet.

python3 engine/stills.py <slug>
Reads  script.md, timeline.json, shots.md
Writes stages/03-storyboard/output/stills/NN.png and contact.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import frame as F  # noqa: E402
import script as S  # noqa: E402
from ink import font  # noqa: E402

slug = sys.argv[1]
v = F.Video(slug)
out = v.dir / "stages/03-storyboard/output/stills"
out.mkdir(parents=True, exist_ok=True)
thumbs = []
for e in v.timeline["blocks"]:
    b = v.blocks[e["id"]]
    shot = v.shots.get(e["id"])
    if shot is None:
        print(f"block {e['id']}: no shots block, skipped")
        continue
    spoken = "say" in e
    # draw the most telling moment: mid-speech, or 70% into a silent beat (after its action)
    t = ((e["speech_start"] + e["speech_end"]) / 2 - e["start"]) if spoken else (e["end"] - e["start"]) * 0.7
    flat = F.state_at(shot, t)
    caption = (b["who"], b["say"]) if spoken else None
    c = F.draw_frame(v, b["cam"], flat, t=t, speaking=b.get("who") if spoken else None, talk=0.35 if spoken else 0.0, caption=caption)
    img = c.finish()
    img.save(out / f"{e['id']}.png")
    thumbs.append((e["id"], b["cam"], img))
    print(f"{e['id']} cam {b['cam']} t={t:.1f}s")

# contact sheet: 4 across
tw, th = 480, 270
cols = 4
rows = (len(thumbs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + 28)), (255, 255, 255))
d = ImageDraw.Draw(sheet)
f = font(18, True)
for i, (bid, cam, img) in enumerate(thumbs):
    x, y = (i % cols) * tw, (i // cols) * (th + 28)
    sheet.paste(img.resize((tw, th)), (x, y + 28))
    d.text((x + 8, y + 5), f"{bid}  cam {cam}", font=f, fill=(40, 40, 40))
sheet.save(v.dir / "stages/03-storyboard/output/contact.png")
print("contact sheet:", v.dir / "stages/03-storyboard/output/contact.png")
