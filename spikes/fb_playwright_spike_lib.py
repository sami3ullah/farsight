import json
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

