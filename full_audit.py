# -*- coding: utf-8 -*-
"""
完整審查：
1. 規範合規問題
2. 未被使用的 VFS 檔案（死檔案）
3. 未被使用的 Custom Data Table
4. 未被使用的 Data Reference
5. 未被使用的 Action
6. 未被引用的元件/頁面
"""
import json, urllib.request, ssl, re
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "da7789b4-59bc-422c-8e7b-b6a7b9103146"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:300]}")
        return None

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]

print(f"VFS version: {app_data['vfs_version']}, 共 {len(vfs)} 個檔案")

# SDK 不可修改的檔案
SDK_FILES = {"src/api.ts", "src/db.ts", "src/action.ts", "src/data.json", "src/db.json"}
# 系統/設定檔
SYSTEM_FILES = {"package.json", "_template_meta.json", "actions/manifest.json"}

# =====================================================
# 1. 建立引用圖：每個檔案被哪些檔案 import
# =====================================================
all_content = {path: content for path, content in vfs.items()}
import_graph = {path: set() for path in vfs}  # path -> set of files that import it

for src_path, content in all_content.items():
    if not (src_path.endswith(".tsx") or src_path.endswith(".ts")):
        continue
    # 找所有 import 語句
    imports = re.findall(r'''(?:from|import)\s+['"](\.\.?/[^'"]+)['"]''', content)
    for imp in imports:
        # 解析相對路徑
        parts = src_path.split("/")
        imp_parts = imp.split("/")
        base_dir = "/".join(parts[:-1])
        resolved = []
        for p in imp_parts:
            if p == "..":
                base_dir = "/".join(base_dir.split("/")[:-1])
            elif p == ".":
                pass
            else:
                resolved.append(p)
        target_base = base_dir + "/" + "/".join(resolved) if base_dir else "/".join(resolved)
        # 嘗試不同副檔名
        for ext in ["", ".ts", ".tsx", ".json", ".css"]:
            target = target_base + ext
            if target in vfs:
                import_graph[target].add(src_path)
                break
        # 也嘗試 index
        for ext in ["/index.ts", "/index.tsx"]:
            target = target_base + ext
            if target in vfs:
                import_graph[target].add(src_path)

# =====================================================
# 2. 找出死檔案
# =====================================================
print("\n" + "=" * 80)
print("死檔案分析（VFS 中未被任何檔案 import 的）")
print("=" * 80)

# 入口點（不需要被 import）
entry_points = {"src/main.tsx", "src/App.css"}
entry_points.update(SDK_FILES)
entry_points.update(SYSTEM_FILES)
# Action 檔案（被 manifest 引用）
entry_points.update(p for p in vfs if p.startswith("actions/") and p.endswith(".py"))
entry_points.add("actions/manifest.json")

dead_files = []
for path in sorted(vfs):
    if path in entry_points:
        continue
    importers = import_graph.get(path, set())
    if not importers:
        dead_files.append(path)
        print(f"  ❌ {path} — 無任何檔案引用")

# =====================================================
# 3. 檢查 manifest.json 中的 actions vs 實際檔案
# =====================================================
print("\n" + "=" * 80)
print("Action 分析")
print("=" * 80)
manifest = json.loads(vfs.get("actions/manifest.json", "{}"))
actions = manifest.get("actions", [])
registered_files = set()
for act in actions:
    f = f"actions/{act.get('file', '')}"
    registered_files.add(f)
    exists = f in vfs
    used_in_code = act.get("name", "") in " ".join(all_content.get(p, "") for p in vfs if p.endswith((".tsx", ".ts")))
    print(f"  {'✅' if exists else '❌'} {act.get('name','?')} → {f} (exists={exists}, called_in_frontend={used_in_code})")

# 未被 manifest 引用的 action 檔案
orphan_actions = [p for p in vfs if p.startswith("actions/") and p.endswith(".py") and p not in registered_files]
for p in orphan_actions:
    print(f"  ⚠️  {p} — 不在 manifest.json 中，永遠不會被呼叫")

# =====================================================
# 4. 檢查 routes.ts 中的頁面 vs 實際頁面檔案
# =====================================================
print("\n" + "=" * 80)
print("頁面/路由分析")
print("=" * 80)
routes_ts = vfs.get("src/routes.ts", "")
app_tsx = vfs.get("src/App.tsx", "")
page_files = [p for p in vfs if p.startswith("src/pages/") and p.endswith(".tsx") and p != "src/pages/_manifest.json"]

for pf in sorted(page_files):
    basename = pf.split("/")[-1].replace(".tsx", "")
    in_routes = basename in routes_ts
    in_app = basename in app_tsx
    importers = import_graph.get(pf, set())
    if not importers:
        print(f"  ❌ {pf} — 未被 import（routes={in_routes}, App={in_app}）")
    else:
        print(f"  ✅ {pf} — imported by {list(importers)[:3]}")

# =====================================================
# 5. 檢查元件使用情況
# =====================================================
print("\n" + "=" * 80)
print("元件使用分析")
print("=" * 80)
comp_files = [p for p in vfs if p.startswith("src/components/") and p.endswith(".tsx")]
for cf in sorted(comp_files):
    basename = cf.split("/")[-1].replace(".tsx", "")
    importers = import_graph.get(cf, set())
    # 也檢查有沒有被 JSX 使用 <ComponentName
    jsx_users = []
    for src_path, content in all_content.items():
        if src_path == cf:
            continue
        if f"<{basename}" in content or f"import {{ {basename}" in content or f'from "' in content:
            pass
    if not importers:
        print(f"  ❌ {cf} — 未被任何檔案 import")
    else:
        print(f"  ✅ {cf} — imported by {[p.split('/')[-1] for p in importers]}")

