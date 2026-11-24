"""Spike: yt-dlp tiktok:user logged out, 3-month Lookback window, ~10 Profiles."""
import json, time
from datetime import datetime, timedelta, timezone
import yt_dlp
from yt_dlp.utils import DateRange

FIELDS = ["view_count", "like_count", "comment_count", "repost_count", "save_count", "description", "timestamp",
          "duration", "track", "artist", "channel_follower_count", "uploader", "tags"]
since = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y%m%d")
profiles = json.load(open("profiles.json"))
results = []
for p in profiles:
    h = p["tiktok"]; t0 = time.time()
    r = {"handle": h, "ok": False, "posts_in_window": 0, "error": None, "fields_present": {}, "sample": None, "all_keys": None}
    entries = []
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).timestamp()
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"https://www.tiktok.com/@{h}", download=False, process=False)
            old = 0
            for e in info.get("entries", []):
                if not e: continue
                if e.get("_type") == "url":  # unresolved entry: resolve it
                    e = ydl.extract_info(e["url"], download=False, process=False)
                ts = e.get("timestamp")
                if ts and ts < cutoff:
                    old += 1
                    if old > 3: break  # pinned Posts can be old
                    continue
                entries.append(e)
                if len(entries) >= 200: break
        r["ok"] = True
    except Exception as e:
        r["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    r["posts_in_window"] = len(entries)
    for e in entries:
        for k in FIELDS:
            r["fields_present"].setdefault(k, [0, 0]); r["fields_present"][k][0] += e.get(k) is not None; r["fields_present"][k][1] += 1
    if entries:
        e = entries[0]; r["sample"] = {k: e.get(k) for k in FIELDS + ["id", "webpage_url"]}
        r["sample"]["description"] = (e.get("description") or "")[:80]
        r["all_keys"] = sorted(e.keys())
    r["seconds"] = round(time.time() - t0, 1)
    results.append(r); print(json.dumps({k: v for k, v in r.items() if k != "all_keys"}), flush=True)
    time.sleep(3)
json.dump(results, open("out/ytdlp_tiktok.json", "w"), indent=2)
