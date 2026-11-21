# Story videos — playbook (read fully before making one)

Owner, 2026-11-21, after approving "What if the Eiffel Tower was made of human bones?" (16:9 + 9:16 in our look):
**"post 2 videos like this everyday on youtube. and 1 video 9:16 on instagram everyday. you can choose which one goes on instagram."**
Earlier the same day: "for youtube its better if its horizontal videos, for these videos prioritise youtube",
"the voice modulation when explaining is not right" (fixed by voicing the whole script in ONE take) and
"dont forget to follow our UI guidelines" (the whatiffun look, below). Topics he wants: murder mysteries, rescue
missions, abnormal human beings, fun facts nobody knows, weird "what if" ideas ("what if the Eiffel Tower was
made of human bones"), weird stuff. He chose **vidIQ only** for drawings and voice (not OpenArt).

## Slots (IST)
| Run | Makes | Posts |
|---|---|---|
| STORY A (task fires ~08:20) | one story, both formats | YouTube 16:9 regular video at **11:00** |
| STORY B (task fires ~12:20) | one story, both formats | YouTube 16:9 at **16:00** + the better 9:16 of the day (A's or B's) as an Instagram Reel at **20:30** |
YouTube best-time data (Metricool, 2026-11-21): 16:00 is the daily peak, 10:00–15:00 next; 20:00+ is weak.
A and B on the same day use DIFFERENT categories. Never repeat a topic in `story/HISTORY.md`.

## Credits (vidIQ only — check first)
- Costs: voice 28 per 1,000 characters (rounded up, so keep the script ≤ 1,000 characters); drawings 22 each; titles 5.
- Per story budget: voice 28 + at most **3 new drawings** (66) + title 5 ≈ 100. Reuse art from `story/library/` and
  earlier stories' `art/` wherever it fits; when you draw a generic stick figure (pointing, shocked, thinking,
  running…), also copy it to `story/library/` for later stories.
- The four daily puzzles need ~20 credits/day for titles. Before spending anything: `vidiq_balance`; reserve =
  20 × days until `renewableResetsAt`. If `totalCredits − reserve < 110`, make nothing, send the owner ONE line
  ("Story <A/B> skipped today: vidIQ credits at X, they renew on <date>.") and stop.

## Categories (rotate; A and B differ)
1. **What if** — a physical what-if with real arithmetic (do the maths in Python; keep the numbers in notes.md).
2. **Mystery** — a famous, well-documented historical case (murder mysteries, disappearances, unsolved puzzles).
   Focus on clues and the puzzle, never gore; only facts reliable sources agree on; no private individuals.
3. **Rescue** — real rescues told as a countdown (dates, depths, hours, how it worked).
4. **Abnormal humans** — documented rare conditions or record-holders, told with respect (no mockery).
5. **Fun facts nobody knows / weird history.**

## Steps
1. `git pull`. Check Metricool (`getScheduledPosts`, blogId 7560268, Asia/Calcutta): if a NON-DRAFT YouTube post is
   already scheduled within 45 min of your slot today, do nothing and finish. Credit check (above).
2. **Research** with WebSearch/WebFetch: ≥ 2 reputable sources for every number and key claim. Write
   `story/<slug>/notes.md` (sources as links, the maths). Slug = short kebab-case.
3. **Script**: 130–170 words, ≤ 1,000 characters (~55–70 s). First sentence = the hook question/claim (≤ 12 words).
   Then 3–5 beats that escalate, each with ONE concrete number or picture, then the twist/answer, then
   "Subscribe for more <what-ifs | mysteries | rescues | weird facts>." Short spoken sentences; write numbers as
   words ("seven thousand three hundred") so George reads them right. Clean it with the `humanizer` skill's rules.
4. **Voice**: `vidiq_voiceover_generate`, voiceId `JBFqnCBsd6RMkjVDRZzb` (George), the whole script as ONE `script`
   string. NEVER `scriptLines` (per-line voicing gave every fragment a sentence ending — the owner noticed).
5. **Drawings** (≤ 3 new): `vidiq_image_generate` in ONE call, `background: "transparent"`, `aspectRatio` "9:16"
   for tall subjects or "1:1", no `model`. Prompt = the subject + this style line: "hand-drawn cartoon illustration,
   bold dark ink outlines, warm muted colours with cream and bone highlights, characters are simple stick figures
   with round white heads, expressive faces and black line limbs, one isolated subject, no text, no frame, no
   background". Poll each with `vidiq_job_poll` for its imageUrl.
