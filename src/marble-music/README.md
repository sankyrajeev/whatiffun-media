# MARBLE MUSIC — "guess the song" (owner, 2026-11-26)

Owner: "Check this page out [satisfy3dverse]. Maybe add one such video a day instead of a puzzle."
That page: one striped marble bounces down a wall of chime pads in glossy 3D; every bounce plays one note of a
melody people know; "Guess all the songs" / "Which version is the best?"; 1.8M–3.5M plays on the top reels.
Ours keeps the idea (a marble playing a melody, one note per bounce) and nothing else: our warm-dark studio look,
brass tubes / walnut blocks / amber glass / copper saucers, our typography, and ONLY public-domain melodies
(composers dead > 100 years, our own synthesised performance). Never their songs (Mario, Doraemon, Roblox, phonk),
never their white wall, layout or text.

## How it works
1. `songs.py` — the melody library. A song = sections `(bpm, family, transpose, notes)`; each section switches the
   instrument family (a new "version" every few seconds) and the tempo climbs, so it escalates.
2. `choreo.py <song>` — plans the wall: depth-first search over bounce choices so the marble, under real gravity,
   reaches a pad exactly on every note; each pad is tilted by the reflection law; no pad may sit in any part of
   the marble's flight. Writes `plan/<song>.json` and a 2D preview. (~1–3 min)
3. `strip.py plan/<song>.json ball` then `... tiles 100 24` — Blender Cycles: 36 marble sprites, and the whole wall
   as tall orthographic tiles twice (pads idle / pads lit). (~25–40 min on 2 cores)
4. `compose.py plan/<song>.json [stills t1,t2]` — films it: a 1080×1920 window follows the marble (smoothed),
   struck pads light up, sparkle at each contact, marble shadow, "GUESS / THE SONG" header, "Comment the song" CTA,
   soundtrack synthesised from the same hit list (one note per hit), loudnorm −14 LUFS. (~3 min)

Answer loop: add `{"<No.>": {"answer": "<song title>", "what": "<composer, year>"}}` to answers.json; the caption
must contain "Comment the song" so the reply bot treats it as a song reel and reveals the title 24 h later.
