# -*- coding: utf-8 -*-
"""取得目標 app VFS + 比對功能差異"""
import json, urllib.request, ssl
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
TARGET = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"

auth = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/auth/login",
    json.dumps({"email":"admin@tslg.com.tw","password":"password123"}).encode(),
    method="POST", headers={"Content-Type":"application/json"}
)).read())
token = auth["access_token"]

# Get app
app = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/builder/apps/{TARGET}",
    headers={"Authorization": f"Bearer {token}"}
)).read())
vfs = app["vfs_state"]

print(f"App: {app.get('name','?')}")
print(f"VFS: {len(vfs)} files, v{app['vfs_version']}")
print()

# List all files
print("=== VFS Files ===")
for f in sorted(vfs):
    print(f"  {f}")

# Routes & pages
print("\n=== Routes (App.tsx) ===")
app_tsx = vfs.get("src/App.tsx", "")
for i, line in enumerate(app_tsx.split("\n")):
    if "Route" in line or "path" in line or "element" in line or "import" in line:
        print(f"  L{i+1}: {line.strip()[:120]}")

# routes.ts
print("\n=== routes.ts ===")
routes = vfs.get("src/routes.ts", "")
print(routes[:3000])

# Pages summary
print("\n=== Pages ===")
for path in sorted(vfs):
    if not path.startswith("src/pages/") or not path.endswith(".tsx"):
        continue
    content = vfs[path]
    name = path.split("/")[-1].replace(".tsx", "")
    lines = len(content.split("\n"))
    
    # 找 API 呼叫
    apis = []
    for fn in ["listRecords", "submitRecord", "query(", "queryAdvanced", "insert(", "fetch(", "callAction", "proxyInsert"]:
        if fn in content:
            apis.append(fn.replace("(", ""))
    
    # 找 useState
    states = []
    for line in content.split("\n"):
        if "useState" in line:
            import re
            m = re.search(r'const \[(\w+)', line)
            if m:
                states.append(m.group(1))
    
    print(f"\n  {name} ({lines} lines)")
    print(f"    APIs: {', '.join(apis) if apis else 'none'}")
    print(f"    States: {', '.join(states[:8]) if states else 'none'}")
    # 摘要前 3 行重要 JSX
    for line in content.split("\n"):
        s = line.strip()
        if s.startswith("<h1") or s.startswith("<h2") or "page-title" in s:
            print(f"    Title: {s[:100]}")
            break

# Actions
print("\n=== Actions ===")
manifest = json.loads(vfs.get("actions/manifest.json", "{}"))
for act in manifest.get("actions", []):
    print(f"  {act.get('name', '?')}: {act.get('description', '')}")
    f = f"actions/{act.get('file', '')}"
    if f in vfs:
        content = vfs[f]
        # 找 tool definitions
        for line in content.split("\n"):
            if "def " in line and "(" in line:
                print(f"    {line.strip()[:80]}")

# Components
print("\n=== Components ===")
for path in sorted(vfs):
    if not path.startswith("src/components/") or not path.endswith(".tsx"):
        continue
    content = vfs[path]
    name = path.split("/")[-1].replace(".tsx", "")
    lines = len(content.split("\n"))
    # 找 export
    exports = [l.strip()[:80] for l in content.split("\n") if "export " in l and "function" in l]
    print(f"  {name} ({lines} lines): {'; '.join(exports[:3]) if exports else ''}")

# Refs
print("\n=== Data References ===")
refs = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/refs/apps/{TARGET}",
    headers={"Authorization": f"Bearer {token}"}
)).read())
for ref in refs:
    t = ref.get("table_name", "?")
    cols = ref.get("columns", [])
    perms = ref.get("permissions", [])
    print(f"  {t}: {len(cols)} cols, perms={perms}")
