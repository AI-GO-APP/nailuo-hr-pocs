# -*- coding: utf-8 -*-
"""全面盤點 Custom App 技術債"""
import json, urllib.request, ssl, re
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:300]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]
slug = app_data["slug"]

print("=" * 70)
print("  Custom App 全面技術債盤點")
print("=" * 70)

# =============================================================
# 1. VFS 檔案清單 — 找出未被引用的檔案
# =============================================================
print("\n[1] VFS 檔案清單 + 引用分析")
all_files = sorted(vfs.keys())
print(f"  共 {len(all_files)} 個檔案")

# Build import graph
imported_from = {}  # file -> set of files that import it
for path in all_files:
    if not path.endswith((".tsx", ".ts")):
        continue
    content = vfs[path]
    for m in re.finditer(r'from\s+"([^"]+)"', content):
        mod = m.group(1)
        if not mod.startswith("."):
            continue
        # Resolve relative path
        parts = path.split("/")
        if mod.startswith("../"):
            base = "/".join(parts[:-2])
            rest = mod[3:]
        elif mod.startswith("./"):
            base = "/".join(parts[:-1])
            rest = mod[2:]
        else:
            continue
        candidates = [f"{base}/{rest}.tsx", f"{base}/{rest}.ts",
                      f"{base}/{rest}/index.tsx", f"{base}/{rest}/index.ts",
                      f"{base}/{rest}"]
        for c in candidates:
            if c in vfs:
                imported_from.setdefault(c, set()).add(path)
                break

# Entry points (always used)
entry_points = {"src/App.tsx", "src/App.css", "src/main.tsx", "src/index.css",
                "manifest.json", "tsconfig.json", "package.json", "vite.config.ts",
                "index.html"}

# Also: routes.ts imports pages
routes_file = "src/routes.ts"

# Find pages referenced in routes
routes_content = vfs.get(routes_file, "")
route_pages = set()
for m in re.finditer(r'from\s+"([^"]+)"', routes_content):
    mod = m.group(1)
    if mod.startswith("./pages/"):
        page = mod.replace("./", "src/")
        for ext in [".tsx", ".ts"]:
            if page + ext in vfs:
                route_pages.add(page + ext)
                break

# Action files (always used)
action_files = {f for f in all_files if f.startswith("actions/")}

# Mark reachable files
reachable = set()
reachable.update(entry_points)
reachable.update(action_files)
reachable.add(routes_file)
reachable.update(route_pages)

# BFS
queue = list(reachable)
while queue:
    f = queue.pop()
    for target, importers in imported_from.items():
        if f in importers and target not in reachable:
            reachable.add(target)
            queue.append(target)

# Also mark CSS, JSON, etc as reachable if referenced
for path in all_files:
    if path.endswith((".css", ".json")) and path.startswith("src/"):
        # Check if any ts/tsx imports it
        basename = path.split("/")[-1]
        for other in all_files:
            if other.endswith((".tsx", ".ts")) and basename in vfs.get(other, ""):
                reachable.add(path)
                break

# Files not reachable
unreachable = set(all_files) - reachable
# Filter out obvious config files
config_patterns = ["package", "tsconfig", "vite", "manifest", "index.html", ".json"]
truly_unused = []
for f in sorted(unreachable):
    if any(p in f for p in config_patterns):
        reachable.add(f)
        continue
    truly_unused.append(f)

print(f"\n  可能未使用的檔案 ({len(truly_unused)} 個):")
for f in truly_unused:
    size = len(vfs[f])
    print(f"    {f} ({size} chars)")

# =============================================================
# 2. Routes — 檢查所有路由是否都有對應頁面
# =============================================================
print(f"\n[2] 路由 → 頁面對應")
for m in re.finditer(r'path:\s*"([^"]+)"', routes_content):
    path = m.group(1)
    print(f"    route: {path}")

# Check for pages not in routes
page_files = [f for f in all_files if f.startswith("src/pages/") and f.endswith(".tsx")]
for pf in page_files:
    basename = pf.split("/")[-1].replace(".tsx", "")
    if basename not in routes_content and pf not in route_pages:
        print(f"    ⚠️  {pf} 不在路由中（可能未使用）")

# =============================================================
# 3. Components — 檢查所有元件是否都有被引用
# =============================================================
print(f"\n[3] 元件引用")
comp_files = [f for f in all_files if f.startswith("src/components/") and f.endswith(".tsx")]
for cf in comp_files:
    basename = cf.split("/")[-1].replace(".tsx", "")
    importers = imported_from.get(cf, set())
    if importers:
        print(f"    {basename}: 被 {len(importers)} 個檔案引用")
    else:
        print(f"    ⚠️  {basename}: 無人引用")

