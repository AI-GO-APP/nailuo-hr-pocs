# -*- coding: utf-8 -*-
import json, urllib.request, ssl, time
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:300]
        print(f"  HTTP {e.code}: {err}")
        return None

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# Set OPENAI_API_KEY via settings PATCH
print("Setting OPENAI_API_KEY...")
r = api("PATCH", f"/builder/apps/{APP}/settings", {
    "secrets": {"OPENAI_API_KEY": "sk-proj-placeholder-will-be-set-later"}
}, token)
if r:
    # Check if secrets is in response
    for k in r:
        if "secret" in k.lower():
            print(f"  {k}: {str(r[k])[:100]}")
    print("  PATCH settings OK")
else:
    print("  PATCH settings FAILED")

# Test the action
time.sleep(1)
print("\nTesting dashboard action...")
r2 = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights", {"params": {"action": "dashboard"}}, token)
if r2:
    status = r2.get("status", "?")
    result = r2.get("result", {})
    insight = result.get("ai_insight", "")
    error = r2.get("error", "")
    print(f"  status: {status}")
    print(f"  ai_insight: {insight[:200]}")
    if error:
        print(f"  error: {error}")
    # Print KPI
    kpi = result.get("kpi", {})
    print(f"  KPI: {json.dumps(kpi, ensure_ascii=False)}")
