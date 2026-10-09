# Inkline

An ICM video factory. A script goes in, an animated ink-on-paper video comes out, and a person checks the work between every stage.

Built to make short sketches without a video generator: the characters, the room, the captions and the motion are all drawn by code, so every video looks like it came from the same hand.

First video: *The AI Founder Interview*, a two-character sketch about shipping software before anyone has used it. Its script, shot list and settings are in `videos/founder-interview/`.

## Setup, once

```
brew install ffmpeg            # or your package manager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.10+ and ffmpeg on the PATH. Run everything below with the venv active.

## How it works

Five stages per video. Each one writes plain files you can read and edit; the next stage reads your edited version.

| Stage | In | Out | You check |
|---|---|---|---|
| 01 script | approved dialogue | `script.md`: lines, delivery, expressions, pauses | read it |
| 02 voice | `script.md` | one clip per line, joined track, `timeline.json` | listen |
| 03 storyboard | script + timeline | `shots.md` + one still per block | look at the contact sheet |
| 04 render | shots + voice | the MP4, with captions, label and sound | watch it |
| 05 post | the video | thumbnail + post text | approve |

The stage contracts live in `_templates/video/stages/` and are copied into each new video. `CLAUDE.md` says what an agent loads at each stage and what it must leave alone.

## Make a video

This is the whole process, written from a clean run of the second episode. Most of it is you at a terminal; two steps need an agent.

**1. Create the folder.**

```
python3 engine/new.py my-video --title "My Video" --cast founder_interview --room loft_office
```

Then open `videos/my-video/video.md` and check two things before going further:
- The voices. `new.py` copies them from the latest video with the same cast, which may be the wrong voice for this episode's Theo. Set `voice=` to the id you want.
- The title. Use a straight apostrophe (`Can't`, not `Can’t`); a curly one breaks the settings parser. Add an `opening:` line if you want a title card, for example `opening: block=02, at=0.6, hold=2.5, title=My Video, sub=a fictional sketch`.

**2. Drop the dialogue** in `videos/my-video/stages/01-script/input/dialogue.md`. Plain `Name: line`, directions in parentheses, an optional `(On screen: "..." Then: "...")` at the end for a closing card. The writer brief is `reference/writing-for-inkline.md`.

**3. Agent: stage 01.** Say `run stage 01 for videos/my-video`. The agent writes `stages/01-script/output/script.md`: cameras, pauses, delivery, expressions. Read it. This is the step that cannot be a command; it is the acting.

**4. Commands.** Each one prints what to run next.

```
python3 engine/voice.py my-video      # voices and timeline; listen, check voices.md
python3 engine/shots.py my-video      # storyboard keys from the script's directions
python3 engine/stills.py my-video     # one still per block; look at output/contact.png
python3 engine/render.py my-video     # the MP4 and a 720p preview; watch it
python3 engine/thumb.py my-video --block 38 --at 0.1 --title "MY TITLE" --sub "a fictional sketch"
```

