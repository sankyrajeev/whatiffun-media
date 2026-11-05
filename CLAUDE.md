# whatiffun daily reel — playbook

This repo hosts the videos for the Instagram page **@whatiffun** (public raw links are what Metricool
posts from) and the code + rules for making them. Each daily run makes ONE brand-new reel and schedules it.

## THE BAR: experimental and new, never generic (owner, 2026-11-04)
The owner's gold standard is the **1,000 double pendulums** reel ("experimental, new and nice — keep it
like that"; also the best performer: 5,187 IG plays, 65% watched). The others (doubling marbles,
metronome sync, Chladni sand, Galton board, bouncing ball) "seemed too generic".

What made the pendulums work, and what every reel needs:
1. **A deep, counterintuitive truth about the real world**, shown rather than explained (there:
   chaos — a difference too small to measure decides everything). Not a toy or a game mechanic.
2. **Many copies of one system with a near-invisible difference**, so the idea becomes a visual event
   (1,000 overlapping pendulums = one line, then a fan, then a spectrum).
3. **A deceptive calm start that transforms**: it looks simple and ordered, then blooms into
   something nobody expected. Motion from frame 1, but the "turn" is the hook that holds people.
4. **A twist on top** that plays with time or expectation (there: everything rewinds exactly back to one
   line — and the loop ends where it began).
5. **Precise, elegant instrumentation**: live readouts like `Δ 0.000001°` and `t 07.20s`, minimal serif
   type, a cool premium look. The numbers make it feel like a real experiment.
6. **Not a format already common on sim pages.**

Banned (famous demos / common formats, even with our styling): metronome sync, Newton's cradle,
pendulum waves, Galton/plinko boards, Chladni/cymatics, double pendulums again, "ball bounces in a circle
and grows/splits/escapes", doubling/multiplying-marble counters, colour battles, marble races, sand/fluid
pours, domino runs, orbit/solar-system builds, Brazil-nut shaking, Lissajous/harmonograph drawings.

**Originality check before building:** write 5 candidate concepts in one line each and score each 1–5 on
"have I seen this on a sim page?" (1 = never), "is there a real counterintuitive truth?" and "is there a
transformation + twist?". Build only the best, and only if it scores 1 on the first question. Log the
rejected candidates in HISTORY.md's notes so later runs don't retry them.

## What performs (owner feedback, keep doing this)
- The 1,000-double-pendulums butterfly-effect reel is the model (see THE BAR). A simple rule or setup is
  still the hook ("One rule."), but the payoff must be a real, surprising truth, not a counter going up.
- Owner said "too generic / think outside the box" about a pure pretty-pattern piece (Chladni sand).
  Prefer a surprising rule + an emergent, unscripted ending over a calm visual.
- ASMR: tactile, physically driven sound (every collision a real event, stereo-panned by x), no music.
- Colour (owner, 2026-11-05: "no rules, just keep the background theme same"): the BACKGROUND is
  always the same warm near-black (#0f0d0b-ish radial vignette) with the same cream text
  (0.96,0.92,0.84), fonts, kicker and end card, so the page looks like one series. Everything ON it
  (objects, trails, accents) uses whatever colours make that video's idea read best — a spectrum like
  the pendulums, a single hue, anything. No colour rules beyond the background.
- Different from the many generic "satisfying ball" pages. No stock music.

## Series + analytics lessons (2026-11-03 review)
- The page is now ONE identity: physics simulations, as a numbered series called **"One rule."**
  Two reels a day (13:00 and 19:30 IST), numbered per reel: next number = highest number in HISTORY.md + 1.
  The kicker on the video reads `ONE RULE  ·  NO. N` and the caption's title line starts with `No. N:`
  (e.g. `No. 3: <title>`). Never write "#N" (Instagram would read it as a hashtag).
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
- **Progress you can read at a glance.** Make each stage/generation visibly different (colour,
  brightness, size) so growth is legible even with the sound off.
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
- **One hero to follow.** Mark a single object (brighter or differently coloured than the rest) so the eye has
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
0. `git pull` first: the other daily slot may have pushed a reel since you cloned.
1. Pick a concept NOT in `HISTORY.md` that passes THE BAR's originality check. Real physics (pymunk, numpy RK4, particle methods...), seeded
   so it's deterministic. Tune the sim headless first (print counts/timings), then render previews.
2. Render with skia-python (`pip install --break-system-packages skia-python pymunk scipy`): draw a few
   full-size preview frames at the busiest moments and LOOK at them before the full render.
3. Pipe raw RGBA frames into ffmpeg; synthesize audio in numpy from the sim's own events; mux with -c:v copy.
4. Copy the mp4 to `reels/YYYY-MM-DD-<slug>.mp4`, the code to `src/YYYY-MM-DD-<slug>/`, append to
   `HISTORY.md`, commit and push to `main`.
5. Check `https://raw.githubusercontent.com/sankyrajeev/whatiffun-media/main/reels/<file>` returns 200.
6. Schedule ONE Metricool post (blogId 7560268) to BOTH Instagram and YouTube Shorts:
   providers [{"network":"instagram"},{"network":"youtube"}], autoPublish true, timezone Asia/Calcutta,
   at the post time your task prompt gives (13:00 or 19:30 IST, same day), media = the raw GitHub URL,
   text = the caption.
   instagramData {type: "REEL", showReelOnFeed: true}.
   youtubeData {title: "No. N: <title>" (≤ 100 chars, no hashtags), type: "short", privacy: "public",
   madeForKids: false, category: "SCIENCE_TECHNOLOGY", tags: 8–12 plain keywords for the concept}.
7. Send the owner the video file and the caption.

`src/` has the full code of every past reel — reuse the rendering/audio helpers rather than starting over.
