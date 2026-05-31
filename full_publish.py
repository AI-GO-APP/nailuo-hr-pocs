# -*- coding: utf-8 -*-
"""完整 publish：包含 html + bundle_js + css"""
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
bundle_js = c.get("bundle_js", "")
css = c.get("css", "")
print("html:", len(html), "bytes")
print("bundle_js:", len(bundle_js), "bytes")
print("css:", len(css), "bytes")

if not c.get("success"):
    for e in c.get("compile_errors", []):
        print("  ERROR:", json.dumps(e, ensure_ascii=False)[:200])
    exit(1)

# 檢查 bundle_js 中是否包含我們的元件
if "CategoriesPage" in bundle_js or "panel-head" in bundle_js:
    print("bundle_js contains our components: YES")
else:
    print("bundle_js contains our components: NO (might be a problem)")

if "btn-primary" in bundle_js or "btn btn-primary" in css:
    print("btn-primary style found: YES")

# 檢查 bundle_js 前面
print("\nbundle_js preview:", repr(bundle_js[:200]))
print("css preview:", repr(css[:200]))

# Publish with ALL assets
print("\n=== Publish with full assets ===")
published_assets = {"html": html}
if bundle_js:
    published_assets["bundle_js"] = bundle_js
if css:
    published_assets["css"] = css

r = api("POST", f"/builder/apps/{APP}/publish", {
    "published_assets": published_assets
}, token)
print("Publish:", "OK" if r and "_error" not in r else "FAIL")

# Verify
time.sleep(1)
app_data = api("GET", f"/builder/apps/{APP}", None, token)
pa = app_data.get("published_assets", {})
print("\nVerification - published_assets:")
for k, v in pa.items():
    print("  %s: %d bytes" % (k, len(v) if isinstance(v, str) else 0))
