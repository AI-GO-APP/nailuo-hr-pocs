# -*- coding: utf-8 -*-
"""
模仿成功 app 的方式：published_assets 設為空，只依賴 published_vfs
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

# 1. 確認 published_vfs 中的 App.css 確實有新規則
app_data = api("GET", f"/builder/apps/{APP}", None, token)
pvfs = app_data.get("published_vfs", {})
css = pvfs.get("src/App.css", "")
print("=== 1. published_vfs App.css 檢查 ===")
print("Length:", len(css))
print("Has kpi-card.danger bg:", "kpi-card.danger { background:" in css or "kpi-card.danger{background" in css)
print("Has donut-wrap:", "donut-wrap" in css)
print("Has risk-circle:", "risk-circle" in css)
print("Has v2 Additions:", "v2 Additions" in css)

# 2. 模仿成功 app: 清空 published_assets
print("\n=== 2. 清空 published_assets (模仿成功 app) ===")
r = api("POST", f"/builder/apps/{APP}/publish", {
    "published_assets": {
        "html": "",
        "bundle_js": "",
        "css": "",
    }
}, token)
print("Publish with empty assets:", "OK" if r and "_error" not in r else "FAIL: " + str(r))

# 3. 驗證
time.sleep(1)
app2 = api("GET", f"/builder/apps/{APP}", None, token)
pa2 = app2.get("published_assets", {})
print("\n=== 3. 驗證 published_assets ===")
for k, v in pa2.items():
    if isinstance(v, str):
        print("  %s: %d bytes" % (k, len(v)))

# 4. 確認 published_vfs 沒有被影響
pvfs2 = app2.get("published_vfs", {})
css2 = pvfs2.get("src/App.css", "")
print("\n=== 4. published_vfs 確認 ===")
print("App.css length:", len(css2))
print("Still has v2 CSS:", "v2 Additions" in css2)
print("Still has donut-wrap:", "donut-wrap" in css2)

# 5. 列出成功 app 的 published_vfs 中 App.css 的 :host 寫法
good = api("GET", "/builder/apps/da7789b4-59bc-422c-8e7b-b6a7b9103146", None, token)
good_css = good.get("published_vfs", {}).get("src/App.css", "")
print("\n=== 5. 成功 App 的 CSS 開頭 ===")
print("Start:", repr(good_css[:100]))
print("\n我們的 CSS 開頭:")
print("Start:", repr(css2[:100]))

# 關鍵差異：成功 app 用 :host, :root
print("\n=== 6. :host vs :root 差異 ===")
print("Good app uses ':host':", ":host" in good_css)
print("Our app uses ':host':", ":host" in css2)
print("Good app uses ':root':", ":root" in good_css)
print("Our app uses ':root':", ":root" in css2)

# 檢查成功 app 的 main.tsx
good_main = good.get("published_vfs", {}).get("src/main.tsx", "")
our_main = pvfs2.get("src/main.tsx", "")
print("\n=== 7. main.tsx 比較 ===")
print("Good main.tsx:")
print(good_main)
print("\nOur main.tsx:")
print(our_main)

print("\n===== DONE =====")
