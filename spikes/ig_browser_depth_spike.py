"""Spike: how deep can a logged-out browser page an Instagram Profile grid, with metrics + timestamps?"""
import json, sys, time
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).timestamp()
profiles = json.load(open("profiles.json")); only = sys.argv[1:]
SHARE_KEYS = set()

def walk(o, media):
    if isinstance(o, dict):
        code = o.get("code") or o.get("shortcode")
        if code and isinstance(code, str) and ("like_count" in o or "taken_at" in o or "comment_count" in o):
            m = media.setdefault(code, {})
            for k in ["taken_at", "like_count", "comment_count", "play_count", "view_count", "product_type", "media_type", "video_duration"]:
                if o.get(k) is not None: m[k] = o[k]
            if isinstance(o.get("caption"), dict) and o["caption"].get("text"): m["caption"] = True
        for k in o:
            if "share" in k.lower() and "count" in k.lower(): SHARE_KEYS.add(k)
        for v in o.values(): walk(v, media)
    elif isinstance(o, list):
        for v in o: walk(v, media)

results = []
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for p in profiles:
        h = p["instagram"]
        if only and h not in only: continue
        ctx = b.new_context(locale="en-US", viewport={"width": 1280, "height": 1800},
                            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
        page = ctx.new_page(); media = {}; errs = []; t0 = time.time(); r = {"handle": h, "error": None}
        def on_resp(resp):
            if "graphql" in resp.url or "/api/v1/" in resp.url:
                try:
                    t = resp.text()
                    if "Rate limit" in t or "require_login" in t or resp.status in (401, 429): errs.append(f"{resp.status} {t[:120]}")
                    walk(json.loads(t), media)
                except Exception: pass
        page.on("response", on_resp)
        try:
            page.goto(f"https://www.instagram.com/{h}/", wait_until="domcontentloaded", timeout=45000); page.wait_for_timeout(5000)
            for lbl in ["Decline optional cookies", "Allow all cookies"]:
                try:
                    x = page.get_by_role("button", name=lbl).first
                    if x.is_visible(timeout=1500): x.click(); page.wait_for_timeout(3000); break
                except Exception: pass
            for s in page.locator("script[type='application/json']").all():
                try: walk(json.loads(s.inner_text()), media)
                except Exception: pass
            stall = 0
            for i in range(25):
                n = len(media)
                try:
                    c = page.locator("svg[aria-label='Close']").first
                    if c.is_visible(timeout=300): c.click(timeout=1000)
                except Exception: pass
                page.mouse.wheel(0, 3000); page.wait_for_timeout(2500)
                stall = stall + 1 if len(media) == n else 0
                ts = [m["taken_at"] for m in media.values() if "taken_at" in m]
                if stall >= 5 or (len(ts) > 4 and sorted(ts)[3] < cutoff): break
            grid = page.eval_on_selector_all("a[href*='/p/'], a[href*='/reel/']", "els => els.length")
            ts = sorted(m["taken_at"] for m in media.values() if "taken_at" in m)
            def cnt(k): return sum(k in m for m in media.values())
            r.update({"media_nodes": len(media), "grid_links": grid, "scrolls": i + 1,
                      "with_taken_at": cnt("taken_at"), "with_like": cnt("like_count"), "with_comment": cnt("comment_count"),
                      "with_play": cnt("play_count"), "with_caption": cnt("caption"),
                      "oldest": datetime.fromtimestamp(ts[0], timezone.utc).date().isoformat() if ts else None,
                      "newest": datetime.fromtimestamp(ts[-1], timezone.utc).date().isoformat() if ts else None,
                      "in_window": sum(t >= cutoff for t in ts), "errors": errs[:2]})
            page.screenshot(path=f"out/ig_{h}.png")
        except Exception as e:
            r["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        r["seconds"] = round(time.time() - t0, 1)
        results.append(r); print(json.dumps(r), flush=True); ctx.close(); time.sleep(8)
    b.close()
print("share-count-like keys seen:", sorted(SHARE_KEYS))
json.dump({"results": results, "share_keys": sorted(SHARE_KEYS)}, open("out/ig_browser.json", "w"), indent=2)
