"""@whatiffun comment auto-replies (Instagram API with Instagram Login).

Every run (GitHub Actions, every 15 min):
  * looks at our recent Reels,
  * finds top-level comments from the last REPLY_WINDOW_H hours that we have not answered yet,
  * replies to answer-style comments on SPOT IT puzzles ("E7", "b 4", "found it") with a rotating,
    spoiler-free line ("Locked in 🔒 …") — it never says whether a guess is right,
  * replies to "what's the answer?" comments with where the answer appears,
  * leaves everything else (questions, long comments, other reels) for a human,
  * 24 h after a puzzle goes up, posts its answer as a comment ON THAT PUZZLE ("Answer: E6 🎯 …"), using
    answers.json (puzzle number -> cell), once per puzzle.

Stateless: a comment counts as answered when it already has a reply from our own account.
Public repo => logs are public, so we only ever print counts and ids, never names or comment text.

Env: IG_TOKEN (required, long-lived Instagram user token with instagram_business_basic +
instagram_business_manage_comments), DRY_RUN=1 to only count, MAX_REPLIES (default 25 per run).
"""
import json, os, pathlib, random, re, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.instagram.com"
MEDIA_LIMIT = 60            # ~two weeks of reels at 4 a day
ANSWER_AFTER_H = 24         # reveal the answer on the puzzle this long after it posts
REPLY_WINDOW_H = 48         # only comments younger than this
MAX_REPLIES = int(os.environ.get("MAX_REPLIES", "25"))
DRY = os.environ.get("DRY_RUN", "") not in ("", "0", "false")

LINES = [
    "Locked in 🔒 The answer drops right here tomorrow 👀",
    "Noted ✍️ We post the answer in these comments tomorrow 🎯",
    "Bold pick 👀 Answer goes up here tomorrow",
    "Got it 📌 Check back here tomorrow for the answer",
    "Locked in. Answer in the comments tomorrow 🎯",
    "Pinned your guess 📌 We reveal it here tomorrow 👀",
]
LINES_BREAKS = [
    "Locked in 🔒 Tomorrow we reveal it here, and the law it breaks 👀",
    "Noted ✍️ Answer (and the broken law) drops here tomorrow 🎯",
    "Bold pick 👀 We reveal the cheater here tomorrow",
]
LINES_ASK = [
    "It drops right here in the comments tomorrow 👀 Take a guess first!",
    "Answer goes up here tomorrow 🎯 Guess first: letter + number",
]
LINES_SONG = [
    "Locked in 🎵 The song gets revealed right here tomorrow 👀",
    "Noted ✍️ We name the song in these comments tomorrow 🎯",
    "Good ear? We'll see 👀 Answer drops here tomorrow",
]
ANSWER_FMT = "Answer: {answer} 🎯 It's {what}. Did you get it? New puzzle tomorrow 👀"
ANSWER_FMT_SONG = "Answer: {answer} 🎵 {what}. Did you get it? New one tomorrow 👀"


# grid address: a column letter A–L and a row number 1–12, e.g. "E7", "e 7", "E-7", "7E"
ADDR = re.compile(r"(?<![a-z0-9])(?:[a-l]\s?[-:.]?\s?(?:1[0-2]|[1-9])|(?:1[0-2]|[1-9])\s?[-:.]?\s?[a-l])(?![a-z0-9])", re.I)
FOUND = re.compile(r"\b(found (it|him|her|the)|got (it|him)|there it is|easy|too easy|spotted)\b|🎯", re.I)
ASK = re.compile(r"\b(answer|where is|which one|what is it|can'?t find|cant find|cannot find)\b", re.I)


def classify(text):
    """-> 'guess' | 'ask' | None  (None = leave it for a human)"""
    t = (text or "").strip()
    if not t:
        return None
    if ADDR.search(t):
        return "guess"
    if len(t) <= 40 and FOUND.search(t):
        return "guess"
    if len(t) <= 60 and ASK.search(t):
        return "ask"
    return None


def api(path, params=None, method="GET"):
    params = dict(params or {}, access_token=os.environ["IG_TOKEN"])
    url = path if path.startswith("http") else f"{API}/{path.lstrip('/')}"
    data = None
    if method == "GET":
        if "access_token=" not in url:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code >= 500 and attempt < 2:
                time.sleep(3 * (attempt + 1)); continue
            raise RuntimeError(f"HTTP {e.code} on {path.split('?')[0][:60]}: {body}") from None


def paged(path, params, cap=500):
    out, res = [], api(path, params)
    while True:
        out += res.get("data", [])
        nxt = res.get("paging", {}).get("next")
        if not nxt or len(out) >= cap:
            return out
        res = api(nxt)