# =====================================================
# 6. Custom Data Tables
# =====================================================
print("\n" + "=" * 80)
print("Custom Data Table 分析")
print("=" * 80)
data_json = json.loads(vfs.get("src/data.json", "[]"))
if isinstance(data_json, list):
    tables = data_json
else:
    tables = data_json.get("objects", [])

for tbl in tables:
    slug = tbl.get("api_slug", tbl.get("slug", "?"))
    name = tbl.get("name", "?")
    # 在程式碼中搜尋
    used = False
    for src_path, content in all_content.items():
        if slug in content and (src_path.endswith(".tsx") or src_path.endswith(".ts") or src_path.endswith(".py")):
            used = True
            break
    print(f"  {'✅' if used else '❌'} {name} (api_slug={slug}) — {'被使用' if used else '未使用'}")

# 也直接查 API
print("\n  --- API 查詢 Custom Tables ---")
custom_tables = api("GET", f"/data/objects?app_id={APP}", None, token)
if custom_tables:
    ct_list = custom_tables if isinstance(custom_tables, list) else custom_tables.get("objects", custom_tables.get("data", []))
    for ct in ct_list:
        slug = ct.get("api_slug", "?")
        name = ct.get("name", "?")
        ct_id = ct.get("id", "?")
        # 搜尋程式碼
        used = any(slug in content for p, content in all_content.items()
                    if p.endswith((".tsx", ".ts", ".py")))
        print(f"    {'✅' if used else '❌'} {name} (slug={slug}, id={ct_id})")

# =====================================================
# 7. Data References
# =====================================================
print("\n" + "=" * 80)
print("Data Reference 使用分析")
print("=" * 80)
refs = api("GET", f"/refs/apps/{APP}", None, token)
if refs:
    for ref in refs:
        table = ref.get("table_name", "?")
        ref_id = ref.get("id", "?")[:8]
        cols = len(ref.get("columns", []))
        perms = ref.get("permissions", [])
        # 搜尋程式碼
        used = any(table in content for p, content in all_content.items()
                    if p.endswith((".tsx", ".ts", ".py")))
        # 也檢查 db.json
        db_json = vfs.get("src/db.json", "")
        in_db_json = table in db_json
        print(f"  {'✅' if used else '❌'} {table} (ref={ref_id}, {cols} cols, perms={perms}, in_code={used}, in_db.json={in_db_json})")

# =====================================================
# 8. 規範合規問題（之前審查的重播）
# =====================================================
print("\n" + "=" * 80)
print("規範合規問題")
print("=" * 80)
compliance = []
for path, content in sorted(vfs.items()):
    issues = []
    if path.endswith(".css"):
        for i, line in enumerate(content.split("\n")):
            if ":root" in line and ":host" not in line and "{" in line:
                issues.append(f"L{i+1}: `:root` 沒有 `:host`")
    if path.endswith((".tsx", ".ts")):
        if "BrowserRouter" in content:
            issues.append("使用 BrowserRouter")
        if "confirm(" in content and "ConfirmDialog" not in path:
            # 排除引用 ConfirmDialog 的情境
            pass
        if "submitRecord" in content:
            for t in ["hr_leaves", "hr_employees", "hr_leave_types"]:
                if f'submitRecord("{t}"' in content:
                    issues.append(f'submitRecord("{t}") 應改用 db.ts')
    if path.endswith(".py"):
        if "ctx.env" in content:
            issues.append("使用 ctx.env（是 str 不是 dict）")
        if "insert_object" in content:
            issues.append("使用 insert_object（應為 ctx.db.insert）")
        for i, line in enumerate(content.split("\n")):
            if "ctx.secrets.get(" in line:
                args_start = line.find("ctx.secrets.get(") + len("ctx.secrets.get(")
                args_end = line.find(")", args_start)
                if args_end > args_start and "," in line[args_start:args_end]:
                    issues.append(f"L{i+1}: ctx.secrets.get() 雙參數")
    if "AppLayout" in path and path.endswith(".tsx"):
        if "overflow" not in content and "overflowY" not in content:
            issues.append("缺少 overflow-y: auto")
        if "100vh" not in content:
            issues.append("缺少 height: 100vh")
    if issues:
        compliance.append((path, issues))
        print(f"  ❌ {path}: {'; '.join(issues)}")

if not compliance:
    print("  ✅ 全部合規")

# =====================================================
# SUMMARY
# =====================================================
print("\n" + "=" * 80)
print("總結")
print("=" * 80)
print(f"\n死檔案（建議移除）: {len(dead_files)}")
for f in dead_files:
    print(f"  - {f}")
print(f"\n孤立 Action（不在 manifest 中）: {len(orphan_actions)}")
for f in orphan_actions:
    print(f"  - {f}")
print(f"\n合規問題: {sum(len(i) for _, i in compliance)}")
for path, issues in compliance:
    print(f"  - {path}: {'; '.join(issues)}")
