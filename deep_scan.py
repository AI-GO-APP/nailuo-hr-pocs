# -*- coding: utf-8 -*-
"""深入檢查每個頁面的資料來源是否是真實 API 還是 hardcoded"""
import json, urllib.request, ssl, re
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "da7789b4-59bc-422c-8e7b-b6a7b9103146"

auth = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/auth/login",
    json.dumps({"email":"admin@tslg.com.tw","password":"password123"}).encode(),
    method="POST", headers={"Content-Type":"application/json"}
)).read())
token = auth["access_token"]
app = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/builder/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())
vfs = app["vfs_state"]

pages = {p: vfs[p] for p in sorted(vfs) if p.startswith("src/pages/") and p.endswith(".tsx")}

for path, content in pages.items():
    name = path.split("/")[-1].replace(".tsx", "")
    print(f"\n{'=' * 70}")
    print(f"  {name}")
    print(f"{'=' * 70}")

    lines = content.split("\n")

    # 找所有 const/let 陣列或物件定義
    for i, line in enumerate(lines):
        s = line.strip()

        # 找 const xxx = [ ... ] 或 const xxx = { ... }
        m = re.match(r'(?:const|let|var)\s+(\w+)\s*[:=]', s)
        if m:
            var_name = m.group(1)
            # 看這一行 + 後面幾行是否包含大量 hardcoded 資料
            block = "\n".join(lines[i:min(i+30, len(lines))])
            # 計算 { 數量
            brace_count = block.count("{")
            if brace_count >= 3 and "[" in s:
                print(f"  L{i+1}: const {var_name} = [ ... ] ({brace_count} objects)")
                # 印出前幾行
                for j in range(i, min(i+5, len(lines))):
                    print(f"    {lines[j].rstrip()[:110]}")

        # 找 useState 初始值含有 hardcoded 資料
        if "useState(" in s and ("[" in s or "{" in s):
            if s.count("{") >= 2 or s.count("[") >= 1:
                print(f"  L{i+1}: [useState 初始值] {s[:110]}")

    # 找 API 呼叫
    print(f"\n  資料來源:")
    for i, line in enumerate(lines):
        s = line.strip()
        if any(x in s for x in ["listRecords(", "query(", "queryAdvanced(", "callAction(", "runAction(", "fetch(", "proxyInsert("]):
            table_match = re.search(r'(?:listRecords|query|queryAdvanced|insert)\(\s*["\'](\w+)["\']', s)
            table = table_match.group(1) if table_match else ""
            print(f"    L{i+1}: {s[:100]}  {'→ table: ' + table if table else ''}")

# 也檢查 constants.ts
print(f"\n{'=' * 70}")
print(f"  constants.ts")
print(f"{'=' * 70}")
const_ts = vfs.get("src/constants.ts", "")
lines = const_ts.split("\n")
for i, line in enumerate(lines):
    s = line.strip()
    if s and not s.startswith("//") and not s.startswith("import"):
        print(f"  L{i+1}: {s[:120]}")

# 檢查 AI action 的 TYPE_ID_MAP
print(f"\n{'=' * 70}")
print(f"  ai_leave_chat.py — TYPE_ID_MAP")
print(f"{'=' * 70}")
ai_py = vfs.get("actions/ai_leave_chat.py", "")
ai_lines = ai_py.split("\n")
in_map = False
for i, line in enumerate(ai_lines):
    if "TYPE_ID_MAP" in line:
        in_map = True
    if in_map:
        print(f"  L{i+1}: {line.rstrip()[:100]}")
        if line.strip() == "}":
            in_map = False
            break
print("\n  ⚠️ TYPE_ID_MAP 是 hardcoded 的假別 UUID。")
print("     建議：改為在 execute() 中動態查詢 ctx.db.query('hr_leave_types')")
