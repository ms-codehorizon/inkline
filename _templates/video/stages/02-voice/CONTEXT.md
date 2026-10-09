# Stage 02: Voice

**Job:** voice every line, join them into one track and record exactly when each line starts and ends.

## Inputs

| Source | File/Location | Why |
|---|---|---|
| Script (possibly edited by the author) | `../01-script/output/script.md` | Lines, delivery, beats |
| Imported clips | `input/<block>.mp3` or `.wav` (for example `17.mp3`), one per spoken block | Real voices, from ElevenLabs or a recording |
| Voice settings | `../../video.md`, section Voices | Fallback text-to-speech per character |
| Cast sheet | `../../../../library/cast/<cast>.md` | Voice direction |

## Process

1. Voices come from `## Voices` in `video.md`: ElevenLabs (key in `.env`) or local text-to-speech if there is no key. A recorded clip dropped into `input/<block>.mp3` wins over both; `script.md`'s `say` and `how` fields are the brief for whoever records it.
2. From the factory root run `python3 engine/voice.py <slug>`. Unchanged lines come from `output/cache/`, so re-runs are free.
3. Each clip is transcribed back and compared to `say`; the compare ignores digits, accents, spelling and spacing. Read the Heard column in `output/voices.md` and listen to any UNCLEAR clip before changing anything. A real mispronunciation wants a `tts:` spelling in the script; a recorded clip wants a re-record.
4. Pauses and holds come from the script, not the clips. Clips are trimmed and levelled.

## Audit

- [ ] One clip per spoken block, none missing
- [ ] Every line reads "clear" in `output/voices.md`, or the author has accepted the exception
- [ ] The two characters sound clearly different and match the cast sheet
- [ ] Any text-to-speech voice has its licence written down

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Line clips | `output/clips/NN.wav` | WAV, 22050 Hz mono |
| Joined tracks | `output/voice.wav`, `output/voice-short.wav` | WAV |
| Timing | `output/timeline.json`, `output/timeline-short.json` | start, speech_start, speech_end, end per block |
| Voice notes | `output/voices.md` | source, settings, licence, what was heard |

## Completion

Ask the author to listen to `voice.wav` from start to finish. STOP.
