"""Stage 04: draw every frame, add captions, label and sound, export the MP4.

python3 engine/render.py <slug> [--cut short] [--start S --end E] [--out file.mp4] [--jobs N]
Reads  script.md, timeline(.json|-short.json), voice(.wav|-short.wav), shots.md, video.md, _config/style.md
Writes stages/04-render/output/<slug>.mp4 (or <slug>-short.mp4)
"""
import argparse
import math
import random
import subprocess
import sys
import tempfile
import wave
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import frame as F  # noqa: E402
import script as S  # noqa: E402

FPS = 24
RATE = 22050
BOIL_HZ = 6
CAPTION_LEAD, CAPTION_TAIL = 0.15, 0.35

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("--cut", default="full")
ap.add_argument("--start", type=float, default=0.0)
ap.add_argument("--end", type=float, default=None)
ap.add_argument("--out", default=None)
ap.add_argument("--jobs", type=int, default=None)
ap.add_argument("--frames", default=None, help="also dump every Nth frame as PNG to this folder, e.g. --frames /tmp/f:48")
ap.add_argument("--part", type=int, default=None, help="render only part K of --parts (video only), for machines with a time limit per command")
ap.add_argument("--parts", type=int, default=4)
ap.add_argument("--join", action="store_true", help="join the rendered parts and add the sound")
ap.add_argument("--no-preview", action="store_true", help="skip the 720p preview written beside the master")
args = ap.parse_args()

V = F.Video(args.slug, cut="short" if args.cut == "short" else None)
sfx = "-short" if args.cut == "short" else ""
VOICE = V.dir / "stages/02-voice/output" / f"voice{sfx}.wav"
OUT = Path(args.out) if args.out else V.dir / "stages/04-render/output" / f"{args.slug}{sfx}.mp4"
OUT.parent.mkdir(parents=True, exist_ok=True)
OPEN = {}
if V.manifest.get("opening"):
    OPEN = S.kv(V.manifest["opening"])
INTRO = float(OPEN.get("hold", 0)) if OPEN else 0.0
DUR = V.timeline["duration"] + INTRO  # script time = t - INTRO
END = min(args.end, DUR) if args.end else DUR


# ---- sound ----------------------------------------------------------------
def read_wav(p):
    with wave.open(str(p)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def write_wav(p, a):
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def chime():
    n = int(0.9 * RATE)
    t = np.arange(n) / RATE
    env = np.exp(-t * 4.2)
    a = 0.6 * np.sin(2 * np.pi * 1568 * t) * env
    b = 0.5 * np.sin(2 * np.pi * 2093 * np.clip(t - 0.11, 0, None)) * np.exp(-np.clip(t - 0.11, 0, None) * 4.2) * (t > 0.11)
    return 0.35 * (a + b)


def room_tone(n, seed=1):
    rng = np.random.default_rng(seed)
    white = rng.normal(0, 1, n).astype(np.float32)
    brown = np.cumsum(white)
    brown -= np.convolve(brown, np.ones(2000) / 2000, mode="same")
    brown /= np.abs(brown).max() + 1e-9
    return 0.012 * brown


voice = np.concatenate([np.zeros(int(INTRO * RATE), np.float32), read_wav(VOICE)])
mix = np.zeros(int(DUR * RATE) + RATE, np.float32)
mix[:len(voice)] += voice
mix += room_tone(len(mix))
for e in V.timeline["blocks"]:
    for s in e.get("sfx", []):
        if s["name"] == "chime":
            at = int((s["at"] + INTRO) * RATE)
            c = chime()
            mix[at:at + len(c)] += c[:len(mix) - at]
# fade the sound out with the picture at the very end
fade_n = int(1.0 * RATE)
mix[int(DUR * RATE) - fade_n:int(DUR * RATE)] *= np.linspace(1, 0, fade_n)
mix = mix[:int(DUR * RATE)]
peak = float(np.abs(mix).max()) or 1.0
if peak > 0.85:
    mix *= 0.85 / peak  # keep about 1.4 dB of headroom, no clipping

# mouth drive: loudness of the voice track per frame, normalised per spoken block
env = np.zeros(int(math.ceil(DUR * FPS)) + 1, np.float32)
hop = RATE // FPS
for i in range(len(env)):
    seg = voice[i * hop:(i + 1) * hop]
    env[i] = math.sqrt(float(np.mean(seg ** 2))) if len(seg) else 0.0
talk = np.zeros_like(env)
for e in V.timeline["blocks"]:
    if "say" not in e:
        continue
    a, b = int((e["speech_start"] + INTRO) * FPS), int((e["speech_end"] + INTRO) * FPS) + 1
    peak = env[a:b].max() or 1.0
    talk[a:b] = np.clip(env[a:b] / peak * 1.4, 0, 1)
# smooth a little so the mouth does not flicker
talk = np.convolve(talk, [0.25, 0.5, 0.25], mode="same")


# ---- blinks ---------------------------------------------------------------
def blink_times(seed, dur):
    rng = random.Random(seed)
    t, out = rng.uniform(1.0, 3.0), []
    while t < dur:
        out.append(t)
        t += rng.uniform(3.0, 6.0)
    return out


BLINKS = {who: blink_times(i * 7 + 3, DUR) for i, who in enumerate(V.people)}


def blinking(who, t):
    for b in BLINKS[who]:
        if b <= t < b + 3 / FPS:
            return True
    return False


# ---- frames ---------------------------------------------------------------
def block_at(t):
    for e in V.timeline["blocks"]:
        if e["start"] <= t < e["end"]:
            return e
    return V.timeline["blocks"][-1]


_CARD = None


def render_frame(i):
    t = i / FPS
    if t < INTRO:
        global _CARD
        c = F.draw_title_card(V, OPEN["block"], float(OPEN.get("at", 0)), OPEN.get("title", ""), OPEN.get("sub", ""), boil=int(t * BOIL_HZ))
        img = c.finish()
        if t < 0.5:  # fade in from black
            from PIL import Image
            img = Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, t / 0.5)
        return i, img.tobytes()
    t -= INTRO
    e = block_at(t)
    b = V.blocks[e["id"]]
    shot = V.shots.get(e["id"], {})
    tb = t - e["start"]
    flat = F.state_at(shot, tb)
    spoken = "say" in e
    speaking = b["who"] if spoken and e["speech_start"] <= t <= e["speech_end"] else None
    caption = None
    if spoken and e["speech_start"] - CAPTION_LEAD <= t <= e["speech_end"] + CAPTION_TAIL:
        caption = (b["who"], b["say"])
    elif not spoken and b.get("caption"):
        caption = (None, b["caption"])
    blinks = {who for who in V.people if blinking(who, t) or flat.get(f"{who}.blink") == "1"}
    # a slow breath, out of phase for the two characters
    breath = {who: 1.5 * math.sin(2 * math.pi * t / 4.2 + k * 1.3) for k, who in enumerate(V.people)}
    for who in V.people:
        flat.setdefault(f"{who}.breath", 0)
    c = F.draw_frame(V, b["cam"], flat, t=tb, speaking=speaking, talk=float(talk[i]) if speaking else 0.0,
                     caption=caption, boil=int(t * BOIL_HZ), blink=blinks, breath=breath)
    img = c.finish()
    # fades: shots may set fade=out at a time; the very end always fades
    fade_at = None
    for when, k, v in shot.get("changes", []):
        if k == "fade" and v == "out":
            fade_at = when
    k = 1.0
    if fade_at is not None and tb >= fade_at:
        k = max(0.0, 1.0 - (tb - fade_at) / 1.0)
    if t > DUR - INTRO - 0.6:
        k = min(k, max(0.0, (DUR - INTRO - t) / 0.6))
    if k < 1.0:
        from PIL import Image
        img = Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, k)
    return i, img.tobytes()


