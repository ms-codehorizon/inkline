"""Look test for a cast in a room: one still per close-up camera.

python3 engine/preview.py <cast> <room> <out_dir>   e.g. founder_interview loft_office /tmp/look
Cast characters are seated in order: first character in the left seat, second in the right seat.
"""
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "engine")]
from ink import Canvas  # noqa: E402

cast_name, room_name, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
cast = importlib.import_module(f"library.cast.{cast_name}")
room = importlib.import_module(f"library.rooms.{room_name}")
out.mkdir(parents=True, exist_ok=True)
people = list(cast.CHARACTERS.items())
for cam, spec in room.CAMERAS.items():
    for seat, (x, y, flip) in spec["seats"].items():
        key, draw = people[0] if seat == "left" else people[1]
        c = Canvas(boil=0)
        spec["draw"](c)
        with c.at(x, y, flip=flip):
            draw(c, cast.DEFAULT_FACE.get(key, {}))
        room.label(c)
        c.finish().save(out / f"camera-{cam.lower()}-{key}.png")
        print("saved", out / f"camera-{cam.lower()}-{key}.png")
