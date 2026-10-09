# Stage 01: Script

**Job:** turn the approved dialogue into `script.md`, the block format every later stage reads.

## Inputs

| Source | File/Location | Why |
|---|---|---|
| Dialogue | `input/dialogue.md`: plain `Name: line` dialogue with stage directions in parentheses (see `../../../../reference/writing-for-inkline.md`) | The words |
| Cast sheet | `../../../../library/cast/<cast>.md` (cast named in `../../video.md`) | Allowed expressions and poses |

## Process

1. Copy every line word for word. Never rewrite a joke without asking.
   The writer gives no timings, cameras or expressions. You set them: camera by who speaks (A for the left seat, B for the right, C for both, D for the laptop), `pause` and `hold` from the stage directions and the rhythm of the exchange, a silent beat for each stage direction that needs time on screen, and expressions from the cast sheet.
2. One block per line or silent beat, in order:

```
## 17
cam: A
who: theo
say: Four. One finished while we were meditating.
how: "Four" gentle and corrective, pause, then the rest unhurried
before: glances down at the phone, then back up
after: serene smile, slow blink
sfx: chime
cut: keep
```

3. Fields:

| Field | Meaning |
|---|---|
| `cam` | `A` Theo close-up, `B` Dana close-up, `C` wide two-shot, `D` laptop screen |
| `who` | `theo`, `dana`, or `-` for a silent beat |
| `say` | the line, word for word |
| `how` | delivery, for the voice stage |
| `tts` | optional spelling for the voice only, when a word is mispronounced (captions still use `say`) |
| `voice` | per-line voice overrides, e.g. `stability=0.3, style=0.7, speed=0.95` |
| `context` | a sentence the voice model hears before the line to set the tone; never spoken or shown |
| `before` / `during` / `after` | face and body, using `cast.md` words in backticks |
| `pause` / `hold` | seconds of silence before / after the line (defaults 0.3 / 0.5) |
| `beat` + `action` | length and content of a silent beat |
| `sfx` | `chime` at block start, or `chime@2.4` seconds in |
| `caption` | a caption-band line for a silent beat (no speaker tag) |
| `text`, `text2` | centred on-screen lines (closing cards); the storyboard sets when each appears |
| `cut` | `keep` or `optional` (dropped from the short cut) |

## Later edits to the dialogue

Do not redo this stage. `python3 engine/sync.py <slug>` updates `script.md` from the edited `dialogue.md` and keeps all existing direction. New blocks arrive with only `cam`, `who`, `say`: add `how`, `before`, `after`, `pause`, `hold` to those blocks only, and revisit the block just before them if its `hold` or `after` was written as an ending.

## Audit

- [ ] Every approved line is present, words unchanged, in order
- [ ] Every block has `cam` and `who`; silent beats have `beat`
- [ ] Expressions use words from the cast sheet
- [ ] No em dashes

## Outputs

| Artifact | Location | Format |
|---|---|---|
| Script | `output/script.md` | Block format above |

## Completion

Tell the author the script is ready to read. STOP.
