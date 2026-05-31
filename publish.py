# -*- coding: utf-8 -*-
"""正式發佈"""
import json, urllib.request, ssl
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

slug = "da1900f990b0"

# Compile production
c = api("POST", f"/compile/compile/{slug}", None, token)
html = c.get("html", "")
success = c.get("success")
errors = c.get("compile_errors", [])
print(f"Compile: success={success}, html_len={len(html)}, errors={len(errors)}")
for e in errors:
    print(f"  Error: {e}")

# Publish
r = api("POST", f"/builder/apps/{APP}/publish", {"published_assets": {"html": html}}, token)
if "_error" not in r:
    subdomain = r.get("subdomain", "?")
    print(f"Published! subdomain={subdomain}")
    print(f"URL: https://{subdomain}.ai-go.app")
else:
    print(f"Publish error: {json.dumps(r, ensure_ascii=False)[:300]}")

# Also update action manifest
manifest = {
    "actions": [
        {"name": "analyze_churn", "file": "actions/analyze_churn.py", "description": "客戶流失風險分析"},
        {"name": "fetch_crm_data", "file": "actions/fetch_crm_data.py", "description": "CRM 資料查詢"}
    ]
}
r2 = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": {"actions/manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2)}}, token)
print(f"Manifest updated: {'OK' if r2 and '_error' not in r2 else 'FAIL'}")

# Re-compile and re-publish with manifest
c2 = api("POST", f"/compile/compile/{slug}", None, token)
html2 = c2.get("html", "")
r3 = api("POST", f"/builder/apps/{APP}/publish", {"published_assets": {"html": html2}}, token)
print(f"Re-published: {'OK' if r3 and '_error' not in r3 else 'FAIL'}")

print("\nDone!")
