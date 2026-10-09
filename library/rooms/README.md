# Room library

One file per setting. Each exposes `CAMERAS`: camera letter -> `{draw, seats}` where `draw(canvas, lit=False)` draws the room from that camera and `seats` says where each character sits (x, y, flip). Rooms are drawn in soft ink; props near the characters in full ink.
