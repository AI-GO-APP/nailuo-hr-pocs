# -*- coding: utf-8 -*-
"""調查 proxy table 中是否有 payroll/bonus 相關表"""
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

# 1. 查看所有 data references (proxy tables)
print("=== Data References (Proxy Tables) ===")
refs = api("GET", f"/refs/apps/{APP}", None, token)
if isinstance(refs, list):
    for ref in refs:
        table = ref.get("table_name", "?")
        cols = ref.get("columns", [])
        perms = ref.get("permissions", [])
        print(f"\n  {table}")
        print(f"    columns: {cols}")
        print(f"    permissions: {perms}")

# 2. 測試每個 payroll/bonus 相關的 proxy table
print("\n=== 測試 Payroll/Bonus Proxy Tables ===")
payroll_tables = [
    "hr_payroll_runs",
    "hr_payroll_slips",
    "hr_payroll_slip_lines",
    "hr_payroll_contracts",
    "hr_payroll_bonus_rules",
    "hr_payroll_bonus_rule_results",
    "hr_payroll_settings",
    "hr_bonuses",
]
for table in payroll_tables:
    r = api("GET", f"/proxy/{APP}/{table}?limit=3", None, token)
    if r and "_error" not in r:
        records = r if isinstance(r, list) else r.get("records", r.get("data", []))
        if isinstance(records, list) and len(records) > 0:
            # Show first record's keys
            keys = list(records[0].keys())
            print(f"  {table}: {len(records)} records, keys={keys}")
        elif isinstance(records, list):
            print(f"  {table}: 0 records")
        else:
            print(f"  {table}: response type={type(records).__name__}, keys={list(r.keys()) if isinstance(r, dict) else '?'}")
    else:
        err = r.get("_error", "?") if r else "?"
        detail = r.get("_detail", "")[:150] if r else ""
        print(f"  {table}: ERROR {err} — {detail}")

# 3. 查看 hr_payroll_runs 的 columns
print("\n=== hr_payroll_runs 詳細 ===")
if "hr_payroll_runs" in [r.get("table_name") for r in (refs or [])]:
    ref = next(r for r in refs if r["table_name"] == "hr_payroll_runs")
    print(f"  columns: {ref.get('columns', [])}")
    print(f"  permissions: {ref.get('permissions', [])}")

print("\n=== hr_payroll_slips 詳細 ===")
if "hr_payroll_slips" in [r.get("table_name") for r in (refs or [])]:
    ref = next(r for r in refs if r["table_name"] == "hr_payroll_slips")
    print(f"  columns: {ref.get('columns', [])}")
    print(f"  permissions: {ref.get('permissions', [])}")

print("\n=== hr_payroll_bonus_rule_results 詳細 ===")
if "hr_payroll_bonus_rule_results" in [r.get("table_name") for r in (refs or [])]:
    ref = next(r for r in refs if r["table_name"] == "hr_payroll_bonus_rule_results")
    print(f"  columns: {ref.get('columns', [])}")
    print(f"  permissions: {ref.get('permissions', [])}")

# 4. Also check the custom table bonus_records_8e0a2d (old one)
print("\n=== 舊的 bonus_records_8e0a2d ===")
r = api("GET", "/data/objects/bonus_records_8e0a2d/records?limit=3", None, token)
if isinstance(r, list):
    print(f"  {len(r)} records")
    if r:
        print(f"  keys: {list(r[0].keys())}")
        print(f"  sample: {json.dumps(r[0], ensure_ascii=False)[:200]}")
else:
    print(f"  {r}")

# 5. 查看 BonusImportPage 和 HistoryPage 怎麼用的
print("\n=== BonusImportPage 完整邏輯 ===")
bp = vfs.get("src/pages/BonusImportPage.tsx", "")
for i, line in enumerate(bp.split("\n")):
    s = line.strip()
    if "submitRecord" in s or "listRecords" in s or "bonus" in s.lower() or "runAction" in s:
        print(f"  L{i+1}: {s[:120]}")

print("\n=== SettlementPage 完整邏輯 ===")
sp = vfs.get("src/pages/SettlementPage.tsx", "")
for i, line in enumerate(sp.split("\n")):
    s = line.strip()
    if "calculatePayrollRun" in s or "runAction" in s or "payroll" in s.lower() or "insert" in s.lower() or "query" in s.lower():
        print(f"  L{i+1}: {s[:120]}")
