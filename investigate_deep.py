# -*- coding: utf-8 -*-
"""深入查看 mockup 和 PayrollSettings 問題"""
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

# 1. PayrollSettingsPage — 完整 loadData 函式
print("=" * 60)
print("  PayrollSettingsPage 完整程式碼")
print("=" * 60)
psp = vfs["src/pages/PayrollSettingsPage.tsx"]
lines = psp.split("\n")
for i, line in enumerate(lines):
    print(f"  L{i+1:3d}: {line[:120]}")

# 2. AttendancePage — 找「模擬」
print("\n" + "=" * 60)
print("  AttendancePage 模擬數據")
print("=" * 60)
att = vfs["src/pages/AttendancePage.tsx"]
for i, line in enumerate(att.split("\n")):
    if "模擬" in line or "mock" in line.lower() or "fake" in line.lower():
        # Show context
        alines = att.split("\n")
        for j in range(max(0,i-3), min(len(alines), i+5)):
            print(f"  L{j+1}: {alines[j][:120]}")
        print()

# 3. LeavesPage — 找 demo
print("\n" + "=" * 60)
print("  LeavesPage demo")
print("=" * 60)
leaves = vfs["src/pages/LeavesPage.tsx"]
for i, line in enumerate(leaves.split("\n")):
    if "demo" in line.lower() or "mock" in line.lower():
        llines = leaves.split("\n")
        for j in range(max(0,i-3), min(len(llines), i+5)):
            print(f"  L{j+1}: {llines[j][:120]}")
        print()

# 4. Check if payroll_settings and payroll_brackets custom tables exist
print("\n" + "=" * 60)
print("  Custom Tables 檢查")
print("=" * 60)

# listRecords uses api.ts → /data/objects/{objectId}/records
# Check if payroll_settings exists
for table in ["payroll_settings", "payroll_brackets"]:
    r = api("GET", f"/data/apps/{APP}/objects/{table}/records", None, token)
    if r and "_error" not in r:
        count = len(r) if isinstance(r, list) else r.get("total", "?")
        print(f"  {table}: OK ({count} records)")
    else:
        err = r.get("_error", "") if r else "null"
        detail = r.get("_detail", "") if r else ""
        print(f"  {table}: ERROR {err} — {detail[:200]}")

# Also try the listRecords path that api.ts uses
for table in ["payroll_settings", "payroll_brackets"]:
    r = api("GET", f"/data/objects/{table}/records", None, token)
    if r and "_error" not in r:
        count = len(r) if isinstance(r, list) else r.get("total", "?")
        print(f"  {table} (no app prefix): OK ({count} records)")
    else:
        err = r.get("_error", "") if r else "null"
        detail = r.get("_detail", "") if r else ""
        print(f"  {table} (no app prefix): ERROR {err} — {detail[:100]}")

# 5. Check ai_hr_insights.py prompt details
print("\n" + "=" * 60)
print("  AI Action 完整 prompt")
print("=" * 60)
ai = vfs["actions/ai_hr_insights.py"]
for i, line in enumerate(ai.split("\n")):
    print(f"  L{i+1:3d}: {line[:120]}")
