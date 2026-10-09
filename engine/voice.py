"""Stage 02: voice every line, join the track, write the timing.

Run from the factory root:  python3 engine/voice.py <slug>
Reads  videos/<slug>/stages/01-script/output/script.md and videos/<slug>/video.md
       videos/<slug>/stages/02-voice/input/<block>.(mp3|wav|m4a): imported clips, used first
Writes videos/<slug>/stages/02-voice/output/{clips/, voice.wav, voice-short.wav, timeline.json, timeline-short.json, voices.md}
"""
import json
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import re
import unicodedata

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import script as S

ROOT = Path(__file__).resolve().parent.parent
if len(sys.argv) < 2:
    sys.exit("usage: python3 engine/voice.py <slug>")
VIDEO = ROOT / "videos" / sys.argv[1]
if not VIDEO.exists():
    sys.exit(f"no such video: {VIDEO}")
IN = VIDEO / "stages/02-voice/input"
OUT = VIDEO / "stages/02-voice/output"
VOICES = Path(__file__).resolve().parent / "voices"
RATE = 22050
DEF_PAUSE, DEF_HOLD = 0.3, 0.5


def read_wav(p):
    with wave.open(str(p)) as w:
        assert w.getframerate() == RATE, w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a


def write_wav(p, a):
    a = np.clip(a, -1, 1)
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def trim(a, thresh=0.005, pad=0.12):
    idx = np.where(np.abs(a) > thresh)[0]
    if not len(idx):
        return a
    p = int(pad * RATE)
    return a[max(0, idx[0] - p): idx[-1] + p]


def level(a, target_db=-20.0):
    rms = np.sqrt(np.mean(a ** 2)) or 1e-9
    return a * (10 ** (target_db / 20) / rms)


def length_for(spec, i, n):
    lo, _, hi = spec.partition("..")
    lo = float(lo)
    return lo if not hi else lo + (float(hi) - lo) * (i / max(1, n - 1))


def imported(block_id, out):
    """A clip the author dropped in input/, converted to our format. None if there is none."""
    for ext in ("wav", "mp3", "m4a", "ogg", "flac"):
        src = IN / f"{block_id}.{ext}"
        if src.exists():
            raw = Path(tempfile.gettempdir()) / f"fi-{block_id}.import.wav"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", str(RATE), str(raw)], check=True)
            a = level(trim(read_wav(raw)))
            raw.unlink()
            write_wav(out, a)
            return a, src.name
    return None, None


def env(name):
    """Read a secret from .env at the factory root (never committed)."""
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name:
                return v.strip()
    return os.environ.get(name)


