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

## Series + analytics lessons (2026-11-03 review)
- The page is now ONE identity: physics simulations, as a numbered series called **"One rule."**
  Next day number = last Day in HISTORY.md + 1. The kicker on the video reads `ONE RULE  ·  DAY N`
  and the caption's title line starts with `Day N:` (e.g. `Day 2: <title>`).
- Sims beat "what if" explainers 3–7x on reach (owner paused the "what if" pipeline on 2026-11-03). Followers are the weak spot (~1 per 1,500 views), so
  every reel must make the series obvious (kicker, end card) to give people a reason to follow.
- Motion must start on frame 1 — no waiting/latch/static intro. Galton's quiet first second = 41% skip.
- Aim for ≤ 25 s unless the story genuinely needs more; 45 s reels died (68% skip).

## Reference reels from the owner — learn principles, NEVER copy
The owner sends other creators' reels as references only. Never reuse their concept, mechanism, layout,
look, branding or sound; borrow only the underlying craft principle, applied to our own original idea.
Full list with notes: `REFERENCES.md`. Principles so far:
- **A visible cause.** The viewer should see the one thing that makes the rule happen (a machine, a
  contact, a trigger) so every event reads instantly without text.
- **Progress you can read at a glance.** Make each stage/generation visibly different (in our theme:
  amber shade or brightness tiers, never a rainbow) so growth is legible even with the sound off.
- **Rhythm in the sound.** Make the key events happen in pulses (driven by the physics: a rotation, a
  period, a cycle), so the ASMR gets a beat-like groove. Give the key event a deeper "thump" layer
  under the glassy detail. Still no music.
- **A payoff that breaks the frame.** The ending should release built-up tension in a way that changes
  the scene itself (something gives way, escapes, collapses, flips, goes silent), not just a counter stopping.
- **Brand on screen all the time.** Keep a small, tasteful `@whatiffun` mark visible throughout (not only
  on the end card), placed where Instagram's UI won't cover it, so reposts and screenshots carry the name.
- **The rule in six words or fewer, from frame 1.** A short bold label beats a sentence. Put the full
  explanation in the caption, not on screen.
- **Let the viewer play.** Where the physics allows, build in a prediction moment: freeze for ~1.5 s
  just before the outcome with a clear numbered or lettered choice on screen ("Which one is left? 1–6"),
  then reveal. The caption asks the same question, so comments are a single number. This also drives
  rewatches (people go back to check).
- **One hero to follow.** Mark a single object (a brighter, gold-white one among the amber) so the eye has
  something to track through the chaos, and make its fate part of the payoff.
- **Tension right before the payoff.** A short beat that signals "it's about to happen" (things slowing,
  a sound swelling, a readout nearing its limit) right before the key moment. Motion still starts on frame 1.
- **A big final number is a payoff in itself.** Show the live counter and land on a satisfying final
  value, but never put that number in the title or caption.

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
6. Schedule ONE Metricool post (blogId 7560268) to BOTH Instagram and YouTube Shorts:
   providers [{"network":"instagram"},{"network":"youtube"}], autoPublish true, timezone Asia/Calcutta,
   19:30 IST the same day, media = the raw GitHub URL, text = the caption.
   instagramData {type: "REEL", showReelOnFeed: true}.
   youtubeData {title: "Day N: <title>" (≤ 100 chars, no hashtags), type: "short", privacy: "public",
   madeForKids: false, category: "SCIENCE_TECHNOLOGY", tags: 8–12 plain keywords for the concept}.
7. Send the owner the video file and the caption.

`src/` has the full code of every past reel — reuse the rendering/audio helpers rather than starting over.
