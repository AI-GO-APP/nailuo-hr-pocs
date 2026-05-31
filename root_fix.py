# -*- coding: utf-8 -*-
"""
根本修復：
1. CSS :root 改為 :host, :root（讓 Shadow DOM 也能套用）
2. published_assets 清空（和成功 app 一樣）
3. 只依賴 published_vfs
"""
import json, urllib.request, ssl, time
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
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# 1. 讀取現有 CSS
app_data = api("GET", f"/builder/apps/{APP}", None, token)
pvfs = app_data.get("published_vfs", {})
old_css = pvfs.get("src/App.css", "")

# 2. 修正 :root → :host, :root
print("=== 1. Fix CSS :root → :host, :root ===")
if old_css.startswith(":root {"):
    new_css = ":host, :root {" + old_css[len(":root {"):]
    print("Fixed :root to :host, :root")
elif old_css.startswith(":host, :root {"):
    new_css = old_css
    print("Already has :host, :root")
else:
    new_css = old_css
    print("WARNING: Unexpected CSS start:", repr(old_css[:50]))

# 也修復 html,body,#root 的 overflow:hidden 問題
# 成功 app 沒有 overflow:hidden，我們有 → 可能導致 scroll 問題
new_css = new_css.replace(
    "html,body,#root{height:100%;overflow:hidden}",
    "html,body,#root{height:100%}"
).replace(
    "html, body, #root {\n  height: 100%;\n  overflow: hidden;\n}",
    "html, body, #root {\n  height: 100%;\n}"
)

print("CSS length: %d → %d" % (len(old_css), len(new_css)))
print("Has :host:", ":host" in new_css[:20])

# 3. Upload CSS
print("\n=== 2. Upload fixed CSS ===")
r = api("PATCH", f"/builder/apps/{APP}/source/files", {
    "files": {"src/App.css": new_css}
}, token)
print("Upload:", "OK" if r and "_error" not in r else "FAIL")

# 4. Publish with empty assets to sync VFS + mimic good app
print("\n=== 3. Publish (empty assets, sync VFS) ===")
r = api("POST", f"/builder/apps/{APP}/publish", {
    "published_assets": {"html": "", "bundle_js": "", "css": ""}
}, token)
print("Publish:", "OK" if r and "_error" not in r else "FAIL")

# 5. Verify
time.sleep(2)
app2 = api("GET", f"/builder/apps/{APP}", None, token)
pvfs2 = app2.get("published_vfs", {})
css2 = pvfs2.get("src/App.css", "")
pa2 = app2.get("published_assets", {})
print("\n=== 4. Verification ===")
print("published_vfs App.css length:", len(css2))
print("CSS starts with ':host, :root':", css2.startswith(":host, :root {"))
print("Has donut-wrap:", "donut-wrap" in css2)
print("Has kpi-card.danger bg:", "kpi-card.danger { background:" in css2)
print("Has v2 Additions:", "v2 Additions" in css2)
print("published_assets html:", len(pa2.get("html", "")), "bytes")
print("published_assets css:", len(pa2.get("css", "")), "bytes")
print("published_assets bundle_js:", len(pa2.get("bundle_js", "")), "bytes")

# Also check if overflow:hidden was removed
print("Has overflow:hidden:", "overflow:hidden" in css2 or "overflow: hidden" in css2)

# 6. 對比成功 app 的結構
print("\n=== 5. 結構對比 ===")
good = api("GET", "/builder/apps/da7789b4-59bc-422c-8e7b-b6a7b9103146", None, token)
good_pa = good.get("published_assets", {})
print("Good app published_assets html:", len(good_pa.get("html", "")))
print("Good app published_assets css:", len(good_pa.get("css", "")))
print("Good app published_assets bundle_js:", len(good_pa.get("bundle_js", "")))
print("Our app published_assets html:", len(pa2.get("html", "")))
print("Our app published_assets css:", len(pa2.get("css", "")))
print("Our app published_assets bundle_js:", len(pa2.get("bundle_js", "")))
print("\nBoth have empty published_assets:", 
      len(good_pa.get("html", "")) == 0 and len(pa2.get("html", "")) == 0)

print("\n===== DONE =====")
print("請 Ctrl+Shift+R 重整: https://tslg-churn-analysis-manager.ai-go.app")