def main():
    if not os.environ.get("IG_TOKEN"):
        print("IG_TOKEN is not set yet; nothing to do.")
        return 0
    me = api("me", {"fields": "user_id,username"})
    my_name = me["username"].lower()
    since = datetime.now(timezone.utc) - timedelta(hours=REPLY_WINDOW_H)
    media = paged("me/media", {"fields": "id,caption,timestamp,media_product_type", "limit": 50}, cap=MEDIA_LIMIT)
    answers = json.loads((pathlib.Path(__file__).resolve().parent.parent / "answers.json").read_text())
    now = datetime.now(timezone.utc)
    rng = random.Random()
    stats = {"media": 0, "comments": 0, "already": 0, "skipped": 0, "replied": 0, "failed": 0, "answers_posted": 0}
    todo = []
    for m in media:
        cap = (m.get("caption") or "").lower()
        song = "comment the song" in cap              # MARBLE MUSIC "guess the song" reels
        if "letter + number" not in cap and not song:   # only puzzles
            continue
        stats["media"] += 1
        pool = LINES_SONG if song else (LINES_BREAKS if "breaks physics" in cap else LINES)
        comments = paged(f"{m['id']}/comments",
                         {"fields": "id,text,timestamp,username,replies{username}", "limit": 50}, cap=3000)
        # 1) reveal the answer on the puzzle itself, once, ANSWER_AFTER_H after it went up
        mnum = re.match(r"\s*no\.\s*(\d+)", cap)
        posted = datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
        if mnum and mnum.group(1) in answers and now - posted >= timedelta(hours=ANSWER_AFTER_H):
            mine = [c for c in comments if (c.get("username") or "").lower() == my_name]
            if not any((c.get("text") or "").lower().startswith("answer:") for c in mine):
                a = answers[mnum.group(1)]
                if DRY:
                    stats["answers_posted"] += 1
                else:
                    try:
                        api(f"{m['id']}/comments", {"message": (ANSWER_FMT_SONG if song else ANSWER_FMT).format(**a)}, method="POST")
                        stats["answers_posted"] += 1
                    except RuntimeError as e:
                        stats["failed"] += 1; print("answer failed", m["id"], str(e)[:200])
        for c in comments:
            ts = datetime.strptime(c["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            if ts < since:
                continue
            stats["comments"] += 1
            if (c.get("username") or "").lower() == my_name:
                continue
            if any((r.get("username") or "").lower() == my_name for r in c.get("replies", {}).get("data", [])):
                stats["already"] += 1; continue
            kind = classify(c.get("text"))
            if song and kind is None and 2 <= len((c.get("text") or "").strip()) <= 60:
                kind = "guess"                        # any short comment on a song reel is a guess
            if kind is None:
                stats["skipped"] += 1; continue
            todo.append((ts, c["id"], LINES_ASK if (kind == "ask" and not song) else pool))
    todo.sort()                                     # oldest first
    for _, cid, pool in todo[:MAX_REPLIES]:
        msg = rng.choice(pool)
        if DRY:
            stats["replied"] += 1; continue
        try:
            api(f"{cid}/replies", {"message": msg}, method="POST")
            stats["replied"] += 1
            time.sleep(rng.uniform(4, 9))           # look human, stay far from rate limits
        except RuntimeError as e:
            stats["failed"] += 1
            print("reply failed", cid, str(e)[:200])
            if "HTTP 4" in str(e) and stats["failed"] >= 3:
                break
    stats["left_for_next_run"] = max(0, len(todo) - MAX_REPLIES)
    print(("DRY RUN " if DRY else "") + json.dumps(stats))
    return 1 if stats["failed"] and not stats["replied"] else 0


def refresh():
    """Print a refreshed 60-day token (the workflow stores it back into the repo secret)."""
    res = api("refresh_access_token", {"grant_type": "ig_refresh_token"})
    print(res["access_token"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        cases = {"E7": "guess", "e 7": "guess", "I think it's B-4!": "guess", "7E": "guess", "found it": "guess",
                 "🎯": "guess", "what's the answer?": "ask", "can't find it": "ask", "beautiful": None,
                 "this is so calming to watch every night": None, "A1 sauce": "guess", "lol": None,
                 "the answer is c12 because the sand goes up and that breaks the second law": "guess",
                 "at 3am I watch these": None}
        bad = {k: (classify(k), v) for k, v in cases.items() if classify(k) != v}
        print("selftest", "OK" if not bad else bad); sys.exit(1 if bad else 0)
    if len(sys.argv) > 1 and sys.argv[1] == "refresh":
        refresh(); sys.exit(0)
    sys.exit(main())
