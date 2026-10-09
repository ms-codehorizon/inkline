# Style - the look, motion and sound

Our own look: dark ink drawn by hand on warm paper, like a magazine cartoon. One red accent.

## Frame
- 1920 x 1080, 24 fps, H.264 + AAC.
- Cameras cut, they never move or zoom.

## Palette (nothing else)
| Name | Hex | Use |
|---|---|---|
| paper | `#F3EDE0` | background |
| ink | `#2A2622` | characters, props in focus, caption band |
| soft | `#A39A8B` | background lines (the "out of focus" room) |
| wash | `#E6DECD` | flat fills: chair, floor shadow, window light |
| accent | `#C8463C` | one thing per frame at most: phone light, speaker tag, highlight |

## Line
- Every stroke wobbles a little and tapers at both ends, like a pen.
- Lines "boil": the wobble redraws 6 times a second, so a still frame still feels alive.
- Characters: thick lines. Room: thin soft lines. That is our depth of field.
- No gradients, no shadows, no outlines around text.

## Faces and bodies
- Blinks every 3 to 6 seconds, 3 frames long, for both characters.
- Only the speaker's mouth moves, driven by their own voice clip. The listener's mouth stays still.
- A slow breath (1 px rise and fall over 4 s) so held shots are never frozen.

## Captions and label
- Bottom band in ink, text in paper, Inter or a clean sans fallback.
- Speaker name small and uppercase in accent above the line.
- The `label` from `video.md` (usually "Fictional sketch") in soft ink, top right, the whole video.

## Sound
- Quiet room tone under everything. No music.
- Sound effects only where the script asks (`sfx:`). Available: `chime` (a soft phone chime).
