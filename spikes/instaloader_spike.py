"""Spike: instaloader 4.16 logged out, 3-month Lookback window, ~10 Profiles."""
import json, sys, time, traceback
from datetime import datetime, timedelta, timezone
import instaloader

LOOKBACK = datetime.now(timezone.utc) - timedelta(days=90)
MAX_POSTS = 200  # safety cap per Profile
profiles = json.load(open("profiles.json"))
L = instaloader.Instaloader(download_pictures=False, download_videos=False, download_video_thumbnails=False,
                            download_geotags=False, download_comments=False, save_metadata=False,
                            quiet=True, max_connection_attempts=1)
results, raw_keys = [], set()
for p in profiles:
    h = p["instagram"]; t0 = time.time()
    r = {"handle": h, "ok": False, "posts_in_window": 0, "reached_window_end": False, "error": None,
         "followers": None, "fields_present": {}, "sample": None}
    try:
        prof = instaloader.Profile.from_username(L.context, h)
        r["followers"] = prof.followers
        r["is_business"] = prof.is_business_account
        pinned_skips = 0
        for post in prof.get_posts():
            raw_keys.update(post._node.keys())
            if post.date_utc.replace(tzinfo=timezone.utc) < LOOKBACK:
                pinned_skips += 1
                if pinned_skips > 3:  # pinned posts can be old; allow a few
                    r["reached_window_end"] = True; break
                continue
            r["posts_in_window"] += 1
            f = {"caption": post.caption is not None, "likes": post.likes is not None and post.likes >= 0,
                 "comments": post.comments is not None, "typename": post.typename,
                 "views": post.video_view_count is not None if post.is_video else None,
                 "plays": getattr(post, "video_play_count", None) is not None if post.is_video else None,
                 "duration": post.video_duration is not None if post.is_video else None}
            for k, v in f.items():
                if isinstance(v, bool): r["fields_present"].setdefault(k, [0, 0]); r["fields_present"][k][0] += v; r["fields_present"][k][1] += 1
            if r["sample"] is None:
                r["sample"] = {"shortcode": post.shortcode, "date": post.date_utc.isoformat(), "typename": post.typename,
                               "likes": post.likes, "comments": post.comments, "views": post.video_view_count,
                               "plays": getattr(post, "video_play_count", None), "duration": post.video_duration,
                               "hashtags": post.caption_hashtags[:5], "mentions": post.caption_mentions[:5],
                               "share_like_keys": [k for k in post._node if "share" in k.lower()]}
            if r["posts_in_window"] >= MAX_POSTS: break
        r["ok"] = True
    except Exception as e:
        r["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    r["seconds"] = round(time.time() - t0, 1)
    results.append(r); print(json.dumps(r), flush=True)
    time.sleep(5)
json.dump({"results": results, "raw_node_keys": sorted(raw_keys)}, open("out/instaloader.json", "w"), indent=2)
