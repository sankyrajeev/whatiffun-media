#!/usr/bin/env bash
# Installs the owner's four story-video tools (2026-11-21) for this session, pinned to reviewed commits.
#   humanizer            (MIT)   - rewrite scripts/captions so they don't read as AI text
#   last30days           (MIT)   - "what are people saying in the last 30 days" research engine (needs open web access;
#                                  the cloud workspace blocks reddit/youtube/x from the shell, so use WebSearch there)
#   stickman-video-director (MIT) - stickman explainer/story videos; B-mode renders locally with node+ffmpeg
#   OpenMontage          (AGPLv3) - big agentic video pipeline; needs provider API keys for most routes
# Usage: bash tools/install_story_skills.sh [--with-openmontage]
# Skills land in ~/.claude/skills/<name>/ (picked up by sessions that start after this runs);
# full repos in ~/story-tools/<repo>/.
set -euo pipefail
DEST="${HOME}/story-tools"; SK="${HOME}/.claude/skills"
mkdir -p "$DEST" "$SK"
fetch() {  # repo commit
  local repo="$1" sha="$2" dir="$DEST/$(basename "$1")"
  if [ ! -d "$dir/.git" ]; then git clone -q --filter=blob:none --no-checkout "https://github.com/$repo" "$dir"; fi
  git -C "$dir" fetch -q --depth 1 origin "$sha" && git -C "$dir" checkout -q "$sha"
}
fetch blader/humanizer a32f24407364c74c812b43c15926d638bee1e072
fetch mvanhorn/last30days-skill bb2f1ed2b9f6d07b90557c5eebd736b566533fec
fetch kaomei/stickman-video-director 7fa6a9a543694cac95775200eb2f731b5594da0d
ln -sfn "$DEST/humanizer" "$SK/humanizer"
ln -sfn "$DEST/last30days-skill/skills/last30days" "$SK/last30days"
ln -sfn "$DEST/stickman-video-director/skills/directing-stickman-videos" "$SK/directing-stickman-videos"
( cd "$SK/directing-stickman-videos" && npm ci --silent && node scripts/autopilot.mjs doctor >/dev/null && echo "stickman renderer: ok" )
if [ "${1:-}" = "--with-openmontage" ]; then
  fetch OpenMontageInc/OpenMontage 2e003e65fa99a0f329478a2c1cdcf26bc481933a
  echo "OpenMontage cloned to $DEST/OpenMontage (read AGENT_GUIDE.md; most routes need API keys in .env)"
fi
echo "installed: humanizer, last30days, directing-stickman-videos -> $SK"