def preview(master):
    """A small 720p copy beside the master, for sharing and chat uploads. Always made from the master just written."""
    out = master.with_name(master.stem + "-preview-720p.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(master), "-c:v", "libx264", "-crf", "26", "-preset", "fast",
                    "-vf", "scale=1280:-2", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out)], check=True)
    print("wrote", out)


def join():
    parts_dir = OUT.parent / "parts"
    import re as _re
    parts = sorted(p for p in parts_dir.glob(f"{OUT.stem}-*.mp4") if _re.fullmatch(rf"{_re.escape(OUT.stem)}-\d\d\.mp4", p.name))
    if len(parts) != args.parts:
        sys.exit(f"found {len(parts)} parts, expected {args.parts}")
    lst = Path(tempfile.gettempdir()) / "parts.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    write_wav(Path(tempfile.gettempdir()) / "mix.wav", mix)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-i", str(Path(tempfile.gettempdir()) / "mix.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", str(OUT)], check=True)
    print("wrote", OUT)
    if not args.no_preview:
        preview(OUT)


if __name__ == "__main__":
    if args.join:
        join()
        sys.exit()
    first, last = int(args.start * FPS), int(END * FPS)
    if args.part is not None:
        total = int(DUR * FPS)
        per = math.ceil(total / args.parts)
        first, last = args.part * per, min(total, (args.part + 1) * per)
        OUT = OUT.parent / "parts" / f"{OUT.stem}-{args.part:02d}.mp4"
        OUT.parent.mkdir(parents=True, exist_ok=True)
    n = last - first
    print(f"{args.slug} ({args.cut}): {n} frames, {END - args.start:.1f} s, {DUR:.1f} s total")
    tmp = Path(tempfile.gettempdir())
    write_wav(tmp / "mix.wav", mix[int(args.start * RATE):int(END * RATE)])
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{F.W}x{F.H}", "-r", str(FPS), "-i", "-"]
    if args.part is None:
        cmd += ["-i", str(tmp / "mix.wav"), "-c:a", "aac", "-b:a", "160k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)]
    dump = None
    if args.frames:
        d, every = args.frames.split(":")
        dump = (Path(d), int(every))
        dump[0].mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(args.jobs) as pool:
        for k, (i, raw) in enumerate(pool.imap(render_frame, range(first, last), chunksize=4)):
            proc.stdin.write(raw)
            if dump and i % dump[1] == 0:
                from PIL import Image
                Image.frombytes("RGB", (F.W, F.H), raw).save(dump[0] / f"{i:05d}.png")
            if k % (FPS * 5) == 0:
                print(f"  {i / FPS:6.1f} s", flush=True)
    proc.stdin.close()
    proc.wait()
    print("wrote", OUT)
    if args.part is None and not args.no_preview and args.start == 0 and args.end is None:
        preview(OUT)
