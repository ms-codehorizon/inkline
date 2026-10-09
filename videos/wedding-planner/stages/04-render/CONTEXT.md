# Stage 04: Render

**Job:** draw every frame from the shot list and voice timing, add captions, label and sound, and export the video.

## Inputs

| Source | File/Location | Why |
|---|---|---|
| Shot list | `../03-storyboard/output/shots.md` | What to draw |
| Timing and voice | `../02-voice/output/timeline.json`, `voice.wav` | Sync and audio |
| Style | `../../../../_config/style.md` | Captions, label, sound |

## Process

1. From the factory root run `python3 engine/render.py <slug>` (add `--cut short` for the short cut).
2. Check a frame sheet from the start, middle and end before watching.
3. Watch the whole video once with sound and once muted.

## Audit

- [ ] Mouths move only for the speaker, in sync
- [ ] Captions readable at phone size, never covering a face
- [ ] The label from `video.md` visible throughout
- [ ] Chime lands on "Four" and on the ending

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Full video | `output/<slug>.mp4` | 1920x1080 MP4 |
| Short cut | `output/<slug>-short.mp4` | 1920x1080 MP4 |

## Completion

Ask the author to watch it. STOP.
