# whatiffun reels — playbook

This repo hosts the videos for **@whatiffun** (Instagram Reels + YouTube Shorts; public raw links are what
Metricool posts from) and the code + rules for making them. FOUR reels a day from 2026-11-13 (owner's
call): 10:00, 13:00, 15:00 and 18:00 IST (Metricool's best-time data: 10:00 is our audience's peak, 18:00 beats 19:30).

## CURRENT PLAN (2026-11-10) — read this first; it overrides older sections where they conflict
The owner: "You are free to make decisions and constantly upgrade." Decide, ship, measure, improve.
No need to ask the owner anything; report what you did.

**🔥 VIRAL (2026-11-11) — THIS OVERRIDES THE SLOT PLAN BELOW. Owner: "that pendulum video went viral.
stick to stuff like that. that was amazing."** No. 17 SPOT IT pendulums (2D, 12 s loop, 7×10 lettered grid,
one pendulum a touch longer drifting out of a diagonal wave, "Comment its letter + number", lower tick as
an audio clue): **60,753 IG plays in ~11 h, 114% avg watched (people loop it), 14 comments, 11 saves, 344
likes** — 35× every other reel. The 3D reels the same day (No. 18 equation-knight 1.8k, No. 19 bismuth 0.3k
early) and every 3D/ASMR reel before sat at ~1.6k. What worked: (1) a question the viewer answers by
watching — a hunt; (2) a 10–15 s seamless loop, so the watch % passes 100%; (3) a mesmerising physics
pattern (pendulum wave) that is pretty even if you never find it; (4) a one-word comment answer (E7) —
cheap to comment; (5) a fair audio clue. Flat 2D in our look was FINE here — the idea beats the rendering.
**New slot plan from 2026-11-12:**
- **10:00 and 13:00 — SPOT IT puzzles** (format 1 below), each a different object family + difference,
  and different from each other the same day. Pendulums and round bobs are allowed again (they're what
  went viral). Rotate families: pendulum wave rows/rings, double pendulums (one with a slightly heavier
  lower bob — chaos makes it brutal, so make the difference visible after ~5 s), metronomes (one beats
  out of sync), coupled spring-mass chains, spinning tops (one precesses the other way), clock hands,
  Newton's cradles in a grid (one ball is slightly heavier), orbiting moons (one orbit slightly slower),
  wave pools… Vary the hunt too: "one is a little longer / heavier / slower / one starts later / one spins
  the other way / one never syncs". Keep difficulty: hard for ~3 s, findable by ~6–8 s, obvious by the
  loop point. Same layout DNA as No. 17 (lettered columns, numbered rows, 3-line header, @whatiffun).
- **18:00 — a famous physics demo with a chaos → order (or order → chaos) arc** in our look (the two
  earlier breakouts: 48 metronomes syncing 7.1k, 1,000 double pendulums 5.3k): pendulum waves, metronome
  sync, Kuramoto fireflies, double-pendulum divergence, coupled oscillators, Galton board, Chladni
  sand. 12–20 s, open mid-action, a live count, a caption question/prompt that invites a comment
  ("Which one breaks first?" style is fine in the CAPTION; on screen keep it calm). 2D in our look is fine;
  3D only if it doesn't slow the slot down.
- 3D Blender reels and EQUATION DRAWS are paused (no lift vs 2D). Keep the pipeline code for later.
**Upgrades (2026-11-12, after No. 20 metronomes also hit 41k in 5.5 h, 163% watched, and No. 17 passed
275k plays but only ~25 follows):**
- **Answer loop → follows.** Every SPOT IT caption adds a line "Yesterday's answer: <letter+number> 🎯"
  revealing the PREVIOUS DAY's puzzle in the SAME slot (take it from HISTORY.md; skip the line if there is
  none), and every SPOT IT Metricool post sets `firstCommentText` to "Answer in tomorrow's puzzle 👀".
- **No sameness.** Each SPOT IT must change the ARRANGEMENT as well as the object (rectangular grid,
  ring/clock face, spiral, staggered rows, concentric rings…) — never the same layout two puzzles running.
  Keep the lettered/numbered addressing (for rings: letters around, numbers outward).
