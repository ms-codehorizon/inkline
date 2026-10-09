# Stage 03: Storyboard

**Job:** turn every block's before / say / after into exact camera, pose and expression changes, then draw a still of each.

## Inputs

| Source | File/Location | Why |
|---|---|---|
| Script | `../01-script/output/script.md` | Beats and actions |
| Timing | `../02-voice/output/timeline.json` | When things happen |
| Cast sheet and style | `../../../../library/cast/<cast>.md`, `../../../../_config/style.md` | Allowed values and look |
| Engine vocabulary | `../../../../reference/engine.md` | What the renderer understands |

## Process

1. From the factory root run `python3 engine/shots.py <slug>`. It writes `output/shots.md` from the script's `before` / `during` / `after` / `action` prose: one block per script block, the starting state and timed changes (seconds from the block start), with `on "phrase"` changes placed where the phrase is spoken.
2. Run `python3 engine/stills.py <slug>` to draw one still per block plus `output/contact.png`.
3. Look at every still. If an expression is wrong, fix the prose in `script.md` and re-run both commands; `shots.md` is generated and gets overwritten. Anything shots.py could not read is printed with a `?`.
4. Use only vocabulary from `reference/engine.md` and the cast sheet. If a beat needs something new, list it for the author instead of inventing it.

## Audit

- [ ] Every script block has a shots block
- [ ] Every change uses engine vocabulary
- [ ] Stills checked: faces readable, nothing under the caption band

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Shot list | `output/shots.md` | Block format |
| Stills | `output/stills/NN.png`, `output/contact.png` | PNG |

## Completion

Show the author the contact sheet. STOP.
