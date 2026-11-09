# whatiffun reels — playbook

This repo hosts the videos for **@whatiffun** (Instagram Reels + YouTube Shorts; public raw links are what
Metricool posts from) and the code + rules for making them. Two reels a day: 13:00 and 19:30 IST.

## THE DIRECTION: calm, satisfying ASMR (owner, 2026-11-05) — this overrides everything older
The owner called the "science lesson" reels (Fermi string, stochastic resonance, metronomes, Chladni) junk:
"It needs to be ASMR videos. People watch this because they are calm and satisfying."
The three reels the owner approved are THE template — study their code in `src/2026-11-05-asmr-samples/`
(`kit.py` = shared look + sound toolkit, use it):
- **No. 5 "Every bounce splits it in two."** One big glossy sphere in a round glass bowl, zero-g; each wall
  bounce splits it into two smaller ones → ~2,000 glittering beads (purple → pink → gold), sound from deep
  thumps to a high shimmer; then gravity fades in and the glitter rains down into a golden pool.
- **No. 6 "Every note drops a new ball."** Glowing glass chimes in a tall jar; every ring drops a new ball
  from the top; the melody multiplies into a cascade; the rising pile buries the chimes until it fades.
- **No. 7 "Touch it and you stick."** Glass beads rain onto a brass pin; any bead that touches the crystal
  sticks → a frosty coral tree grows upward, each bead a soft rising glass click.

What every reel must be:
1. **ASMR first.** The sound is the product: every collision/contact is a real event in the sim with a
   crisp, pleasant, physically-matched sound (glass clicks, chimes, soft thumps), stereo-panned by x,
   level-balanced so it never gets harsh. Pitch tied to something visible (size, height, which object).
   Calm tonal palette (major pentatonic). No music, no voice.
2. **One dead-simple rule**, 2 short lines on screen from frame 1 (≤ 6 words), e.g. "Every bounce / splits
   it in two." Kicker above it: `ONE RULE`. A live count under it.
3. **Escalation into something gorgeous**: 1 → hundreds/thousands of glossy objects, colour shifting as it
   grows, building density and sound.
4. **A soft, satisfying ending**: settles, fills, buries, rains down, grows to the top — then a short hold,
   the end card, and a crossfade loop back to frame 1. A gentle resolving chord under the end card.
5. **Calm. No interruptions.** NEVER freeze the action, never put questions, choices, quizzes, countdowns
   or "which one?" prompts on screen. Nothing that breaks the flow.
6. **No explanations, no science lessons, no formulas or technical readouts** (the count is the only number).
7. **Fresh every time**: a new rule + new setting/material/arena each reel (never repeat a rule from
   HISTORY.md). Variations on the format are good (multiplying, splitting, sticking, filling, melting,
   magnetising, chain-ringing, stacking, crystallising...), but each must feel new.

## LEVEL UP (owner, 2026-11-09): "I like the direction, but it's becoming a little too simple"
Keep the calm ASMR feel, but make every reel richer. The owner's ideas — use them, never copy any page:
- **Escalation ladders.** The same satisfying action at exploding scale, in stages: 1 → 10 → 100 → 1,000 →
  10,000 (each stage ~3–5 s, the count jumping with a soft thump + chord, the scene getting denser and
  more beautiful each step). The owner loved a page doing "1 knife, 2 knives, 1,000 knives…" — the FORMAT is
  the idea; never knives or anything from that page.
- **Patterns from physics equations.** People love patterns. Balls, beads and lines driven by real equations
  that create shapes nobody drew: harmonic motion with phase offsets (a ring of straight-line sliders that
  rolls as a circle, then blooms into roses), pendulum waves, Lissajous/harmonograph traces, spirographs,
  phyllotaxis (golden-angle spirals), standing-wave grids, orbital resonances, strange-attractor ribbons,
  vortex lattices… Rainbow colour by phase or angle makes the pattern pop.
- **Gliding.** Things gliding smoothly through things: beads sliding on rails, objects passing through
  gates/rings/layers, ribbons, slices, smooth eased motion. Silky > jittery.
