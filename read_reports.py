# -*- coding: utf-8 -*-
import json

for label, cid in [("DASHBOARD", "64bc4e59-7906-4a7a-8515-5f7a8a7454ce"), ("TARGET_APP", "d93443f3-17ca-4400-8d35-c88b83ef137e")]:
    path = rf"C:\Users\User\.gemini\antigravity\brain\{cid}\.system_generated\logs\transcript.jsonl"
    print("\n" + "=" * 70)
    print(f"  {label}")
    print("=" * 70)
    with open(path, "r", encoding="utf-8") as f:
        last_model = ""
        for line in f:
            j = json.loads(line)
            if j.get("source") == "MODEL" and j.get("content") and len(j["content"]) > 500:
                last_model = j["content"]
        print(last_model[:8000])
        if len(last_model) > 8000:
            print(f"...(truncated, total {len(last_model)} chars)")
