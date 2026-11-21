# Story videos (YouTube) — pipeline, 2026-11-21

Owner's brief: murder mysteries, rescue missions, abnormal human beings, fun facts nobody knows,
"what if" stories (e.g. what if the Eiffel Tower was made of human bones), weird stuff.

1. `bash tools/install_story_skills.sh` (humanizer, last30days, directing-stickman-videos; pinned commits).
2. Research with WebSearch/WebFetch (the workspace shell can't reach reddit/youtube/x; last30days' engine needs that).
   Every number checked against a source; sources kept in the story folder's notes.
3. Script in short caption-sized lines (≤ ~32 chars), cleaned with the humanizer rules.
4. Voice: vidIQ `vidiq_voiceover_generate` with `scriptLines` (ElevenLabs voices; George = JBFqnCBsd6RMkjVDRZzb);
   its per-line `startSeconds` give exact caption/shot timing.
5. Art: vidIQ `vidiq_image_generate`, 9:16, transparent background, stickman B1 style prompt.
6. Media download: the workspace can't reach vidIQ's hosts, so push `story/fetch/<name>.txt` lines
   "<story/... path> <https url>" — `.github/workflows/fetch-media.yml` downloads and commits them; `git pull`.
7. Build the B1 native-portrait project (see `eiffel-bones/build_project.py`), `autopilot.mjs validate`, then
   `preview --seconds <full>`; loudnorm the result to about -14 LUFS for Shorts.
Cost per ~45 s Short: ~150–180 vidIQ credits (7 images × 22 + voice ~28).