`thumb.py` needs `--block` (which block's frame) and `--title`; `--at` picks the second within the block, `--out` a different file name for a second candidate.

**5. Agent: the post.** The post text is writing, so an agent drafts `stages/05-post/output/post.md` for you to edit.

**6. Commit the video folder.** Rendered MP4s and voice clips are ignored; everything else in `videos/my-video/` is tracked, including the voice cache, so a re-run does not spend credits again.

What to expect along the way:
- `voice.py` prints UNCLEAR when the transcription of a clip does not match the script. Most are the transcriber's spelling (it is tolerant of numbers, accents and British spelling already). Listen to the clip before changing anything; the fix is a `tts:` line in the script.
- `shots.py` prints a `?` when it could not place a phrase and estimated instead. Harmless unless the still looks wrong.
- Deleting a video folder deletes its voice cache. Restore it from git before re-running `voice.py` if you want the old clips back for free.

Stage 01 and the post are the only steps that need an agent. Everything else is a command, and `sync.py` (below) keeps it that way when the dialogue changes.

## Working with a writer

A writer hands in plain dialogue, `Name: line`, with stage directions in parentheses. No timings, cameras or expressions; stage 01 adds those and you review them. The one-page brief for writers is `reference/writing-for-inkline.md`.

## Change the dialogue

Edit `stages/01-script/input/dialogue.md` (change, add or remove lines, same plain format), then:

```
python3 engine/sync.py <slug>      # brings script.md in line with the dialogue
python3 engine/voice.py <slug>     # only new or changed lines are synthesised
```

`sync.py` keeps every existing block as it is, directions and voice settings included, and only replaces `say:` on edited lines. New lines become bare blocks (camera from the speaker, no acting); once the words are right, ask an agent to direct just those blocks, then run stills and render. Removed lines are listed, never dropped silently. Blocks are renumbered, so if `shots.md` already exists, redo stage 03. `--dry` shows what would change without writing.

For a one-word fix you can still edit `say:` in `script.md` directly and run `voice.py`. Make the same change in `dialogue.md`, because the dialogue is the source of truth: the next sync puts its words back.

## Voices

Per character in `video.md`: `provider=elevenlabs` with a voice id (the key goes in a local `.env` as `ELEVENLABS_API_KEY`), or nothing, which falls back to free local Piper voices. Clips dropped into `stages/02-voice/input/<block>.mp3` win over both.

Per line in `script.md`, when a word or a delivery is off:

| Field | Does |
|---|---|
| `tts:` | a different spelling for the voice only; captions keep `say:` |
| `voice:` | overrides such as `stability=0.5, style=0.3, speed=0.9` |
| `context:` | a sentence the voice model hears before the line to set the tone; never spoken or shown |

Every clip is transcribed back and compared to the script. Mismatches are listed in `stages/02-voice/output/voices.md`.

## Characters and rooms

Characters and rooms are drawing code, not images. That is what keeps every video in the same hand, and it is the one part of the factory that a description alone cannot produce: someone (you, or an agent) writes the strokes, looks at the result, and adjusts.

A cast is a pair of files in `library/cast/`:
- `<name>.py` exposes `CHARACTERS`, a dict of `name -> draw(canvas, state)` functions, each drawing that character facing right with the neck base at (0, 0), and `DEFAULT_FACE`, the resting look per character. `state` carries `eyes`, `brows`, `mouth`, `head`, `hands`, plus `talk`, `blink` and `breath`, which the renderer drives. A `hover_hand(canvas)` is optional (camera D).
- `<name>.md` is the character sheet: who they are, never-do rules, and a vocabulary table listing every value of eyes, brows, mouth, head and hands the code supports. Agents and `shots.py` check directions against this table, so it has to match the code.

A room is one file in `library/rooms/` exposing `CAMERAS`: camera letter to `{draw, seats, about}`, where `draw(canvas, lit=False)` draws the room from that angle and `seats` maps `left` and `right` to `(x, y, scale, flip)` for the characters.

Drawing uses `engine/ink.py`: `stroke`, `ellipse`, `fill`, `hatch`, `text`, `push_clip`, all with the wobble and boil applied for you. The quickest start is to copy `founder_interview.py` and `loft_office.py` and change them.

To look at a cast in a room before any video exists:

```
python3 engine/preview.py <cast> <room> /tmp/look     # one still per close-up camera
```

Never change a cast or room that a video already uses; every re-render of that video would change with it. New look, new file, and `cast:` or `room:` in the new video's `video.md` points at it.

## Layout

```
engine/      drawing toolkit (ink.py), voice, stills, render, thumbnail, new video
library/     cast/<name>.py + .md  (characters)   rooms/<name>.py  (settings)
_config/     style.md: palette, line, motion, captions, sound
_templates/  stage contracts copied into each new video
reference/   engine.md: the vocabulary shots.md may use
videos/      one folder per video: video.md + stages 01..05
```

A new character or room is a new file in `library/`. Existing ones are never changed once a video uses them.

## Not in the repo

Rendered videos, voice clips and the local voice models are regenerated from the files that are here. The `.env` with the API key never goes in.
