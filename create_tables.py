# -*- coding: utf-8 -*-
"""用正確 API 建立 custom tables"""
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

# Check existing table detail to understand schema
print("=== 現有 custom table 結構 ===")
r = api("GET", "/data/objects", None, token)
for item in r:
    print(f"  {item['name']} (id={item['id'][:8]})")
    print(f"    api_slug={item.get('api_slug')}, app_id={item.get('app_id')}")
    # Get fields
    fields = item.get("fields", [])
    if not fields:
        # Try fetching detail
        detail = api("GET", f"/data/objects/{item['id']}", None, token)
        if detail and "_error" not in detail:
            fields = detail.get("fields", [])
            print(f"    fields from detail: {[f.get('name') for f in fields[:5]]}")
    else:
        print(f"    fields: {[f.get('name') for f in fields[:5]]}")
    print(f"    full keys: {list(item.keys())}")

# Now create with correct schema
print("\n=== 建立新 tables ===")
tables = [
    {
        "name": "薪資參數設定",
        "api_slug": "payroll_settings",
        "app_id": APP,
        "fields": [
            {"name": "base_hours", "field_type": "number", "display_name": "月基本工時"},
            {"name": "ot_rate_1", "field_type": "number", "display_name": "加班費率1"},
            {"name": "ot_rate_2", "field_type": "number", "display_name": "加班費率2"},
            {"name": "labor_rate", "field_type": "number", "display_name": "勞保費率"},
            {"name": "health_rate", "field_type": "number", "display_name": "健保費率"},
            {"name": "pension_rate", "field_type": "number", "display_name": "勞退提撥率"},
            {"name": "notes", "field_type": "text", "display_name": "備註"},
        ]
    },
    {
        "name": "勞健保級距",
        "api_slug": "payroll_brackets",
        "app_id": APP,
        "fields": [
            {"name": "grade_min", "field_type": "number", "display_name": "級距下限"},
            {"name": "grade_max", "field_type": "number", "display_name": "級距上限"},
            {"name": "labor_grade", "field_type": "number", "display_name": "勞保投保級距"},
            {"name": "health_grade", "field_type": "number", "display_name": "健保投保級距"},
            {"name": "labor_employee", "field_type": "number", "display_name": "勞保自付"},
            {"name": "labor_employer", "field_type": "number", "display_name": "勞保雇主"},
            {"name": "health_employee", "field_type": "number", "display_name": "健保自付"},
            {"name": "health_employer", "field_type": "number", "display_name": "健保雇主"},
        ]
    },
    {
        "name": "薪資紀錄",
        "api_slug": "payroll_records",
        "app_id": APP,
        "fields": [
            {"name": "period", "field_type": "text", "display_name": "期間"},
            {"name": "employee_id", "field_type": "text", "display_name": "員工ID"},
            {"name": "employee_name", "field_type": "text", "display_name": "員工姓名"},
            {"name": "base_salary", "field_type": "number", "display_name": "底薪"},
            {"name": "gross_salary", "field_type": "number", "display_name": "應發"},
            {"name": "deductions", "field_type": "number", "display_name": "扣除"},
            {"name": "net_salary", "field_type": "number", "display_name": "實發"},
            {"name": "status", "field_type": "text", "display_name": "狀態"},
        ]
    },
    {
        "name": "獎金紀錄",
        "api_slug": "bonus_records",
        "app_id": APP,
        "fields": [
            {"name": "period", "field_type": "text", "display_name": "期間"},
            {"name": "employee_id", "field_type": "text", "display_name": "員工ID"},
            {"name": "employee_name", "field_type": "text", "display_name": "員工姓名"},
            {"name": "amount", "field_type": "number", "display_name": "金額"},
            {"name": "bonus_type", "field_type": "text", "display_name": "類型"},
            {"name": "notes", "field_type": "text", "display_name": "備註"},
        ]
    },
]

for t in tables:
    # First check if it exists by api_slug
    test = api("GET", f"/data/objects/{t['api_slug']}/records?limit=1", None, token)
    if test and "_error" not in test:
        print(f"  {t['api_slug']}: 已存在")
        continue
    
    r = api("POST", "/data/objects", t, token)
    if r and "_error" not in r:
        print(f"  {t['api_slug']}: 建立成功 (id={r.get('id','')})")
    else:
        err = r.get("_error", "") if r else "?"
        detail = r.get("_detail", "") if r else ""
        print(f"  {t['api_slug']}: FAILED ({err}) — {detail[:300]}")

# Verify
print("\n=== 驗證 ===")
for slug in ["payroll_settings", "payroll_brackets", "payroll_records", "bonus_records"]:
    r = api("GET", f"/data/objects/{slug}/records?limit=1", None, token)
    if r and "_error" not in r:
        print(f"  {slug}: OK")
    else:
        print(f"  {slug}: {r}")
