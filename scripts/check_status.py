import json
import os

TRACKER_JSON = os.path.join("translations", "tracker.json")
if os.path.exists(TRACKER_JSON):
    with open(TRACKER_JSON, "r", encoding="utf-8") as f:
        t = json.load(f)
    print(f"Total entries in tracker: {len(t)}")
    keys = sorted([int(k) for k in t.keys()])
    verified = [k for k in keys if t[str(k)].get("status") == "VERIFIED"]
    print(f"Verified count: {len(verified)}")
    print(f"Min verified: {min(verified) if verified else None}, Max verified: {max(verified) if verified else None}")
    
    # Check ranges
    ranges = []
    start = keys[0]
    prev = keys[0]
    for k in keys[1:]:
        if k == prev + 1:
            prev = k
        else:
            ranges.append((start, prev))
            start = k
            prev = k
    ranges.append((start, prev))
    print("Ranges present in tracker:", ranges)