6. **Download** (the workspace can't reach vidIQ hosts): write `story/fetch/<slug>.txt` with lines
   `story/<slug>/art/raw/<name>.png <imageUrl>` and `story/<slug>/narration.mp3 <audioUrl>`, commit, push, then
   `git pull` every ~20 s until the files exist (~1 min; `.github/workflows/fetch-media.yml`).
7. **Word timings**: write `story/align/<slug>.txt` containing `story/<slug>/narration.mp3`, commit, push, poll
   `git pull` until `story/<slug>/narration.words.json` exists (~4–6 min; `.github/workflows/align-words.yml`, whisper).
   If a list file with the same content already exists, use a new file name (the workflow fires on changes).
8. **Build**: `python3 story/engine/story.py prep story/<slug>` (trims, adds the cream sticker outline so black
   stick figures read on our dark background). Write `story/<slug>/story.json` (format in the engine's docstring;
   `story/eiffel-bones/story.json` is the worked example): one shot per beat, a new shot every 3–6 s, each with an
   amber kicker (≤ 3 words), l1/l2 ≤ ~22 characters, `num` + `num_at` on the beat's key number, art moving
   (sway/bob/pulse), `grid` for "enough for 24 towers"-style counts, `dim_at`/`out_at`/`in_at` for before→after.
   Use `at_s` / `word_fix` if whisper timed a word badly (check words around long pauses).
9. **Look before rendering**: `stills` for BOTH formats at the busiest moment of every shot; view them. Fix text
   overlapping art, empty stages, unreadable captions, anything outside x 100–980 / y 180–1640 (9:16).
   Then `render` 16x9 and 9x16 (~75 s each) and `thumb`. Check: duration ≈ voice + 3 s, `LUFS -14.0`,
   captions match the speech, a frame from the middle of each format looks right.
10. **Title**: `vidiq_generate_titles` (type "long", numTitles 6, previousTitles = recent titles in story/HISTORY.md).
    Pick the highest-scoring honest one (no clickbait the video doesn't deliver).
11. **Publish**: copy to `reels/stories/YYYY-MM-DD-<slug>-16x9.mp4`, `-9x16.mp4`, `-thumb.jpg`; add the
    `story/HISTORY.md` row; commit + push (pull --rebase, retry); confirm the raw URLs return 200.
    Metricool `createScheduledPost` (blogId 7560268, autoPublish true, timezone Asia/Calcutta):
    providers [youtube], media [16:9 raw URL], videoThumbnailUrl = thumb raw URL (if the call is rejected with
    VIDEO_THUMBNAIL_NOT_APPLICABLE, resend without it), youtubeData {title, type "video", privacy "public",
    madeForKids false, category "ENTERTAINMENT" (EDUCATION for fact stories), tags 8–12 plain keywords}.
    text (the YouTube description) = 2–3 plain lines on the story, blank line, "Sources:" + the links from notes.md,
    blank line, "#whatif #storytime #whatiffun" (3 hashtags).
12. **Instagram (STORY B only)**: decide which of today's two 9:16 cuts is stronger for Instagram (the hook a
    stranger would stop for and share; tie → the weirder one) and schedule it at 20:30 IST: providers [instagram],
    instagramData {type "REEL", showReelOnFeed true}, caption = `<title>`, blank line, one or two calm lines setting
    it up, "Sound on. 🎧", blank line, exactly 5 hashtags ending #whatiffun (e.g. #whatif #facts #history
    #storytime #whatiffun). Note the choice in HISTORY.md. (If A didn't produce a video today, use B's.)
13. **Report**: SendUserFile the 16:9 (and the Instagram 9:16) + SendUserMessage: title, when each posts, credits left.
    Plain words.

## The look (fixed — the owner's UI guidelines)
Warm near-black radial background with a soft amber floor light; amber spaced Inter SemiBold kicker; cream
Instrument Serif headline (2nd line italic); big amber serif numbers; Inter SemiBold cream captions at the bottom;
`@whatiffun` mark; the dark rounded end card "Subscribe / @whatiffun / for more …" with a soft 3-note chord.
Drawings = stick-figure cartoon cut-outs with the cream sticker outline. All of this is built into the engine —
never switch to a white background or another font.
