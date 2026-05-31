# -*- coding: utf-8 -*-
"""
找出 Custom App 平台如何提供 CSS/JS
1. 嘗試各種可能的 asset 端點
2. 檢查 HTML 中是否有其他載入機制
3. 查看模板 app 的結構
"""
import json, urllib.request, ssl
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"
SLUG = "da1900f990b0"

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

def api_raw(m, p, t=None):
    req = urllib.request.Request(f"{BASE}{p}", method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()[:2000]
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:500]

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# 嘗試所有可能的端點來找出 JS/CSS 的載入機制
print("=== 探測 Asset 端點 ===")
endpoints = [
    f"/apps/{SLUG}",
    f"/apps/{SLUG}/bundle.js",
    f"/apps/{SLUG}/styles.css",
    f"/apps/{SLUG}/assets",
    f"/custom-apps/{SLUG}",
    f"/custom-apps/{APP}",
    f"/runtime/apps/{SLUG}",
    f"/runtime/apps/{APP}",
    f"/builder/apps/{APP}/bundle",
    f"/builder/apps/{APP}/css",
    f"/builder/apps/{APP}/js",
    f"/compile/bundle/{SLUG}",
    f"/compile/css/{SLUG}",
    f"/compile/assets/{SLUG}",
]
for ep in endpoints:
    code, body = api_raw("GET", ep, token)
    print("  GET %s -> %d (%d bytes)" % (ep, code, len(body)))
    if code == 200:
        print("    Preview: %s" % body[:150])

# 也直接嘗試 app 的 subdomain URL 的各種路徑
print("\n=== 嘗試直接 URL ===")
for url in [
    "https://ai-go.app/apps/da1900f990b0",
    "https://ai-go.app/apps/da1900f990b0/bundle.js",
    "https://ai-go.app/custom/da1900f990b0",
]:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as r:
            print("  GET %s -> %d (%d bytes)" % (url, r.status, len(r.read()[:100])))
    except Exception as e:
        print("  GET %s -> %s" % (url, str(e)[:100]))

# 查看 _template_meta.json
print("\n=== Template Meta ===")
app_data = api("GET", f"/builder/apps/{APP}", None, token)
pvfs = app_data.get("published_vfs", {})
meta = pvfs.get("_template_meta.json", "")
print("  _template_meta.json:", meta)

# 查看 package.json
pkg = pvfs.get("package.json", "")
print("\n  package.json:", pkg)

# 查看 main.tsx
main = pvfs.get("src/main.tsx", "")
print("\n  src/main.tsx:", main)

# 查看完整 HTML
html = app_data.get("published_assets", {}).get("html", "")
print("\n=== Published HTML (full) ===")
print(html)

# 再看看 compile 返回的完整結構
print("\n=== Compile Response Structure ===")
c = api("POST", f"/compile/compile/{SLUG}", None, token)
for k, v in c.items():
    if isinstance(v, str):
        print("  %s: %d chars, preview: %s" % (k, len(v), repr(v[:100])))
    elif isinstance(v, list):
        print("  %s: list of %d items" % (k, len(v)))
    elif isinstance(v, bool):
        print("  %s: %s" % (k, v))
    else:
        print("  %s: %s" % (k, type(v)))
