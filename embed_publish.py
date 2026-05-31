# -*- coding: utf-8 -*-
"""
嘗試正確的 publish 方式：
把 CSS 嵌入 <style id="app-styles">，把 JS 嵌入 <script id="app-bundle">
讓平台能正確服務
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

# 重新 compile
print("=== 1. Compile ===")
c = api("POST", f"/compile/compile/{SLUG}", None, token)
print("success:", c.get("success"), "errors:", len(c.get("compile_errors", [])))

html_shell = c.get("html", "")
bundle_js = c.get("bundle_js", "")
css = c.get("css", "")
print("html: %d, bundle_js: %d, css: %d" % (len(html_shell), len(bundle_js), len(css)))

# 方法 A: 把 CSS 和 JS 直接嵌入 HTML
print("\n=== 2. 嵌入 CSS/JS 到 HTML ===")
# 只取 minified CSS（source map 之前的部分）
sm_idx = css.find("/*# sourceMappingURL")
if sm_idx > 0:
    clean_css = css[:sm_idx].strip()
    print("Clean CSS (no source map): %d bytes" % len(clean_css))
else:
    clean_css = css

# 組合完整 HTML
full_html = html_shell.replace(
    '<style id="app-styles"></style>',
    '<style id="app-styles">' + clean_css + '</style>'
).replace(
    '<script id="app-bundle"></script>',
    '<script id="app-bundle">' + bundle_js + '</script>'
)
print("Full HTML with embedded assets: %d bytes" % len(full_html))

# 驗證嵌入成功
print("HTML contains 'kpi-card.danger{background':", "kpi-card.danger{background" in full_html)
print("HTML contains 'donut-wrap':", "donut-wrap" in full_html)
print("HTML contains app-styles CSS:", '<style id="app-styles">:root' in full_html)
print("HTML contains app-bundle JS:", '<script id="app-bundle">import' in full_html)

# 方法 B: 也同時以分離方式 publish
print("\n=== 3. Publish (兩種方式) ===")

# 方式 1: 只發 full_html（CSS/JS 已嵌入）
print("  方式 1: 嵌入式 HTML")
r = api("POST", f"/builder/apps/{APP}/publish", {
    "published_assets": {
        "html": full_html,
        "bundle_js": bundle_js,
        "css": css,
    }
}, token)
print("  Result:", "OK" if r and "_error" not in r else "FAIL: " + str(r))

# 驗證
time.sleep(2)
app2 = api("GET", f"/builder/apps/{APP}", None, token)
pa = app2.get("published_assets", {})
published_html = pa.get("html", "")
print("\n=== 4. 驗證 ===")
print("Published HTML length: %d" % len(published_html))
print("Published HTML has embedded CSS:", "kpi-card.danger{background" in published_html)
print("Published HTML has embedded JS:", "donut-wrap" in published_html)
print("Published HTML has <style id='app-styles'> with content:", 
      '<style id="app-styles">:root' in published_html)

# 輸出 HTML 前 500 和後 500 字元
print("\nHTML head:")
print(published_html[:500])
print("\nHTML tail:")
print(published_html[-300:])
