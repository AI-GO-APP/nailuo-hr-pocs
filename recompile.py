# -*- coding: utf-8 -*-
"""完整重新 compile + publish，並檢查 HTML 產出"""
import json, urllib.request, ssl, time
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

# Compile
print("=== Compile ===")
c = api("POST", "/compile/compile/da1900f990b0", None, token)
print("success:", c.get("success"))
print("errors:", len(c.get("compile_errors", [])))
html = c.get("html", "")
print("HTML length:", len(html))
print("HTML preview:", repr(html[:500]))

# 如果有 error key
if c.get("error"):
    print("Error:", c["error"][:300])

# 完整 response keys
print("Response keys:", list(c.keys()))

# 如果 HTML 太短，可能是 shell
if len(html) < 1000:
    print("\nWARNING: HTML is only %d bytes - this is likely just the shell, not a full React app" % len(html))
    print("The app might be loading JS bundles separately")
    
# Publish with new HTML
if c.get("success") and html:
    print("\n=== Publish ===")
    r = api("POST", f"/builder/apps/{APP}/publish", {
        "published_assets": {"html": html}
    }, token)
    print("Publish:", "OK" if r and "_error" not in r else "FAIL")
    if r and "_error" not in r:
        print("Response keys:", list(r.keys()) if isinstance(r, dict) else type(r))
