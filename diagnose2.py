# -*- coding: utf-8 -*-
"""
深入分析 Bundle JS — 找出為什麼 published_vfs 有新內容但 bundle 沒有
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
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# 重新 compile
print("=== COMPILE (fresh) ===")
c = api("POST", f"/compile/compile/{SLUG}", None, token)
print("success:", c.get("success"))
print("errors:", len(c.get("compile_errors", [])))
for e in c.get("compile_errors", []):
    print("  ERROR:", json.dumps(e, ensure_ascii=False)[:200])

new_bundle = c.get("bundle_js", "")
new_css = c.get("css", "")
new_html = c.get("html", "")
print("html:", len(new_html), "bytes")
print("bundle_js:", len(new_bundle), "bytes")
print("css:", len(new_css), "bytes")

# 檢查新 bundle 內容
print("\n=== NEW BUNDLE 內容 ===")
print("Contains 'DonutChart':", "DonutChart" in new_bundle)
print("Contains 'donut-wrap':", "donut-wrap" in new_bundle)
print("Contains 'donut-center':", "donut-center" in new_bundle)
print("Contains 'BarChart':", "BarChart" in new_bundle)
print("Contains 'bar-chart':", "bar-chart" in new_bundle)
print("Contains 'RiskCircle':", "RiskCircle" in new_bundle)
print("Contains 'risk-circle':", "risk-circle" in new_bundle)
print("Contains '匯出':", "匯出" in new_bundle or "\\u532f\\u51fa" in new_bundle)
print("Contains 'Download':", "Download" in new_bundle)
print("Contains 'syncMin':", "syncMin" in new_bundle)
print("Contains '共勤':", "共勤" in new_bundle)
print("Contains 'LayoutDashboard':", "LayoutDashboard" in new_bundle)

# 檢查新 CSS 內容
print("\n=== NEW CSS 內容 ===")
print("Contains 'donut-wrap':", "donut-wrap" in new_css)
print("Contains 'risk-circle':", "risk-circle" in new_css)

# 比較新舊 bundle
app_data = api("GET", f"/builder/apps/{APP}", None, token)
old_bundle = app_data.get("published_assets", {}).get("bundle_js", "")
old_css_pub = app_data.get("published_assets", {}).get("css", "")
print("\n=== OLD vs NEW 比較 ===")
print("Old bundle: %d bytes" % len(old_bundle))
print("New bundle: %d bytes" % len(new_bundle))
print("Bundle changed:", old_bundle != new_bundle)
print("Old CSS: %d bytes" % len(old_css_pub))
print("New CSS: %d bytes" % len(new_css))
print("CSS changed:", old_css_pub != new_css)

# 如果新舊不同，publish 新版本
if new_bundle != old_bundle or new_css != old_css_pub:
    print("\n=== PUBLISHING NEW ASSETS ===")
    assets = {"html": new_html}
    if new_bundle:
        assets["bundle_js"] = new_bundle
    if new_css:
        assets["css"] = new_css
    r = api("POST", f"/builder/apps/{APP}/publish", {"published_assets": assets}, token)
    print("Publish:", "OK" if r and "_error" not in r else "FAIL: " + str(r))
    
    # 驗證 publish 成功
    import time
    time.sleep(2)
    app2 = api("GET", f"/builder/apps/{APP}", None, token)
    pa2 = app2.get("published_assets", {})
    print("\nVerification after publish:")
    print("  bundle_js: %d bytes" % len(pa2.get("bundle_js", "")))
    print("  css: %d bytes" % len(pa2.get("css", "")))
    print("  html: %d bytes" % len(pa2.get("html", "")))
    print("  Bundle matches new:", pa2.get("bundle_js", "") == new_bundle)
    print("  CSS matches new:", pa2.get("css", "") == new_css)
else:
    print("\n=== NO CHANGES - Bundle/CSS identical ===")
    print("This means the compile is NOT picking up VFS changes!")
    print("Possible cause: compiler caches the build")
