"""Spike: facebook-gql-scraper anonymous mode, 3-month Lookback window, ~10 Pages."""
import json, time, itertools
from datetime import datetime, timedelta, timezone
import facebook_gql_scraper as fgs

cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).timestamp()
profiles = json.load(open("profiles.json"))
ctx = fgs.FacebookContext(quiet=True)
results = []
for p in profiles:
    h = p["facebook"]; t0 = time.time()
    r = {"handle": h, "ok": False, "posts_in_window": 0, "reached_window_end": False, "error": None,
         "followers": None, "fields_present": {}, "samples": []}
    try:
        u = fgs.Profile.from_username(ctx, username=h)
        r["followers"] = u.followers_count
        old = 0
        for post in itertools.islice(u.get_posts(), 300):
            ct = getattr(post, "creation_time", None)
            if ct and ct < cutoff:
                old += 1
                if old > 3: r["reached_window_end"] = True; break
                continue
            r["posts_in_window"] += 1
            for k in ["creation_time", "text", "reaction_count", "share_count", "comments_count", "url"]:
                v = getattr(post, k, None)
                r["fields_present"].setdefault(k, [0, 0]); r["fields_present"][k][0] += v is not None; r["fields_present"][k][1] += 1
            if len(r["samples"]) < 3:
                r["samples"].append({k: getattr(post, k, None) for k in ["id", "creation_time", "reaction_count", "share_count", "comments_count", "url"]})
        r["ok"] = True
    except Exception as e:
        r["error"] = f"{type(e).__name__}: {str(e)[:300]}"
    r["seconds"] = round(time.time() - t0, 1)
    results.append(r); print(json.dumps(r, default=str), flush=True)
    time.sleep(5)
json.dump(results, open("out/fb_gql.json", "w"), indent=2, default=str)
