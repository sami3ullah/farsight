"""Spike: logged-out Playwright on Instagram Profile and Reel pages. Do metrics load? Is a Reel share count exposed?"""
import json, re, sys, time
from playwright.sync_api import sync_playwright

handle = sys.argv[1] if len(sys.argv) > 1 else "duolingo"
keys_of_interest = re.compile(r"(like_count|comment_count|share|reshare|repost|play_count|view_count|taken_at|save)", re.I)
found, errors, calls = {}, [], []

def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if keys_of_interest.search(k) and not isinstance(v, (dict, list)):
                found.setdefault(k, []).append(v)
            walk(v, k)
    elif isinstance(o, list):
        for v in o: walk(v, path)

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    ctx = b.new_context(locale="en-US", user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    page = ctx.new_page()
    def on_resp(r):
        if "graphql" in r.url or "/api/v1/" in r.url:
            try:
                t = r.text(); calls.append((r.url[:90], r.status, len(t)))
                if "Rate limit" in t or "require_login" in t: errors.append(t[:200])
                walk(json.loads(t))
            except Exception: pass
    page.on("response", on_resp)
    page.goto(f"https://www.instagram.com/{handle}/reels/", wait_until="domcontentloaded"); page.wait_for_timeout(6000)
    for lbl in ["Decline optional cookies", "Allow all cookies"]:
        try:
            x = page.get_by_role("button", name=lbl).first
            if x.is_visible(timeout=1500): x.click(); page.wait_for_timeout(3000); break
        except Exception: pass
    for s in page.locator("script[type='application/json']").all():
        try: walk(json.loads(s.inner_text()))
        except Exception: pass
    page.mouse.wheel(0, 3000); page.wait_for_timeout(4000)
    links = page.eval_on_selector_all("a[href*='/reel/']", "els => els.map(e => e.getAttribute('href'))")
    print("reel links on grid:", len(links), links[:3])
    page.screenshot(path=f"out/ig_{handle}_reels.png")
    if links:
        page.goto("https://www.instagram.com" + links[0], wait_until="domcontentloaded"); page.wait_for_timeout(6000)
        for s in page.locator("script[type='application/json']").all():
            try: walk(json.loads(s.inner_text()))
            except Exception: pass
        page.screenshot(path=f"out/ig_{handle}_reel.png")
    b.close()
print("calls:", calls[:15])
print("errors:", errors[:3])
for k, v in sorted(found.items()): print(k, len(v), v[:5])