- **Combine two layers per reel** (a ladder + a pattern, a rule + a reveal, gliding + a twist) so it's never
  just one effect. A secret that is revealed as the count grows is ideal ("each ball only moves in a straight
  line… and yet").
Reference implementation: No. 13 `src/2026-11-10-straight-lines/render.py` (ladder 2 → 4,096, rose patterns).
Keep the rule text ≤ 6 words, the count, no questions, no lectures.

Look (fixed): the warm near-black radial background, cream text, Instrument Serif rule lines, Inter
kicker, the serif count, the small `@whatiffun` mark near the bottom, the dark end card
"Follow / @whatiffun / for more" — all exactly as `kit.py` draws them. Colours of the objects are free
(glossy glass/candy spheres with highlights and soft shadows; soft glows on events).

## Format (must)
- 1080x1920, 30 fps, H.264 yuv420p + AAC, 22–28 s total, motion and sound from frame 1.
- Keep everything inside x 100–980, y 180–1640 (Instagram UI covers the edges/bottom).
- File < 95 MB (GitHub limit). Re-encode with -crf 21 -maxrate 14M if larger.

## Caption (must)
`No. N: <title>`, blank line, one or two calm lines that set up the rule, a short "Sound on. 🎧"-style
line, blank line, exactly 5 hashtags ending with `#whatiffun` (usually #asmr #satisfying #relaxing
#physics #whatiffun). No questions needed; never "oddly satisfying" in the text.
Title: draft your own, then `vidiq_generate_titles` (type "short", numTitles 6, your title + a plain
description of the video, recent titles from HISTORY.md as previousTitles). Pick the highest-scoring one
that doesn't spoil the ending; strip hashtags from it. Log the score in HISTORY.md.

## Pipeline
0. `git pull` first (the other slot may have pushed). Check Metricool (`getScheduledPosts`, blogId 7560268,
   timezone Asia/Calcutta) — if a post is already scheduled within 45 minutes of your slot today, do
   nothing and finish (the owner may have queued one by hand).
1. Pick a new rule (not in HISTORY.md). Build the sim (pymunk / numpy, seeded, deterministic). Tune it
   headless until the arc lands: count timeline, when it peaks, when it settles, 20–25 s of action.
2. Render with skia-python via `kit.py` (`pip install --break-system-packages skia-python pymunk scipy`).
   Draw full-size preview frames at frame 1, the busiest moment and the ending, and LOOK at them; fix
   anything off (objects escaping, overlaps, text collisions, ugly colours) before the full render.
3. Pipe frames into ffmpeg (kit.Writer); build the soundtrack from the sim's own events (kit.Mix); check the
   per-second loudness stays even (no harsh peaks, no dead stretches except the intended ending); mux.
4. Save `reels/YYYY-MM-DD-<slug>.mp4` and the code in `src/YYYY-MM-DD-<slug>/`, add a HISTORY.md row,
   commit and push to main (pull --rebase and retry if rejected). Confirm the raw URL returns 200/206.
5. ONE Metricool post (blogId 7560268) to Instagram + YouTube: providers instagram + youtube,
   autoPublish true, timezone Asia/Calcutta, your slot time today, media = the raw GitHub URL,
   text = caption, instagramData {type: "REEL", showReelOnFeed: true}, youtubeData {title: "No. N: <title>"
   (≤ 100 chars, no hashtags), type: "short", privacy: "public", madeForKids: false,
   category: "SCIENCE_TECHNOLOGY", tags: 8–12 plain keywords}.
6. Send the owner the video and caption.

Numbering: next No. = highest number in HISTORY.md + 1.

## Reference reels from the owner — learn principles, NEVER copy
See `REFERENCES.md`. Never reuse another creator's concept, mechanism, layout, look or branding. Principles
worth keeping: a visible cause for the rule; growth legible at a glance; rhythmic, physically-driven sound
with a soft low thump under the glassy detail; a big final count; brand mark on screen throughout.
