# whatiffun daily reel — playbook

This repo hosts the videos for the Instagram page **@whatiffun** (public raw links are what Metricool
posts from) and the code + rules for making them. Each daily run makes ONE brand-new reel and schedules it.

## What performs (owner feedback, keep doing this)
- Rule-based, real-physics hooks: "every time X happens, Y doubles", a rule that runs away and then
  breaks itself. The 1,000-double-pendulums butterfly-effect reel hit 5k views; doubling marbles and the
  Galton board landed well.
- Owner said "too generic / think outside the box" about a pure pretty-pattern piece (Chladni sand).
  Prefer a surprising rule + an emergent, unscripted ending over a calm visual.
- ASMR: tactile, physically driven sound (every collision a real event, stereo-panned by x), no music.
- ONE color theme: amber/gold/honey on warm near-black (#0f0d0b-ish), cream text (0.96,0.92,0.84),
  amber accent (0.88,0.64,0.30). Brass and glass materials.
- Different from the many generic "satisfying ball" pages. No neon rainbow, no stock music.

## Format (must)
- 1080x1920, 30 fps, H.264 yuv420p + AAC, 20–30 s, loops (crossfade the last ~0.6 s back to frame 0).
- Text safe area: keep key text inside y 180–1500 and x 100–980 (Instagram UI covers the edges/bottom).
- Top: small kicker in Inter SemiBold caps with letter-spacing; headline in Instrument Serif (+ italic
  second line). Live readouts in JetBrains Mono. Fonts are in `fonts/` (Inter is at
  /usr/share/fonts/opentype/inter/ in the workspace).
- End card: dark rounded card, "Follow" / "@whatiffun" (italic, amber) / "for more".
- File must be < 95 MB (GitHub limit). Re-encode with -crf 21 -maxrate 14M if larger.

## Caption (must)
Title line, blank line, a short punchy description that sets up the rule and asks a question that
invites comments, then exactly 5 hashtags, the last one `#whatiffun`. No "oddly satisfying" clichés.

Use the vidIQ connector for the title line (owner's request): draft your own title, then call
`vidiq_generate_titles` (type "short", numTitles 6, pass your title + a plain description of the video,
and the last few titles from HISTORY.md as previousTitles) and `vidiq_score_title` on your draft.
Pick the highest-scoring title that doesn't spoil the ending or the number the caption asks viewers to
guess; strip any hashtags from it (hashtags only go in the final 5-tag line). Note the score in HISTORY.md.

## Pipeline
1. Pick a concept NOT in `HISTORY.md`. Real physics (pymunk, numpy RK4, particle methods...), seeded
   so it's deterministic. Tune the sim headless first (print counts/timings), then render previews.
2. Render with skia-python (`pip install --break-system-packages skia-python pymunk scipy`): draw a few
   full-size preview frames at the busiest moments and LOOK at them before the full render.
3. Pipe raw RGBA frames into ffmpeg; synthesize audio in numpy from the sim's own events; mux with -c:v copy.
4. Copy the mp4 to `reels/YYYY-MM-DD-<slug>.mp4`, the code to `src/YYYY-MM-DD-<slug>/`, append to
   `HISTORY.md`, commit and push to `main`.
5. Check `https://raw.githubusercontent.com/sankyrajeev/whatiffun-media/main/reels/<file>` returns 200.
6. Schedule with the Metricool connector: blogId 7560268, network instagram, instagramData type REEL,
   showReelOnFeed true, autoPublish true, timezone Asia/Calcutta, at 19:30 IST the same day.
7. Send the owner the video file and the caption.

`src/` has the full code of every past reel — reuse the rendering/audio helpers rather than starting over.
