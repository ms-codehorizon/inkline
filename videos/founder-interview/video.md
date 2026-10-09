# The AI Founder Interview

slug: founder-interview
cast: founder_interview
room: loft_office
label: Fictional sketch
opening: block=17, at=0.4, hold=2.5, title=The AI Founder Interview, sub=a fictional sketch

## Characters
theo: Theo, the founder. Calm, sincere, cannot code.
dana: Dana, the interviewer. Dry, patient journalist.

## Voices
Clips dropped into `stages/02-voice/input/<block>.mp3` (or .wav) are used first. Then ElevenLabs if `provider=elevenlabs`, else local text-to-speech.
theo: provider=elevenlabs, name=Author (own voice), voice=4P46np8k8CBLNSKevUpQ, model=eleven_multilingual_v2, stability=0.6, style=0.1, length=1.12, licence=the author's own voice on their ElevenLabs account
dana: provider=elevenlabs, name=Sarah, voice=EXAVITQu4vr4xnSDxMaL, model=eleven_multilingual_v2, stability=0.7, style=0.0, length=1.02..1.15, licence=ElevenLabs premade voice under the account plan

Local fallback (used only if the key is missing): theo model=en_US-joe-medium, dana model=en_US-ljspeech-high.

## Cameras (from the room)
A: Theo close-up. B: Dana close-up. C: wide two-shot. D: laptop screen.
