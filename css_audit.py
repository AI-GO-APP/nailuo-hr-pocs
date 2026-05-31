# -*- coding: utf-8 -*-
"""
驗證 CSS minification 問題：
1. 確認 compiled CSS 中的 kpi-card.danger 規則是否只有 .kpi-value 那個
2. 確認 v2 additions 在 compiled CSS 中的位置
3. 確認 compiled CSS 中是否包含 source map 行
"""
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
app_data = api("GET", f"/builder/apps/{APP}", None, token)
css = app_data.get("published_assets", {}).get("css", "")

print("Total CSS length: %d bytes" % len(css))

# CSS 分行
lines = css.split("\n")
print("Total lines: %d" % len(lines))

# 找 source map
for i, line in enumerate(lines):
    if "sourceMappingURL" in line:
        print("\nSource map at line %d (pos %d)" % (i+1, css.find("sourceMappingURL")))
        print("Line length: %d" % len(line))
        print("Line preview: %s" % line[:100])
        
        # 計算 source map 之前和之後的 CSS 大小
        sm_pos = css.find("/*# sourceMappingURL")
        before = css[:sm_pos]
        after = css[sm_pos:]
        print("\nCSS BEFORE source map: %d bytes" % len(before))
        print("CSS AFTER source map: %d bytes" % len(after))
        
        # 檢查 source map 之前有哪些 kpi-card 規則
        print("\nkpi-card rules BEFORE source map:")
        pos = 0
        while True:
            idx = before.find("kpi-card", pos)
            if idx == -1:
                break
            ctx = before[max(0,idx-30):idx+80]
            print("  pos %d: ...%s..." % (idx, repr(ctx)))
            pos = idx + 1
        
        # 檢查 source map 之後有哪些 kpi-card 規則
        print("\nkpi-card rules AFTER source map:")
        pos = 0
        while True:
            idx = after.find("kpi-card", pos)
            if idx == -1:
                break
            ctx = after[max(0,idx-30):idx+80]
            print("  pos %d: ...%s..." % (idx, repr(ctx)))
            pos = idx + 1
        
        break

# 找 minified CSS 中的 .kpi-card.danger 完整規則
print("\n\n=== Minified CSS 中所有 .kpi-card.danger 規則 ===")
pos = 0
count = 0
while True:
    idx = css.find(".kpi-card.danger", pos)
    if idx == -1:
        break
    count += 1
    # 從上一個 } 到下一個 } 擷取完整規則
    rule_start = css.rfind("}", 0, idx)
    rule_end = css.find("}", idx)
    if rule_start >= 0 and rule_end >= 0:
        rule = css[rule_start+1:rule_end+1]
        print("  #%d (pos %d): %s" % (count, idx, repr(rule.strip())))
    pos = idx + 1

print("\nTotal .kpi-card.danger rules: %d" % count)

# 最關鍵問題：compiled CSS 是否真的把 v2 additions 包含在有效 CSS 中？
# 搜索 "donut-wrap" 在 compiled CSS 中
print("\n=== 確認 v2 CSS 在 compiled CSS 中的位置 ===")
for key in ["donut-wrap", "risk-circle", "btn-export", "kpi-card.danger{background"]:
    idx = css.find(key)
    if idx >= 0:
        sm_pos = css.find("/*# sourceMappingURL")
        is_before = idx < sm_pos if sm_pos >= 0 else True
        print("  '%s' at pos %d (%s source map)" % (key, idx, "BEFORE" if is_before else "AFTER"))
    else:
        print("  '%s' NOT FOUND" % key)
