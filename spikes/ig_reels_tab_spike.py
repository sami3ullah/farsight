"""Spike: logged-out browser on each Profile's Reels tab. Metrics coverage and any share-count field."""
import json, re, time
from playwright.sync_api import sync_playwright
profiles = json.load(open("profiles.json")); results = []; share_keys = set()
def walk(o, media):
    if isinstance(o, dict):
        code = o.get("code")
        if isinstance(code, str) and ("like_count" in o or "play_count" in o or "comment_count" in o):
            m = media.setdefault(code, {})
            for k in ["like_count", "comment_count", "play_count", "view_count", "taken_at", "like_and_view_counts_disabled"]:
                if o.get(k) is not None: m[k] = o[k]
        for k in o:
            if re.search(r"(share|reshare|repost|send)", k, re.I) and re.search(r"count", k, re.I): share_keys.add(k)
        for v in o.values(): walk(v, media)
    elif isinstance(o, list):
        for v in o: walk(v, media)
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for p in profiles:
        h = p["instagram"]; media = {}; errs = []; t0 = time.time()
        ctx = b.new_context(locale="en-US", viewport={"width": 1280, "height": 1800}); page = ctx.new_page()
        def on_resp(r):
            if "graphql" in r.url or "/api/v1/" in r.url:
                try:
                    t = r.text()
                    if "Rate limit" in t or r.status in (401, 429): errs.append(f"{r.status} {t[:100]}")
                    walk(json.loads(t), media)
                except Exception: pass
        page.on("response", on_resp)
        try:
            page.goto(f"https://www.instagram.com/{h}/reels/", wait_until="domcontentloaded", timeout=45000); page.wait_for_timeout(5000)
            for lbl in ["Decline optional cookies", "Allow all cookies"]:
                try:
                    x = page.get_by_role("button", name=lbl).first
                    if x.is_visible(timeout=1500): x.click(); page.wait_for_timeout(3000); break
                except Exception: pass
            for s in page.locator("script[type='application/json']").all():
                try: walk(json.loads(s.inner_text()), media)
                except Exception: pass
            for _ in range(4): page.mouse.wheel(0, 3000); page.wait_for_timeout(2000)
            def cnt(k): return sum(k in m for m in media.values())
            r = {"handle": h, "reels_with_metrics": len(media), "like": cnt("like_count"), "comment": cnt("comment_count"),
                 "play": cnt("play_count"), "taken_at": cnt("taken_at"), "errors": errs[:2]}
        except Exception as e:
            r = {"handle": h, "error": f"{type(e).__name__}: {str(e)[:200]}"}
        r["seconds"] = round(time.time() - t0, 1); results.append(r); print(json.dumps(r), flush=True); ctx.close(); time.sleep(6)
    b.close()
print("share-like count keys:", sorted(share_keys))
json.dump({"results": results, "share_keys": sorted(share_keys)}, open("out/ig_reels_tab.json", "w"), indent=2)
