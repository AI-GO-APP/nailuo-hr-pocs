# -*- coding: utf-8 -*-
"""
徹底排查：為什麼 VFS 更新了、compile 成功、publish 完成，但前端樣式不變？
需要搞清楚：
1. published_assets 中的 css/bundle_js 是否真的被瀏覽器載入？
2. HTML 是如何引用 JS/CSS 的？
3. 是否存在平台級別的 CSS 覆蓋？
4. compile 產出的 CSS 中，我們的新規則是否真的存在且格式正確？
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

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)

pa = app_data.get("published_assets", {})
html = pa.get("html", "")
bundle_js = pa.get("bundle_js", "")
css = pa.get("css", "")

print("=" * 70)
print("排查一：HTML 完整內容（看如何引用 JS/CSS）")
print("=" * 70)
print(html)

print("\n" + "=" * 70)
print("排查二：CSS 中的 kpi-card 相關規則（全部列出）")
print("=" * 70)
# 找到所有包含 kpi-card 的 CSS 規則
import re
# 簡單做法：在 CSS 中搜索 kpi-card
css_lines = css.split("\n")
for i, line in enumerate(css_lines):
    if "kpi-card" in line:
        # 印出上下文
        start = max(0, i-1)
        end = min(len(css_lines), i+2)
        for j in range(start, end):
            print("  CSS-L%d: %s" % (j+1, css_lines[j][:200]))
        print()

# 也直接搜索特定字串
print("\n" + "=" * 70)
print("排查三：CSS 關鍵字串搜索")
print("=" * 70)
searches = [
    "kpi-card.danger",
    ".kpi-card.danger",
    "danger-light",
    "donut-wrap",
    "donut-center",
    "risk-circle",
    "btn-export",
    "new-tag",
    "v2 Additions",
]
for s in searches:
    idx = css.find(s)
    if idx >= 0:
        ctx = css[max(0,idx-20):idx+80]
        print("  FOUND '%s' at pos %d: ...%s..." % (s, idx, repr(ctx)))
    else:
        print("  NOT FOUND: '%s'" % s)

print("\n" + "=" * 70)
print("排查四：Bundle JS 頭部（看模組結構）")
print("=" * 70)
print(bundle_js[:500])

print("\n" + "=" * 70)
print("排查五：Bundle JS 中搜尋關鍵元件")
print("=" * 70)
js_searches = [
    "donut-wrap",
    "donut-center",
    "kpi-card danger",
    'kpi-card","danger',
    "risk-circle",
    "btn-export",
    "匯出",
    "Download",
    "syncMin",
    "sync-badge",
    "共勤",
    "LayoutDashboard",
    "new-tag",
    "panel-head",
    "btn btn-primary",
    "loadAI",
    "Brain",
]
for s in js_searches:
    idx = bundle_js.find(s)
    if idx >= 0:
        ctx = bundle_js[max(0,idx-30):idx+50]
        print("  FOUND '%s' at pos %d: ...%s..." % (s, idx, repr(ctx)))
    else:
        print("  NOT FOUND: '%s'" % s)

print("\n" + "=" * 70)
print("排查六：published_vfs 的 App.css 末尾（確認 v2 CSS 是否真的在源頭）")
print("=" * 70)
vfs_css = app_data.get("published_vfs", {}).get("src/App.css", "")
print("Total length: %d chars" % len(vfs_css))
print("Last 500 chars:")
print(vfs_css[-500:])

print("\n" + "=" * 70)
print("排查七：探測 Custom App 平台的 API 端點")
print("=" * 70)
# 檢查 app 的完整欄位
app_keys = list(app_data.keys())
print("App data keys:", app_keys)
print("App status:", app_data.get("status"))
print("App slug:", app_data.get("slug"))
print("App subdomain:", app_data.get("subdomain"))
print("published_at:", app_data.get("published_at"))
# 看有沒有其他相關端點
for endpoint in [
    f"/builder/apps/{APP}/preview",
    f"/builder/apps/{APP}/runtime",
    f"/builder/apps/{APP}/assets",
]:
    r = api("GET", endpoint, None, token)
    print("GET %s: %s" % (endpoint, json.dumps(r, ensure_ascii=False)[:200] if r else "None"))
