# Inkline - Purpose (L1)

One repeatable job: a script in, a finished animated video out, with human review between stages. Reused for every video; only `videos/<slug>/` is new each time.

## Layout
| Path | What | Reuse |
|---|---|---|
| `engine/` | Drawing toolkit, voice, stills, render, post | Every video |
| `library/cast/<name>.py` + `.md` | A set of characters: drawing code + character sheet | Any video that casts them |
| `library/rooms/<name>.py` | A setting, drawn from each camera | Any video set there |
| `_config/style.md` | House look, motion, captions, sound | Every video |
| `_templates/video/` | Stage contracts copied into each new video | Every video |
| `videos/<slug>/` | One video: `video.md` manifest + five stages | That video only |

## A new video needs
1. Plain dialogue from a writer in `stages/01-script/input/dialogue.md`, turned into `script.md` by an agent (stage 01).
2. Voices named in `video.md` (ElevenLabs ids, or local text-to-speech); clips dropped into `stages/02-voice/input/` win.
3. A cast and a room from the library, or a new one added to the library first.

## Videos
| Slug | Title | Cast | Room | Status |
|---|---|---|---|---|
| `founder-interview` | The AI Founder Interview | `founder_interview` (Theo, Dana) | `loft_office` | Final: 1:52 with opening card, thumbnail and post |
| `wedding-planner` | The Wedding Planner Who Can't Commit | `founder_interview` (Theo as a wedding planner, Dana) | `loft_office` | Rendered; thumbnail and post pending |

## Entry point
`python3 engine/new.py <slug> ...`, drop the dialogue, agent runs stage 01, then `voice.py`, `shots.py`, `stills.py`, `render.py`, `thumb.py`. Dialogue edits later: `sync.py`, then the same commands. README has the walkthrough.