# =============================================================
# 4. Utils — 檢查所有 utils 是否都有被引用
# =============================================================
print(f"\n[4] Utils 引用")
util_files = [f for f in all_files if f.startswith("src/utils/") and f.endswith((".ts", ".tsx"))]
for uf in util_files:
    basename = uf.split("/")[-1]
    importers = imported_from.get(uf, set())
    if importers:
        print(f"    {basename}: 被 {len(importers)} 個檔案引用")
    else:
        print(f"    ⚠️  {basename}: 無人引用")

# =============================================================
# 5. Data References — 檢查哪些 proxy table 實際被使用
# =============================================================
print(f"\n[5] Data References (Proxy Tables)")
refs = api("GET", f"/refs/apps/{APP}", None, token)
ref_tables = {r["table_name"] for r in (refs or [])} if isinstance(refs, list) else set()

# Find which tables are actually used in code
used_proxy = set()
for path in all_files:
    if path.startswith("actions/") and path.endswith(".py"):
        content = vfs[path]
        for m in re.finditer(r'ctx\.db\.query\("([^"]+)"', content):
            used_proxy.add(m.group(1))
        for m in re.finditer(r'ctx\.db\.insert\("([^"]+)"', content):
            used_proxy.add(m.group(1))
    elif path.endswith((".tsx", ".ts")):
        content = vfs[path]
        for m in re.finditer(r'query\("([^"]+)"', content):
            used_proxy.add(m.group(1))
        for m in re.finditer(r'queryAdvanced\("([^"]+)"', content):
            used_proxy.add(m.group(1))
        for m in re.finditer(r'insert\("([^"]+)"', content):
            used_proxy.add(m.group(1))
        for m in re.finditer(r'update\("([^"]+)"', content):
            used_proxy.add(m.group(1))

print(f"  已註冊的 ref: {len(ref_tables)}, 實際使用: {len(used_proxy)}")
for t in sorted(ref_tables):
    used = t in used_proxy
    print(f"    {t}: {'使用中' if used else '⚠️ 未使用'}")

unused_refs = ref_tables - used_proxy
if unused_refs:
    print(f"\n  未使用的 refs ({len(unused_refs)}): {sorted(unused_refs)}")

# Check for used proxy tables not registered
unregistered = used_proxy - ref_tables
if unregistered:
    print(f"\n  使用中但未註冊的 proxy tables ({len(unregistered)}): {sorted(unregistered)}")

# =============================================================
# 6. Custom Tables — 盤點
# =============================================================
print(f"\n[6] Custom Tables")
all_custom = api("GET", "/data/objects", None, token) or []
our_custom = [t for t in all_custom if t.get("app_id") == APP]
other_custom = [t for t in all_custom if t.get("app_id") != APP]

print(f"  本 App 的 custom tables ({len(our_custom)}):")
# Find which custom tables are used in code
used_custom = set()
for path in all_files:
    if not path.endswith((".tsx", ".ts")):
        continue
    content = vfs[path]
    for m in re.finditer(r'(?:listRecords|submitRecord|updateRecord|deleteRecord)\("([^"]+)"', content):
        used_custom.add(m.group(1))

for t in our_custom:
    slug_name = t.get("api_slug", "?")
    name = t.get("name", "?")
    used = slug_name in used_custom
    records = api("GET", f"/data/objects/{slug_name}/records?limit=1", None, token)
    count = len(records) if isinstance(records, list) else "?"
    print(f"    {slug_name} ({name}): {'使用中' if used else '⚠️ 未使用'}, {count} records")

if other_custom:
    print(f"\n  其他 App 的 custom tables ({len(other_custom)}):")
    for t in other_custom:
        print(f"    {t.get('api_slug','?')} ({t.get('name','?')}), app={t.get('app_id','?')[:8] if t.get('app_id') else 'none'}")

# =============================================================
# 7. Actions — 盤點
# =============================================================
print(f"\n[7] Server-Side Actions")
manifest = json.loads(vfs.get("manifest.json", "{}"))
manifest_actions = {a.get("name") for a in manifest.get("actions", [])}
action_py_files = {f.replace("actions/","").replace(".py","") for f in all_files if f.startswith("actions/") and f.endswith(".py")}

# Check which actions are called from frontend
called_actions = set()
for path in all_files:
    if not path.endswith((".tsx", ".ts")):
        continue
    content = vfs[path]
    for m in re.finditer(r'runAction\("([^"]+)"', content):
        called_actions.add(m.group(1))

