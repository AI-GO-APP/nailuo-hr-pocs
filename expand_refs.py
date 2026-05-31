# -*- coding: utf-8 -*-
"""展開 ref 欄位 + 修正 res_partners"""
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

# Delete bad refs (res_partners doesn't exist)
refs = api("GET", f"/refs/apps/{APP}", None, token)
for ref in (refs if isinstance(refs, list) else []):
    tn = ref.get("table_name")
    rid = ref.get("id")
    if tn == "res_partners":
        r = api("DELETE", f"/refs/{rid}", None, token)
        print(f"Deleted {tn}: OK")

# Update refs to have all columns (not just '*')
# For each ref, delete and re-create with proper columns
# First find out what columns exist by querying schema
for table in ["sale_orders", "crm_leads", "crm_teams", "crm_stages", "crm_tags", "sale_order_lines", "mail_activities", "mail_messages"]:
    # Try querying with POST to get all fields
    r = api("POST", f"/proxy/{APP}/{table}/query",
            {"limit": 1, "columns": ["*"]}, token)
    if isinstance(r, list) and r:
        fields = list(r[0].keys())
        print(f"\n{table}: {len(fields)} fields")
        print(f"  {fields}")
        # Update ref with these columns
        # Find ref id
        for ref in (refs if isinstance(refs, list) else []):
            if ref.get("table_name") == table:
                rid = ref["id"]
                # Update columns
                r2 = api("PATCH", f"/refs/{rid}",
                         {"columns": fields, "permissions": ["read", "write"]}, token)
                if r2 and "_error" not in r2:
                    print(f"  Updated ref with {len(fields)} columns + write")
                else:
                    print(f"  Update failed: {r2}")
                break
    elif isinstance(r, dict) and r.get("results"):
        fields = list(r["results"][0].keys())
        print(f"\n{table}: {len(fields)} fields (dict)")
        print(f"  {fields}")
    else:
        # Try GET
        r2 = api("GET", f"/proxy/{APP}/{table}?limit=1", None, token)
        if isinstance(r2, list) and r2:
            fields = list(r2[0].keys())
            print(f"\n{table} (GET): {len(fields)} fields")
            print(f"  {fields}")
        else:
            print(f"\n{table}: no data or error")

# Now query with actual data
print("\n\n=== Data Samples ===")
for table in ["sale_orders", "crm_leads", "crm_teams", "crm_stages"]:
    r = api("POST", f"/proxy/{APP}/{table}/query",
            {"limit": 2, "columns": ["*"]}, token)
    if isinstance(r, list) and r:
        print(f"\n{table} sample:")
        for rec in r[:1]:
            print(f"  {json.dumps(rec, ensure_ascii=False)[:400]}")

# Count records
print("\n\n=== Record Counts ===")
for table in ["sale_orders", "crm_leads", "crm_teams", "crm_stages", "crm_tags", "sale_order_lines", "mail_activities"]:
    r = api("POST", f"/proxy/{APP}/{table}/query",
            {"limit": 500, "columns": ["id"]}, token)
    count = len(r) if isinstance(r, list) else 0
    print(f"  {table}: {count} records")

print("\nDone!")
