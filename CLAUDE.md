# Inkline (L1)

Turns a reviewed script into a captioned, voiced, animated video in our own ink-on-paper line style. One folder per video under `videos/`, one shared engine, one growing library of characters and rooms.

## What to Load

| Resource | When | Why |
|---|---|---|
| `CONTEXT.md` | Always | Purpose and layout |
| `videos/{slug}/video.md` | Always | This video's cast, room and voices |
| `videos/{slug}/stages/{current}/CONTEXT.md` | Always | The stage contract |
| Previous stage `output/` (text files only) | Always | The stage input |
| `library/cast/{name}.md` | Stages 01, 02, 03 | Who the characters are, allowed expressions and poses |
| `_config/style.md` | Stages 03, 04, 05 | Look, motion, captions, sound |
| `reference/engine.md` | Stages 03, 04 | Vocabulary the renderer understands |

## What NOT to Load

| Resource | Why |
|---|---|
| `engine/*.py`, `library/**/*.py` | The factory. Read only when changing the engine or adding a character or room |
| Other videos under `videos/` | Not this job |
| All stage CONTEXT.md files at once | Only the active stage matters |
| Audio, video and image files | Binary. Listen or look, do not load |
| Any outside animation kit | Not ours. Nothing here is copied from one |

## Stage Progression (per video)

1. `01-script` - dialogue -> `script.md`
2. `02-voice` - `script.md` + voice clips -> joined track + `timeline.json`
3. `03-storyboard` - script + timeline -> `shots.md` + stills
4. `04-render` - shots + voice -> MP4 with captions
5. `05-post` - video -> thumbnail + post text

## How to Run

Start a video: `python3 engine/new.py <slug> --title "..." --cast <name> --room <name>`
Then read `videos/<slug>/stages/{current}/CONTEXT.md` and carry out its contract.
Stages 02 to 04 are commands (`voice.py`, `shots.py` + `stills.py`, `render.py`); an agent only checks their output.
Dialogue edited after stage 01: `python3 engine/sync.py <slug>` updates `script.md` (new lines arrive without acting; direct only those blocks), then voice, stills, render again.
STOP after each stage so the author can review and edit the output. The next stage reads the edited output.

## House Rules

- Plain, simple words. No em dashes anywhere.
- Every character is invented. Never draw or describe one like a real person.
- Every video carries a small "Fictional sketch" label.
- A new character or room is a new file in `library/`, never a change to an existing one that other videos use.