print(f"  Manifest 定義: {sorted(manifest_actions)}")
print(f"  Python 檔案: {sorted(action_py_files)}")
print(f"  前端呼叫: {sorted(called_actions)}")

# Actions in manifest but not called
uncalled = manifest_actions - called_actions
if uncalled:
    print(f"\n  定義但前端未呼叫的 actions ({len(uncalled)}): {sorted(uncalled)}")

# Actions called but not in manifest
unmanifested = called_actions - manifest_actions
if unmanifested:
    print(f"\n  前端呼叫但 manifest 未定義: {sorted(unmanifested)}")

# Python files not in manifest
orphan_py = action_py_files - manifest_actions
if orphan_py:
    print(f"\n  Python 檔存在但 manifest 未定義: {sorted(orphan_py)}")

# =============================================================
# 8. 重複/冗餘 CSS 分析
# =============================================================
print(f"\n[8] CSS 分析")
app_css = vfs.get("src/App.css", "")
css_lines = len(app_css.split("\n"))
css_size = len(app_css)
print(f"  App.css: {css_lines} lines, {css_size:,} chars")

# Count Tailwind-style utility classes (from template)
tailwind_selectors = []
for m in re.finditer(r'\.([\w\-\[\]\\\.]+)\s*\{', app_css):
    sel = m.group(1)
    if "\\" in sel or "[" in sel:
        tailwind_selectors.append(sel)

print(f"  Tailwind-style utility selectors: {len(tailwind_selectors)}")
if tailwind_selectors:
    # Check if any are actually used
    used_tw = 0
    for sel in tailwind_selectors:
        # Convert CSS escaped class back to className
        cls = sel.replace("\\[", "[").replace("\\]", "]").replace("\\.", ".").replace("\\#", "#").replace("\\%", "%").replace("\\/", "/").replace("\\:", ":").replace("\\&", "&")
        for path in all_files:
            if path.endswith(".tsx") and cls in vfs.get(path, ""):
                used_tw += 1
                break
    print(f"  Tailwind utils 被 TSX 使用: {used_tw} / {len(tailwind_selectors)}")
    unused_tw = len(tailwind_selectors) - used_tw
    if unused_tw > 0:
        print(f"  ⚠️  {unused_tw} 個 Tailwind utility selector 可能未使用（來自模板）")

# =============================================================
# 9. 前端 import 來自 node_modules 但可能未使用
# =============================================================
print(f"\n[9] 外部依賴 (node_modules)")
npm_imports = set()
for path in all_files:
    if not path.endswith((".tsx", ".ts")) or path.startswith("actions/"):
        continue
    content = vfs[path]
    for m in re.finditer(r'from\s+"([^\.][^"]*)"', content):
        pkg = m.group(1).split("/")[0]
        npm_imports.add(pkg)

pkg_json = json.loads(vfs.get("package.json", "{}"))
pkg_deps = set(pkg_json.get("dependencies", {}).keys())
pkg_dev_deps = set(pkg_json.get("devDependencies", {}).keys())

print(f"  程式碼引用的 npm packages: {sorted(npm_imports)}")
print(f"  package.json dependencies: {sorted(pkg_deps)}")

unused_deps = pkg_deps - npm_imports - {"react", "react-dom"}
if unused_deps:
    print(f"\n  ⚠️  package.json 有但程式碼未 import: {sorted(unused_deps)}")

missing_deps = npm_imports - pkg_deps - pkg_dev_deps - {"react", "react/jsx-runtime"}
if missing_deps:
    print(f"\n  ⚠️  程式碼 import 但 package.json 沒有: {sorted(missing_deps)}")

# =============================================================
# 10. data.json / ListPage (舊模板殘留)
# =============================================================
print(f"\n[10] 舊模板殘留")
data_json = vfs.get("src/data.json", "")
if data_json.strip() in ("{}", "[]", ""):
    print(f"  src/data.json: 空的 (可移除)")
else:
    print(f"  src/data.json: {len(data_json)} chars (有內容)")

# Check if ListPage is used in routes
if "ListPage" in routes_content:
    print(f"  ListPage: 在路由中（使用中）")
else:
    if "src/pages/ListPage.tsx" in vfs:
        print(f"  ⚠️  ListPage.tsx: 存在但不在路由中（可移除）")

# =============================================================
# 11. 技術債摘要
# =============================================================
print(f"\n{'='*70}")
print("  技術債摘要")
print(f"{'='*70}")
