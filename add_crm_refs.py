# -*- coding: utf-8 -*-
"""嘗試為 target app 新增 CRM refs 並查詢資料"""
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
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# 1) crm_tags 現有資料
print("=== crm_tags ===")
r = api("GET", f"/proxy/{APP}/crm_tags?limit=20", None, token)
print(json.dumps(r, ensure_ascii=False, indent=2)[:500])

# 2) 嘗試新增 CRM refs
print("\n=== Adding refs ===")
tables_to_add = [
    "sale_orders", "sale_order_lines",
    "crm_leads", "crm_teams", "crm_stages",
    "res_partners", "res_users",
    "mail_activities", "mail_messages",
]
for table in tables_to_add:
    r = api("POST", f"/refs/apps/{APP}",
            {"table_name": table, "columns": ["*"], "permissions": ["read"]}, token)
    if r and "_error" not in r:
        print(f"  ADDED: {table}")
    else:
        detail = r.get("_detail", "") if isinstance(r, dict) else ""
        print(f"  FAIL: {table} -> {detail[:150]}")

# 3) 列出所有 refs
print("\n=== All refs ===")
refs = api("GET", f"/refs/apps/{APP}", None, token)
if isinstance(refs, list):
    print(f"  Total: {len(refs)}")
    for ref in refs:
        tn = ref.get("table_name", "?")
        cols = ref.get("columns", [])
        perms = ref.get("permissions", [])
        print(f"  {tn}: perms={perms}, cols_count={len(cols)}")

# 4) 查詢新增的表
print("\n=== Query tables ===")
for table in ["sale_orders", "crm_leads", "res_partners", "crm_teams", "crm_stages", "crm_tags"]:
    r = api("GET", f"/proxy/{APP}/{table}?limit=3", None, token)
    if r and "_error" not in r and isinstance(r, list):
        if r:
            fields = list(r[0].keys())
            print(f"\n  {table}: {len(r)}+ records")
            print(f"    Fields: {fields}")
            # Print first record
            sample = json.dumps(r[0], ensure_ascii=False)
            print(f"    Sample: {sample[:300]}")
        else:
            print(f"  {table}: empty")
    else:
        print(f"  {table}: error - {json.dumps(r, ensure_ascii=False)[:200]}")

print("\nDone!")
