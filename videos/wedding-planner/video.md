# The Wedding Planner Who Can't Commit

slug: wedding-planner
cast: founder_interview
room: loft_office
label: Fictional sketch
opening: block=02, at=0.6, hold=2.5, title=The Wedding Planner Who Can't Commit, sub=a fictional sketch

## Characters
theo: Theo, the guest.
dana: Dana, the interviewer.

## Voices
Clips dropped into `stages/02-voice/input/<block>.mp3` (or .wav) are used first. Local text-to-speech fills any block without a clip.
theo: provider=elevenlabs, name=Andre Rene, voice=GogJbMCDT0Viv4cU3N4s, model=eleven_multilingual_v2, stability=0.6, style=0.1, length=1.12, licence=Andre Rene is a smooth, textured younger male voice that feels genuinely human ElevenLabs account
dana: provider=elevenlabs, name=Sarah, voice=EXAVITQu4vr4xnSDxMaL, model=eleven_multilingual_v2, stability=0.7, style=0.0, length=1.02..1.15, licence=ElevenLabs premade voice under the account plan

Local fallback (used only if the key is missing): theo model=en_US-joe-medium, dana model=en_US-ljspeech-high.