def eleven(text, cfg, speed, out, over=None):
    """ElevenLabs text-to-speech. Cached by content so reruns cost nothing."""
    import hashlib
    import urllib.request
    key = env("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY missing: put it in .env at the factory root")
    cfg = dict(cfg, **(over or {}))
    if over and "speed" in over:
        speed = float(over["speed"])
    settings = {"stability": float(cfg.get("stability", 0.6)), "similarity_boost": float(cfg.get("similarity", 0.8)),
                "style": float(cfg.get("style", 0.0)), "use_speaker_boost": True, "speed": round(speed, 3)}
    body = {"text": text, "model_id": cfg.get("model", "eleven_multilingual_v2"), "voice_settings": settings}
    if cfg.get("context"):
        body["previous_text"] = cfg["context"]  # heard by the model for tone, never spoken
    digest = hashlib.sha1(json.dumps([cfg["voice"], body], sort_keys=True).encode()).hexdigest()[:16]
    cache = OUT / "cache" / f"{digest}.mp3"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice']}?output_format=mp3_44100_128",
            data=json.dumps(body).encode(), headers={"xi-api-key": key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            cache.write_bytes(r.read())
    raw = Path(tempfile.gettempdir()) / f"fi-{out.stem}.el.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(cache), "-ac", "1", "-ar", str(RATE), str(raw)], check=True)
    a = level(trim(read_wav(raw)))
    raw.unlink()
    write_wav(out, a)
    return a


def synth(text, cfg, length, out):
    model = VOICES / f"{cfg['model']}.onnx"
    if not model.exists():
        sys.exit(f"Missing voice {model.name}. Run: cd engine/voices && python3 -m piper.download_voices {cfg['model']}")
    raw = Path(tempfile.gettempdir()) / f"fi-{out.stem}.raw.wav"
    subprocess.run([sys.executable, "-m", "piper", "-m", str(model), "-f", str(raw),
                    "--length-scale", f"{length:.3f}", "--sentence-silence", cfg.get("gap", "0.3")],
                   input=text.encode(), check=True, capture_output=True)
    a = level(trim(read_wav(raw)))
    raw.unlink()
    write_wav(out, a)
    return a


_ASR = None


def heard(a):
    """What a listener would hear: transcribe the clip (needs faster-whisper)."""
    global _ASR
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    if _ASR is None:
        _ASR = WhisperModel("small.en", device="cpu", compute_type="int8")
    x = np.interp(np.arange(0, len(a), RATE / 16000), np.arange(len(a)), a).astype(np.float32)
    segs, _ = _ASR.transcribe(np.pad(x, 3200), language="en", beam_size=5)
    return " ".join(s.text.strip() for s in segs)


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "twenty thirty forty fifty sixty seventy eighty ninety".split()


def number_word(n):
    """0..99 as words, the way a script writes them: 'forty six'."""
    if n < 20:
        return ONES[n]
    t, o = divmod(n, 10)
    return TENS[t - 2] + (" " + ONES[o] if o else "")


def words(s):
    """Normalise text for the listen-back compare: lower case, no punctuation,
    digits as words, British 'our' = American 'or', spaces removed so
    'short list' == 'shortlist'. Returns one string."""
    s = unicodedata.normalize("NFKD", s.lower().replace("-", " "))  # fiancé -> fiance
    s = re.sub(r"\b(\d{1,2})\b", lambda m: number_word(int(m.group(1))), s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"(?<=[a-z]{2})our", "or", s)  # favourite/colour, not four/hour
    return "".join(s.split())


def build(blocks, clips, short):
    t, timeline, parts = 0.0, [], []
    for b in blocks:
        if short and b.get("cut") == "optional":
            continue
        e = {"id": b["id"], "cam": b.get("cam"), "who": b.get("who"), "start": round(t, 3)}
        if b.get("who", "-") == "-":
            t += S.num(b, "beat", 2.0)
            parts.append(np.zeros(int(S.num(b, "beat", 2.0) * RATE), np.float32))
        else:
            a = clips[b["id"]]
            pause, hold = S.num(b, "pause", DEF_PAUSE), S.num(b, "hold", DEF_HOLD)
            e["say"] = b["say"]
            e["speech_start"] = round(t + pause, 3)
            e["speech_end"] = round(t + pause + len(a) / RATE, 3)
            parts += [np.zeros(int(pause * RATE), np.float32), a, np.zeros(int(hold * RATE), np.float32)]
            t += pause + len(a) / RATE + hold
        e["end"] = round(t, 3)
        e["sfx"] = [{"name": n, "at": round(e["start"] + at, 3)} for n, at in S.sfx(b)]
        timeline.append(e)
    return timeline, np.concatenate(parts)


def main():
    blocks = S.load(VIDEO / "stages/01-script/output/script.md")
    only = os.environ.get("ONLY")
    if only:
        blocks = [b for b in blocks if b["id"] in only.split(",")]
    cfg = S.config(VIDEO / "video.md")
    (OUT / "clips").mkdir(parents=True, exist_ok=True)
    spoken = [b for b in blocks if b.get("who", "-") != "-"]
    counts = {b["who"]: sum(1 for x in spoken if x["who"] == b["who"]) for b in spoken}
    seen = {w: 0 for w in counts}
    clips, notes = {}, []
    for b in spoken:
        who = b["who"]
        ln = length_for(cfg[who]["length"], seen[who], counts[who]) if who in cfg else 1.0
        seen[who] += 1
        a, src = imported(b["id"], OUT / "clips" / f"{b['id']}.wav")
        if a is not None:
            got = heard(a)
            ok = got is None or words(got) == words(b["say"])
            source = f"imported {src}"
        else:
            if who not in cfg:
                sys.exit(f"block {b['id']}: no clip in input/ and no voice for '{who}' in video.md")
            text = b.get("tts", b["say"])
            if cfg[who].get("provider") == "elevenlabs":
                # speed: 1.0 is normal; a 'length' of 1.12 means 12% slower, so speed = 1 / length
                speed = max(0.7, min(1.2, 1.0 / ln))
                over = S.kv(b["voice"]) if b.get("voice") else {}
                if b.get("context"):
                    over["context"] = b["context"]
                for attempt in range(2):
                    a = eleven(text, cfg[who], speed + (0.0, 0.03)[attempt], OUT / "clips" / f"{b['id']}.wav", over)
                    got = heard(a)
                    ok = got is None or words(got) == words(b["say"])
                    if ok:
                        break
                source = f"elevenlabs {cfg[who].get('name', cfg[who]['voice'])} x{speed:.2f}"
            else:
                for attempt in range(4):
                    a = synth(text, cfg[who], ln + (0.0, 0.04, -0.04, 0.08)[attempt], OUT / "clips" / f"{b['id']}.wav")
                    got = heard(a)
                    ok = got is None or words(got) == words(b["say"])
                    if ok:
                        break
                source = f"tts {cfg[who]['model']} x{ln:.2f}"
        clips[b["id"]] = a
        check = "not checked" if got is None else ("clear" if ok else f"UNCLEAR, heard: {got}")
        notes.append(f"| {b['id']} | {who} | {source} | {len(a) / RATE:.2f} s | {b['say']} | {check} |")
        print(f"{b['id']} {who:5} {len(a) / RATE:5.2f}s  {source:28.28} {check:12.40}  {b['say']}")
    for short in (False, True):
        tl, track = build(blocks, clips, short)
        sfx = "-short" if short else ""
        write_wav(OUT / f"voice{sfx}.wav", track)
        (OUT / f"timeline{sfx}.json").write_text(json.dumps({"rate": RATE, "duration": round(len(track) / RATE, 3), "blocks": tl}, indent=1))
        print(f"voice{sfx}.wav  {len(track) / RATE:.1f} s")
    lines = ["# Voices used", "", "Imported clips come from `input/`. Text-to-speech voices:", ""]
    for w, c in cfg.items():
        if c.get("provider") == "elevenlabs":
            lines.append(f"- **{w}**: ElevenLabs voice `{c.get('name', '')}` ({c['voice']}), model {c.get('model', 'eleven_multilingual_v2')}, stability {c.get('stability', 0.6)}, style {c.get('style', 0)}, length {c['length']}. Licence: {c.get('licence', 'per the ElevenLabs plan')}")
        else:
            lines.append(f"- **{w}**: `{c['model']}`, length {c['length']}, sentence gap {c.get('gap', '0.3')} s. Licence: {c.get('licence', 'CHECK')}")
    lines += ["", "| Block | Who | Source | Clip | Line | Heard |", "|---|---|---|---|---|---|"] + notes
    (OUT / "voices.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
