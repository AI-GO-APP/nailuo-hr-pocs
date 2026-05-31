# -*- coding: utf-8 -*-
"""驗證修正結果 + 確認前端 table slug 對應"""
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

# 1. 確認前端引用的所有 custom table slug
import re
print("=== 前端引用的 Custom Table Slugs ===")
for path in sorted(vfs):
    if not path.endswith((".tsx", ".ts")) or path.startswith("actions/"):
        continue
    content = vfs[path]
    for m in re.finditer(r'(?:listRecords|submitRecord|updateRecord|deleteRecord)\("([^"]+)"', content):
        slug = m.group(1)
        # Test if it exists
        r = api("GET", f"/data/objects/{slug}/records?limit=1", None, token)
        ok = r and "_error" not in r
        print(f"  {path.split('/')[-1]}: {slug} → {'OK' if ok else 'NOT FOUND'}")

# 2. 確認 HistoryPage 和 BonusImportPage 的 table 引用
for page_name in ["BonusImportPage", "HistoryPage"]:
    page = vfs.get(f"src/pages/{page_name}.tsx", "")
    print(f"\n  {page_name} table refs:")
    for m in re.finditer(r'(?:listRecords|submitRecord|updateRecord|deleteRecord|runAction)\("([^"]+)"', page):
        print(f"    {m.group(1)}")

# 3. Test Settlement action
print("\n=== 測試 Settlement Action ===")
r = api("POST", f"/actions/apps/{APP}/run/run_monthly_payroll",
        {"params": {"period": "2026-05"}}, token)
if r and "_error" not in r:
    status = r.get("status", "?")
    result = r.get("result", {})
    error = r.get("error", "")
    if error:
        print(f"  status={status}, error={error}")
    else:
        emp_count = result.get("employee_count", "?")
        total_net = result.get("total_net", "?")
        slips_count = len(result.get("slips", []))
        print(f"  status={status}, employees={emp_count}, net={total_net}, slips={slips_count}")
else:
    print(f"  FAILED: {r}")

# 4. Test PayrollSettings table access
print("\n=== 測試 PayrollSettings Table ===")
r = api("GET", f"/data/objects/payroll_settings/records", None, token)
if r and "_error" not in r:
    print(f"  payroll_settings records: {len(r)}")
else:
    print(f"  payroll_settings: {r}")

r = api("GET", f"/data/objects/payroll_brackets/records", None, token)
if r and "_error" not in r:
    print(f"  payroll_brackets records: {len(r)}")
else:
    print(f"  payroll_brackets: {r}")

# 5. Check the actual api_slug that BonusImportPage uses
bonus_page = vfs.get("src/pages/BonusImportPage.tsx", "")
print(f"\n=== BonusImportPage Action ===")
for i, line in enumerate(bonus_page.split("\n")):
    if "runAction" in line or "listRecords" in line or "submitRecord" in line:
        print(f"  L{i+1}: {line.strip()[:120]}")

# 6. List all data objects to see actual slugs
print("\n=== 所有 Custom Table 完整列表 ===")
r = api("GET", "/data/objects", None, token)
for item in (r or []):
    slug = item.get("api_slug", "?")
    app_id = item.get("app_id", "?")
    is_ours = app_id == APP
    print(f"  {slug} (app={'OURS' if is_ours else app_id[:8] if app_id else 'none'}) — {item['name']}")
