"""Spike: Instagram Business Discovery API against ~10 Profiles, 3-month Lookback window.

Needs spikes/.fb_token (gitignored) or env FB_TOKEN (a User access token from Graph API Explorer, see CHECKLIST in the results doc).
Records which fields come back and the app-usage headers so the real hourly limit can be extrapolated.
"""
import json, os, sys, time
from datetime import datetime, timedelta, timezone
import requests

V = "v24.0"; G = f"https://graph.facebook.com/{V}"
TOKEN = os.environ.get("FB_TOKEN") or (open(".fb_token").read().strip() if os.path.exists(".fb_token") else sys.exit("put a token in spikes/.fb_token or set FB_TOKEN"))
cutoff = datetime.now(timezone.utc) - timedelta(days=90)
MEDIA_FIELDS = "id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count,view_count,media_url,thumbnail_url"
usage_log, calls = [], [0]

def get(path, **params):
    params["access_token"] = TOKEN
    r = requests.get(f"{G}/{path}", params=params, timeout=60); calls[0] += 1
    usage_log.append({"call": calls[0], "status": r.status_code, "x_app_usage": r.headers.get("x-app-usage"),
                      "x_buc_usage": r.headers.get("x-business-use-case-usage")})
    return r.status_code, r.json()

# 1. Find the user's own IG professional account id via their Pages
st, me = get("me/accounts", fields="name,instagram_business_account{id,username}")
igs = [p["instagram_business_account"] for p in me.get("data", []) if p.get("instagram_business_account")]
if not igs: sys.exit(f"No Instagram Business account linked to any Page: {json.dumps(me)[:400]}")
ig_id = igs[0]["id"]; print("querying as", igs[0])

profiles = json.load(open("profiles.json")); results = []
for p in profiles:
    h = p["instagram"]; t0 = time.time(); after = None; posts = []; err = None; acct = {}
    while True:
        cursor = f".after({after})" if after else ""
        st, d = get(ig_id, fields=f"business_discovery.username({h}){{followers_count,media_count,media.limit(50){cursor}{{{MEDIA_FIELDS}}}}}")
        if st != 200: err = json.dumps(d.get("error", d))[:300]; break
        bd = d["business_discovery"]; acct = {"followers_count": bd.get("followers_count"), "media_count": bd.get("media_count")}
        media = bd.get("media", {}); batch = media.get("data", [])
        old = 0
        for m in batch:
            if datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z") < cutoff: old += 1
            else: posts.append(m)
        after = media.get("paging", {}).get("cursors", {}).get("after")
        if old >= 3 or not after or not batch: break
    fields = {}
    for k in MEDIA_FIELDS.split(","):
        fields[k] = [sum(k in m for m in posts), len(posts)]
    reels = [m for m in posts if m.get("media_product_type") == "REELS"]
    r = {"handle": h, "ok": err is None, "error": err, **acct, "posts_in_window": len(posts),
         "reels": len(reels), "reels_with_views": sum("view_count" in m for m in reels), "fields_present": fields,
         "sample": posts[0] if posts else None, "seconds": round(time.time() - t0, 1)}
    results.append(r); print(json.dumps({k: v for k, v in r.items() if k != "sample"}), flush=True)

# 2. Burn a controlled batch of cheap calls to see how fast x-app-usage rises (estimate the hourly ceiling)
for _ in range(int(os.environ.get("BURN", "40"))):
    get(ig_id, fields="business_discovery.username(nike){followers_count}")
json.dump({"results": results, "calls": calls[0], "usage_log": usage_log}, open("out/business_discovery.json", "w"), indent=2)
print("total calls:", calls[0]); print("last usage headers:", usage_log[-1])
