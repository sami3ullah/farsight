"""Spike: logged out, open individual Facebook Post/Reel URLs and capture exact counts from page JSON."""
import json, sys
from playwright.sync_api import sync_playwright
from fb_playwright_spike_lib import walk, parse_body
urls = sys.argv[1:]
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    for u in urls:
        ctx = b.new_context(locale="en-US"); page = ctx.new_page(); found = {}
        page.on("response", lambda r: [walk(o, found) for o in parse_body(r.text())] if "/api/graphql" in r.url else None)
        page.goto(u, wait_until="domcontentloaded", timeout=45000); page.wait_for_timeout(3000)
        for lbl in ["Decline optional cookies", "Allow all cookies"]:
            try:
                x = page.get_by_role("button", name=lbl).first
                if x.is_visible(timeout=1500): x.click(); page.wait_for_timeout(4000); break
            except Exception: pass
        for s in page.locator("script[type='application/json']").all():
            try: walk(json.loads(s.inner_text()), found)
            except Exception: pass
        mets = [m for m in found.get("_metric_nodes", []) if any(v is not None for v in m.values())]
        best = {k: max((m[k] for m in mets if isinstance(m[k], int)), default=None) for k in ["reaction", "share", "comments", "video_views"]}
        print(u, "->", best, "| nodes:", len(mets)); ctx.close()
    b.close()
