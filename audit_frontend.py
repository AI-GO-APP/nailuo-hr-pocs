# -*- coding: utf-8 -*-
"""全面盤點前端元件"""
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
vfs = app_data.get("vfs_state", {})

# 完整列出所有檔案
print("=" * 60)
print("VFS 完整檔案清單")
print("=" * 60)
for path in sorted(vfs.keys()):
    content = vfs[path]
    print(f"  {path}: {len(content)} chars")

# 逐一檢查各元件
print("\n" + "=" * 60)
print("各元件內容檢查")
print("=" * 60)

# 1. main.tsx
print("\n--- 1. main.tsx ---")
main = vfs.get("src/main.tsx", "")
print(main)

# 2. App.tsx
print("\n--- 2. App.tsx ---")
app = vfs.get("src/App.tsx", "")
print(app)

# 3. routes.ts
print("\n--- 3. routes.ts ---")
routes = vfs.get("src/routes.ts", "")
print(routes)

# 4. action.ts (只看關鍵行)
print("\n--- 4. action.ts (key lines) ---")
at = vfs.get("src/action.ts", "")
for line in at.split("\n"):
    line_s = line.strip()
    if any(kw in line_s for kw in ["actionUrl", "API_BASE", "result.result", "result.data", "return {"]):
        print(f"  {line_s}")

# 5. components
for comp in ["AppLayout", "AppHeader", "AppSidebar"]:
    path = f"src/components/{comp}.tsx"
    content = vfs.get(path, "")
    print(f"\n--- 5. {path} ({len(content)} chars) ---")
    print(content[:500])
    if len(content) > 500:
        print("  ... [truncated]")

# 6. pages - 逐一檢查
for page in ["DashboardPage", "SalesPage", "CategoriesPage", "DataSourcePage", "NotFoundPage"]:
    path = f"src/pages/{page}.tsx"
    content = vfs.get(path, "")
    print(f"\n--- 6. {path} ({len(content)} chars) ---")
    # 檢查關鍵元素
    checks = {
        "import runAction": "import { runAction" in content,
        "useState": "useState" in content,
        "useEffect": "useEffect" in content,
        "Loader2": "Loader2" in content,
        "r.data || r": "r.data || r" in content or "r.data" in content,
        "error handling": "setError" in content or "catch" in content,
        "中文標題": any(ord(c) > 0x4E00 for c in content[:200]),
        "backslash-u": "\\u" in content[:200],
    }
    for check, result in checks.items():
        status = "OK" if result else "MISSING"
        if check == "backslash-u":
            status = "BAD" if result else "OK"
        print(f"  [{status}] {check}")
    
    # 看前幾行
    lines = content.split("\n")[:5]
    for l in lines:
        print(f"  > {l[:100]}")

# 7. CSS
print(f"\n--- 7. App.css ({len(vfs.get('src/App.css', ''))} chars) ---")
css = vfs.get("src/App.css", "")
css_classes = []
for line in css.split("\n"):
    if line.strip().startswith(".") and "{" in line:
        cls = line.strip().split("{")[0].strip()
        css_classes.append(cls)
print(f"  Total CSS classes: {len(css_classes)}")
# 檢查關鍵 CSS class
needed = [".page", ".kpi-grid", ".kpi-card", ".panel", ".sidebar", ".badge", ".btn", ".bar-chart",
          ".top-list", ".ai-reason-box", ".cat-tabs", ".cat-tab", ".dashboard-grid", ".sales-grid",
          ".data-status-card", ".connector-list", ".spin"]
for cls in needed:
    found = any(cls in c for c in css_classes)
    print(f"  [{'OK' if found else 'MISSING'}] {cls}")

# 8. package.json
print(f"\n--- 8. package.json ---")
pkg = vfs.get("package.json", "")
print(pkg)

# 9. db.ts 和 api.ts
print(f"\n--- 9. db.ts ({len(vfs.get('src/db.ts', ''))} chars) ---")
print(f"--- 9. api.ts ({len(vfs.get('src/api.ts', ''))} chars) ---")

# 10. actions
print(f"\n--- 10. actions ---")
manifest = vfs.get("actions/manifest.json", "")
print(f"  manifest.json: {manifest}")
for f in sorted(vfs.keys()):
    if f.startswith("actions/") and f != "actions/manifest.json":
        print(f"  {f}: {len(vfs[f])} chars")

# 11. 空檔案或殘留檔案
print(f"\n--- 11. 空或殘留檔案 ---")
for path, content in sorted(vfs.items()):
    if len(content) <= 10:
        print(f"  WARNING: {path} = {repr(content)}")

print("\n" + "=" * 60)
print("盤點完成")
print("=" * 60)