- **18:00 slot rule.** If the 18:00 famous demos (from No. 22 on) stay under ~5k IG plays at 24 h for two
  in a row while SPOT IT keeps beating them, switch 18:00 to a third daily SPOT IT (the weekly review
  checks this and edits the 18:00 task's prompt).
- **18:00 tension → release (2026-11-12 reference):** build the demo around a near-miss — a long "almost" (it nearly syncs, the gap nearly closes, the last one nearly falls) with ticks building tempo — then a sudden cascading payoff. Comment prompt in the caption can ride the tension ("Guess the second it happens.").
- Reply to comments early (owner) — comments are what pushed No. 17. Pin No. 17 on the profile.

**15:00 — SATISFYING CHAIN REACTION (owner, 2026-11-12, after No. 23 "One gap": "This is nice. Tomorrow after
plan to post stuff like this around 3pm… stick to similar video like I told. Satisfying").** A FOURTH daily slot.
DNA of No. 23 (code: `src/2026-11-12-one-gap/`): ONE clear goal the viewer instantly gets (get in / break
through / reach / fill), a long NEAR-MISS build-up of ~10–14 s (it almost makes it again and again — the gap
glows, every close call flashes and ticks louder), then a sudden RELEASE into an exploding, satisfying
cascade (things multiply, break, clear, fill) ~5–7 s, a live count racing up, "cleared/filled" moment +
chord, end card; 20–26 s total. 2D in our look, crisp glossy objects, colour gradients; the arena must read
at phone size (big, bright hero object during the build-up). Kicker = the goal in 2 words ("ONE GAP"),
rule lines ≤ 6 words ("Find the gap. / Then it multiplies."). Caption prompt rides the tension: "Guess the
second it slips through." Balls are ALLOWED in this slot (that's the format); keep the other slots' reels
not ball-led. Change the arena + mechanic every day — never the same board twice: a round arena with one
gap in a spinning-free steel ring; a honeycomb of hex blocks; a spiral wall with one opening; a glass jar
whose lid has one hole and the balls multiply until it overflows; a dam of blocks that one drip erodes until
it bursts; a lock of nested rings with one gap each (inner rings only open after the outer is cleared)…
Tune the sim headless so the near misses are VISIBLE (search launch angles/positions for the most spread
near misses, like gap.py's search) and the cascade lasts 5–7 s (not < 2 s, not > 9 s). NEVER copy another
creator's game, layout or face-cam. The owner rejected "One spark" (top-down matches, invisible tension):
if a viewer can't tell what is almost happening, it fails.

**RACE (owner, 2026-11-12: "You can add this too", after a "1 vs 100 vs 10,000" lane race).** The 18:00 slot
now ALTERNATES: RACE on odd days of the month, famous physics demo on even days (start 2026-11-13 = race).
Format: 3 side-by-side lanes (labelled A / B / C, each its own colour), one goal readable in 1 second
("First to the bottom wins", "First jar full wins"), the same start, a different PHYSICAL setting per lane;
the early leader must NOT be the winner (a real comeback), the finish is close and the margin is shown
("C wins by 0.18 s"). Live per-lane counters (time / distance / count). Real, deterministic physics so the
result is true — and ideally counter-intuitive, so people argue in the comments: brachistochrone (straight
ramp vs steep drop vs cycloid curve), honey vs oil vs water fall-through (viscosity), 1 big vs 100 medium
vs 10,000 grains through a funnel, heavy vs light vs hollow cylinders rolling down a slope, pendulum
lengths, spring stiffness, Galton boards with different peg spacing, dominoes with different spacing… Our
look (warm black, cream serif header, amber kicker `RACE`), ASMR sound per lane panned left/centre/right,
a chord + "A/B/C wins" at the finish, end card; 18–28 s. Caption: one line on the setup + "Pick your lane
before it starts: A, B or C 👇" (the cheap one-letter comment that made SPOT IT work) + "Sound on. 🎧".
Never copy that creator's columns-of-HP-floors, ball counts, neon look or wording.

**UPDATE (owner, 2026-11-11) — overrides the NO BALLS rule and the older "too generic" verdicts below:**
"You can resume the metronome style, generic ones. You can use the balls one too. But not for everything."
Why: Metricool 2026-11-11 shows the two real breakouts were famous chaos → order / chaos demos with a
question in the caption — the 48 metronomes syncing (IG 7,110 views, 13.1 s avg watch) and the 1,000 double
pendulums (5,325) — while every calm ASMR reel (Nos. 5–16, 2D and 3D) sat at 1.5–1.8k with ~0 shares.
So: (a) well-known physics demos ("generic ones": metronome sync, pendulum waves, double-pendulum chaos,
coupled oscillators, Galton boards, Chladni, Kuramoto fireflies, Newton's cradle variants…) are allowed
again, done in our premium look and with a clear chaos → order (or order → chaos) arc and a live count;
(b) balls/marbles/beads are allowed again as main objects, but at most ONE reel in any run of 3 consecutive
HISTORY.md rows may use them; the rest keep using other objects (idea bank below).
**NO BALLS (owner, 2026-11-10) — now relaxed, see the update above:** "Stop with the balls. It's getting too much, too boring." Balls, marbles,
beads, pearls, spheres, bubbles-as-dots and glowing orbs were BANNED as the main objects in every reel, all
formats, from No. 18 on. (Reels 1–17 used them to death.) Every reel must be about a different KIND of thing
and a different KIND of action than the last 5 rows in HISTORY.md. Innovate: surprise the owner every time.

**Idea bank (pick fresh, combine, invent better ones; never repeat a row of HISTORY.md):**
- 3D ASMR, tactile actions: jelly cubes pushed through a brass wire grid → 1, 4, 16, 64… cubes; a wax
  block sliced by 1 → 10 → 100 hot wires; kinetic sand shaved into ribbons; a stack of 1,000 glass tiles
  toppling in a spiral; soap bars stamped into hexagons; honey/viscosity ladder pours (thin → thick)
  onto a walnut board; silk cloth draping over 1 → 100 pins; a glass slab cracking in a fractal; paper
  folding in half 1 → 10 times; gears meshing in a growing train (1 → 50) that turns a tiny clock; chain
  links settling into a pile; coins stacking into a spiral tower; crystal (bismuth-like) staircase growth;
  ice cubes melting into a mirror pool; ferrofluid spikes rising in rings; springs compressing in a wave;
  a Jenga-style tower losing one block per beat; origami crane unfolding into a tessellation; dominoes
  laid in a golden-angle spiral; wooden sticks (cobra weave) chain-reacting; sand pendulum drawing a
  harmonograph in sand (the trace is the pattern, not a ball).
- SPOT IT objects: metronome needles, spinning tops, slinkies/springs, gears, clock hands, hourglasses,
  falling dominoes rows, spinning coins, flags in wind, candle flames, windmills/turbines, swinging
  doors, seesaws, wind chimes (tubes), lily pads on ripples, origami birds flapping, piano hammers,
  paper lanterns, rotating cubes, folding fans. Difference: one is a touch faster/slower,
  heavier, longer, reversed, out of phase, stiffer, a slightly different shade or size.

**Three formats, one per slot** (each slot's task runs in its own session; after `git pull`, check today's
HISTORY.md rows and make something with a different object, material and action from the other slots):
0. **10:00 — 3D LADDER** (peak hour, premium). Real 3D, same pipeline as the 18:00 slot. ONE tactile action
   repeated at an escalating setting, each stage ~2–3 s with a small label for the stage under the rule line
   (e.g. "1 wire → 10 → 100 → 1,000 wires" slicing a wax block; "Softness 0% → 100%" pressing a jelly
   stamp; "Thickness: water → honey → tar" pouring), the count/label jumping with a soft thump. Open on the
   most dramatic stage (or a 1-second flash-forward of it), 12–16 s of action. Kicker `LADDER` (or the
   setting's name), rule line ≤ 6 words. Exaggerated tactile foley per stage. Never knives (another page's
   format) and never balls.
   **EQUATION DRAWS (owner, 2026-11-10, "this is what I meant: see how a cool equation is developed"; he
   loved a reel where a Fourier series of spinning circles slowly draws a dragonfly as N climbs 1 → 8,192
   and it finally turns into a real one).** Alternate the 10:00 ladder with this every other day (start
   2026-11-11). Our own version, never a dragonfly, never a copy of that reel's layout:
   - A 3D brass MACHINE draws the picture: a chain of polished brass rings/arms (epicycles = the Fourier
     series) turning on a walnut desk, with a fine nib dragging a glowing gold line (or a groove in sand,
     or ink on cream paper). Real equation, real rotation speeds: arm k turns k times as fast.
   - The ladder IS the number of arms: 1 → 4 → 16 → 64 → 256 → 1,024 (stage label "1 arm", "16 arms"…).
     The drawing goes from a wobbly loop to an unmistakable picture. Each stage change = a soft brass
     clunk + a chord; the arms tick softly as they turn; the nib makes a fine scratch.
   - Pick a subject people instantly recognise and want to share (a chess knight, a cat, a hummingbird,
     a violin, a seahorse, the Taj Mahal outline, a heart, a treble clef…). Outline recipe:
     `matplotlib.textpath.TextPath` of a DejaVu Sans glyph (♞ ♛ ♫ ✈ ❀ ☂ ♥) or a hand-built polyline →
     resample to 4,096 points along arc length → complex FFT → keep the N largest terms, sorted by size.
   - The payoff: at the top stage the line closes, holds a beat, then the outline rises into a real 3D
     object of that subject (extrude + bevel the same outline in brass, glass or walnut) on the desk.
   - On screen: kicker `ONE EQUATION`, the series in one elegant line of serif maths
     (x(t) + i·y(t) = Σ cₖ e^{ikt}) as the rule line (this format is the one exception to "no formulas"),
     and the arm count as the live number. No error %, no lecture, no "why…" title.
   - 3D budget: instance the rings (one point cloud + GN) and draw the trail as a curve with a bevel and
     an emission shader; ≤ 16 s of action; open on a striking mid-drawing frame (a flash-forward of the
     dense stage), then rewind to 1 arm.
1. **13:00 — "SPOT IT" puzzle** (fast to make, built for comments + rewatches). A 10–15 s SEAMLESS LOOP of
   a beautiful physics grid/field (metronomes, tops, springs, gears, clock hands, dominoes, fans,
   flags… never balls) where exactly ONE element differs subtly (longer, heavier, slower, reversed, different
   friction…). Laid out with letter columns + number rows. Kicker `SPOT IT` (amber, spaced), two serif
   lines naming the difference ("One pendulum is / a little longer."), a small italic line "Comment its
   letter + number". It should be hard at first and findable within ~5–8 s. The motion should be a
   gorgeous pattern on its own (a rolling wave, a spiral, a ripple). ASMR sound: soft ticks/clicks, the odd
   one with a slightly different tone (an audio clue). No end card (it loops); `@whatiffun` mark at the
   bottom. Never reuse another creator's puzzle (no orbiting-dot grids, no "going backwards" dots).
   Reference: `src/2026-11-11-spot-pendulums/spot_pendulums.py`.
2. **18:00 — 3D ONE RULE ASMR** (the premium look the owner asked for: "looks flat" was the complaint). Real 3D in
   Blender (`pip install --break-system-packages bpy==5.2.3` ≈ 25 min download) rendered with Cycles on CPU:
   see `src/3d-pipeline/` — `split3d_gn.py` (scene: dark warm studio, walnut pedestal, brass, instanced
   objects driven by a 2D/3D sim — that reel used marbles, which are now banned; reuse the set, lights and
   instancing, not the objects; 540x960 at 6 samples + OpenImageDenoise ≈ 9 s/frame on 2 cores)
   and `composite.py` (upscale + our header/count/mark/end card + sound). Budget: ≤ 18 s of action
   (≈ 540 frames ≈ 80 min render). Use instancing (one point cloud + Geometry Nodes) for many objects.
   Ladders of one setting, gliding, tactile materials (glass, brass, walnut, jelly-like gloss), rich
   lighting. The 2D kit look (flat dots on black) is no longer acceptable for this slot.

**What the numbers say (vidIQ, 2026-11-10):** every reel stalls at ~1,500–1,800 IG plays (Instagram's
first test pool) because shares, saves and comments are ~0 (1 comment in 11 reels; followers 8 → 10). The
only breakout was the 1,000 double pendulums (5,187). Best retention: No. 10 pearls, 82% watched at 22 s.
~30% swipe away in the first second. So:
- **Open on the most striking moment** (no slow build from one object; start mid-action, beautiful at frame 1).
- **Shorter: 15–18 s** of action for ASMR; 10–15 s loops for SPOT IT.
- **Caption must invite a share or save**, not just describe: e.g. "Send this to someone who needs
  20 seconds of calm." / "Save this for when your brain is loud." (a statement, no question on screen).
- Track per-reel plays, watched %, skip rate, shares, saves and comments in HISTORY.md (the weekly review
  fills them in) and lean into whatever breaks the ~1.7k ceiling.

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
WARNING: No. 13 (straight-lines: dots sliding on lines forming rose curves) was REJECTED as "too basic" —
flat dots on thin lines read as a screensaver. Patterns must come from real, tactile, satisfying physical
objects and events (things colliding, cutting, squishing, pouring, stacking, gliding through), richly
rendered, with lots happening — not abstract dots tracing curves.
Keep the rule text ≤ 6 words, the count, no questions, no lectures.

## 3D, NOT FLAT (owner, 2026-11-10): asked what made No. 13 too basic → "Looks flat"
The owner's latest references are realistic 3D CGI (studio lighting, soft shadows, depth, real materials:
wood, brushed metal, glass, jelly, marble, liquid), plus a ladder of one setting per stage ("Soft 0% → 100%",
"10 → 1,000 cuts") and exaggerated tactile foley (chop, squish, shatter, splat). Flat 2D dots/circles on a
black screen now read as basic. Move to real 3D scenes (Blender via `bpy`) on our dark warm studio
background, with objects on a pedestal/surface, a key light + rim light, shadows and reflections.

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
   timezone Asia/Calcutta) — if a NON-DRAFT post is already scheduled within 45 minutes of your slot today, do
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
