# Engine reference

What the renderer understands. Stages 03 and 04 use only these words. A character's own expressions and poses are in its cast sheet (`library/cast/<name>.md`).

## Cameras (from the room file)
| Cam | Shows | Seats |
|---|---|---|
| `A` | close-up of the left seat | `left` |
| `B` | close-up of the right seat | `right` |
| `C` | wide two-shot, table between | `left`, `right` |
| `D` | laptop screen insert | none; `hand: hover` adds the left character's hand |

Seat order comes from the cast: the first character listed sits left, the second sits right. Cameras never move or zoom.

## shots.md format
```
## 17                         block id, same as script.md
theo: eyes=open, mouth=smile, hands=knees, head=down   starting state per character
phone: lit                    scene prop
at 0.6: theo.head=level       a change, seconds from block start
at 1.4: phone=off
```
- Unlisted keys fall back to the character's default face.
- `at` times are from the block start. Speech starts after the block's `pause` (0.3 s unless the script says otherwise); the timeline has the exact `speech_start`.
- Several changes on one `at` line, separated by commas.

## Keys
| Key | Values | Notes |
|---|---|---|
| `<who>.eyes` | per cast sheet | `one_open`, `camera` where the sheet allows |
| `<who>.brows` | `neutral`, `raised`, `knit` | |
| `<who>.mouth` | `rest`, `smile`, `flat`, `open` | the speaker's mouth is driven by the voice; this is the resting shape |
| `<who>.head` | `level`, `tilt`, `lean`, `down` | |
| `<who>.hands` | per cast sheet | |
| `<who>.blink` | `1`, `0` | a forced blink; natural blinks happen anyway |
| `phone` | `lit`, `off` | the phone on the table lights in the accent colour |
| `hand` | `hover` | camera D only |
| `text`, `text2` | any text | centred on-screen lines (closing cards); appear when set |
| `fade` | `out` | picture and sound fade to black over 1 s from that time |

## What the render adds on its own
- Captions from the script's `say`, with the speaker tag, while the line is spoken.
- `caption` / `caption2` from the script for silent beats.
- Mouth movement for the speaker, from the voice clip's loudness.
- Natural blinks every 3 to 6 s, a slow breath, and the boiling line.
- The label from `video.md`, top right.
- Sound effects named in the script's `sfx`.
