"""Spike: logged-out Playwright on a Facebook Page, capturing GraphQL JSON. How far before the login wall?"""
import json, sys, time
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).timestamp()
profiles = json.load(open("profiles.json"))
only = sys.argv[1:]  # optional subset of handles
MAX_SCROLLS = 40

def walk(o, found):
    if isinstance(o, dict):
        pid = o.get("post_id")
        if pid and ("creation_time" in o or "comet_sections" in o):
            found.setdefault(pid, {}).update({"has_node": True})
        if "creation_time" in o and o.get("id") and isinstance(o["creation_time"], int):
            found.setdefault("_times", []).append(o["creation_time"])
        fb = o.get("feedback") if isinstance(o.get("feedback"), dict) else None
        if "reaction_count" in o or "share_count" in o or "comment_rendering_instance" in o or "i18n_reaction_count" in o:
            found.setdefault("_metric_nodes", []).append({
                "reaction": (o.get("reaction_count") or {}).get("count") if isinstance(o.get("reaction_count"), dict) else o.get("reaction_count"),
                "i18n_reaction": o.get("i18n_reaction_count"),
                "share": (o.get("share_count") or {}).get("count") if isinstance(o.get("share_count"), dict) else o.get("share_count"),
                "comments": (((o.get("comment_rendering_instance") or {}).get("comments") or {}).get("total_count")),
                "video_views": o.get("video_view_count"),
            })
        for v in o.values(): walk(v, found)
    elif isinstance(o, list):
        for v in o: walk(v, found)

def parse_body(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("for (;;);"): line = line[9:]
        if not line: continue
        try: out.append(json.loads(line))
        except Exception: pass
    return out

results = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    for p in profiles:
        h = p["facebook"]
        if only and h not in only: continue
        ctx = browser.new_context(locale="en-US", viewport={"width": 1280, "height": 1800},
                                  user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
        page = ctx.new_page()
        found, gql_calls = {}, [0]
        def on_resp(resp):
            if "/api/graphql" in resp.url:
                gql_calls[0] += 1
                try:
                    for obj in parse_body(resp.text()): walk(obj, found)
                except Exception: pass
        page.on("response", on_resp)
        r = {"handle": h, "error": None}
        t0 = time.time()
        try:
            page.goto(f"https://www.facebook.com/{h}", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)
            for label in ["Decline optional cookies", "Only allow essential cookies", "Allow all cookies"]:
                try:
                    b = page.get_by_role("button", name=label).first
                    if b.is_visible(timeout=1500): b.click(timeout=3000); page.wait_for_timeout(2500); r["cookie_banner"] = label; break
                except Exception: pass
            # initial HTML also embeds the first stories as JSON in <script> tags
            for s in page.locator("script[type='application/json']").all():
                try: walk(json.loads(s.inner_text()), found)
                except Exception: pass
            wall_at = None; stall = 0
            for i in range(MAX_SCROLLS):
                for sel in ["div[aria-label='Close']", "[aria-label='Close']"]:
                    try:
                        if page.locator(sel).first.is_visible(timeout=300): page.locator(sel).first.click(timeout=1000)
                    except Exception: pass
                before = gql_calls[0]
                page.mouse.wheel(0, 3000); page.wait_for_timeout(2500)
                login_wall = page.locator("text=/See more on Facebook|Log in to continue|You must log in/i").first
                try: wall_visible = login_wall.is_visible(timeout=300)
                except Exception: wall_visible = False
                if wall_visible and wall_at is None: wall_at = i
                times = found.get("_times", [])
                if sum(t < cutoff for t in set(times)) >= 4: break  # pinned/featured items can be old
                stall = stall + 1 if gql_calls[0] == before else 0
                if stall >= 6: break
            times = sorted(set(found.get("_times", [])))
            posts = [k for k in found if not k.startswith("_")]
            mets = found.get("_metric_nodes", [])
            r.update({
                "post_ids_seen": len(posts), "gql_calls": gql_calls[0], "login_wall_after_scroll": wall_at, "scrolls": i + 1,
                "oldest": datetime.fromtimestamp(times[0], timezone.utc).date().isoformat() if times else None,
                "newest": datetime.fromtimestamp(times[-1], timezone.utc).date().isoformat() if times else None,
                "reached_3_months": sum(t < cutoff for t in times) >= 4, "in_window_times": sum(t >= cutoff for t in times),
                "metric_nodes": len(mets),
                "with_reaction": sum(m["reaction"] is not None for m in mets),
                "with_share": sum(m["share"] is not None for m in mets),
                "with_comments": sum(m["comments"] is not None for m in mets),
                "metric_samples": mets[:3],
            })
            page.screenshot(path=f"out/fb_{h}.png")
        except Exception as e:
            r["error"] = f"{type(e).__name__}: {str(e)[:300]}"
        r["seconds"] = round(time.time() - t0, 1)
        results.append(r); print(json.dumps(r, default=str), flush=True)
        ctx.close(); time.sleep(5)
    browser.close()
json.dump(results, open("out/fb_playwright.json", "w"), indent=2, default=str)
