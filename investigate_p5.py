# -*- coding: utf-8 -*-
"""調查問題 5（Settlement 資料表）+ 完整 mockup 掃描 + custom table 盤點"""
import json, urllib.request, ssl
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
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]

# =============================================================
# 問題 5: Settlement 使用的 table
# =============================================================
print("=" * 60)
print("  [5] SettlementPage 使用的 table")
print("=" * 60)

# 找出 SettlementPage 用到的 table
settlement = vfs.get("src/pages/SettlementPage.tsx", "")
for i, line in enumerate(settlement.split("\n")):
    s = line.strip()
    if "listRecords" in s or "submitRecord" in s or "runAction" in s or "import " in s:
        print(f"  L{i+1}: {s[:120]}")

# 找 run_monthly_payroll action 用的 table
action = vfs.get("actions/run_monthly_payroll.py", "")
print(f"\n  run_monthly_payroll.py ({len(action)} chars):")
for i, line in enumerate(action.split("\n")):
    print(f"    L{i+1}: {line[:120]}")

# 找 payrollCalc.ts 用的 table
calc = vfs.get("src/utils/payrollCalc.ts", "")
print(f"\n  payrollCalc.ts — listRecords/submitRecord 呼叫:")
for i, line in enumerate(calc.split("\n")):
    if "listRecords" in line or "submitRecord" in line or "query(" in line or "insert(" in line:
        print(f"    L{i+1}: {line.strip()[:120]}")

# =============================================================
# 盤點所有 custom table 的使用和存在狀態
# =============================================================
print("\n" + "=" * 60)
print("  Custom Tables 完整盤點")
print("=" * 60)

# 收集所有被引用的 custom table 名稱 (from api.ts: listRecords/submitRecord/updateRecord/deleteRecord)
import re
table_refs = set()
for path in sorted(vfs):
    if not path.endswith((".tsx", ".ts")) or path.startswith("actions/"):
        continue
    content = vfs[path]
    for m in re.finditer(r'(?:listRecords|submitRecord|updateRecord|deleteRecord)\("([^"]+)"', content):
        table_refs.add(m.group(1))

# 收集 action 中的 table (ctx.data.list/ctx.data.create 等)
for path in sorted(vfs):
    if not path.startswith("actions/") or not path.endswith(".py"):
        continue
    content = vfs[path]
    for m in re.finditer(r'ctx\.data\.\w+\("([^"]+)"', content):
        table_refs.add(m.group(1))

print(f"  被引用的 custom tables: {sorted(table_refs)}")

# 測試每個 table 是否存在
for table in sorted(table_refs):
    r = api("GET", f"/data/objects/{table}/records?limit=1", None, token)
    if r and "_error" not in r:
        count = len(r) if isinstance(r, list) else "?"
        print(f"    {table}: OK")
    else:
        err_code = r.get("_error", "?") if r else "?"
        detail = r.get("_detail", "")[:200] if r else ""
        print(f"    {table}: ERROR {err_code} — {detail}")

# 也測試 proxy table (db.ts: query/insert)
print("\n  被引用的 proxy tables (via db.ts):")
proxy_refs = set()
for path in sorted(vfs):
    if not path.endswith((".tsx", ".ts")) or path.startswith("actions/"):
        continue
    content = vfs[path]
    for m in re.finditer(r'(?:query|queryAdvanced|insert)\("([^"]+)"', content):
        proxy_refs.add(m.group(1))

# Action 中的 ctx.db.query
for path in sorted(vfs):
    if not path.startswith("actions/") or not path.endswith(".py"):
        continue
    content = vfs[path]
    for m in re.finditer(r'ctx\.db\.query\("([^"]+)"', content):
        proxy_refs.add(m.group(1))

for table in sorted(proxy_refs):
    print(f"    {table}")

# =============================================================
# AttendancePage 模擬 — 查看上下文
# =============================================================
print("\n" + "=" * 60)
print("  AttendancePage 模擬數據詳情")
print("=" * 60)
att = vfs["src/pages/AttendancePage.tsx"]
lines_att = att.split("\n")
for i, line in enumerate(lines_att):
    if "模擬" in line:
        for j in range(max(0,i-5), min(len(lines_att), i+10)):
            print(f"  L{j+1}: {lines_att[j][:120]}")
        print()

# =============================================================
# LeavesPage demo — 查看上下文
# =============================================================
print("\n" + "=" * 60)
print("  LeavesPage demo 詳情")
print("=" * 60)
leaves = vfs["src/pages/LeavesPage.tsx"]
lines_lv = leaves.split("\n")
for i, line in enumerate(lines_lv):
    if "demo" in line.lower():
        for j in range(max(0,i-3), min(len(lines_lv), i+5)):
            print(f"  L{j+1}: {lines_lv[j][:120]}")
        print()
