# -*- coding: utf-8 -*-
"""重建 refs — 刪除舊的並用正確欄位重建"""
import json, urllib.request, ssl
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"
HR = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"

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

# HR app's refs have proper columns — use them as reference
# Let's see what columns HR app's sale_orders ref had (it was deleted but we know the pattern)
# First check schema endpoint
print("=== Schema discovery ===")
for table in ["sale_orders", "crm_leads", "crm_teams", "crm_stages", "sale_order_lines"]:
    # Try schema endpoint
    r = api("GET", f"/proxy/schema/{table}", None, token)
    if r and "_error" not in r:
        print(f"\n{table} schema: {json.dumps(r, ensure_ascii=False)[:500]}")
    
    # Try describe
    r2 = api("GET", f"/proxy/{APP}/{table}/schema", None, token)
    if r2 and "_error" not in r2:
        print(f"\n{table} schema (via app): {json.dumps(r2, ensure_ascii=False)[:500]}")

    # Try columns endpoint
    r3 = api("GET", f"/proxy/{APP}/{table}/columns", None, token)
    if r3 and "_error" not in r3:
        print(f"\n{table} columns: {json.dumps(r3, ensure_ascii=False)[:500]}")

# OK the issue is probably that columns=['*'] creates a ref that only exposes id
# Let's look at how HR app's refs were created — they have full columns
# Check HR ref for sale_orders (we removed it but other refs still exist)
hr_refs = api("GET", f"/refs/apps/{HR}", None, token)
if isinstance(hr_refs, list):
    # Get the columns of a ref that works well
    for ref in hr_refs:
        if ref.get("table_name") == "hr_employees":
            print(f"\n=== HR employees ref columns ({len(ref.get('columns',[]))}) ===")
            print(f"  {ref.get('columns')}")
            break

# Delete ALL existing refs for target app and recreate with proper columns
print("\n=== Delete all target refs ===")
refs = api("GET", f"/refs/apps/{APP}", None, token)
for ref in (refs if isinstance(refs, list) else []):
    rid = ref["id"]
    tn = ref["table_name"]
    api("DELETE", f"/refs/{rid}", None, token)
    print(f"  Deleted {tn}")

# Recreate refs with proper column lists
# We need to know what columns each table has
# Let's use the builder API to get table schema
print("\n=== Rebuild refs ===")

# First let's try the table metadata API
tables_meta = api("GET", "/proxy/tables", None, token)
if tables_meta and "_error" not in tables_meta:
    print(f"  Tables meta: {json.dumps(tables_meta, ensure_ascii=False)[:500]}")

# Try another approach — just create refs and see what the platform auto-discovers
# Based on HR pattern, they seem to specify exact column names
# Let's try creating with explicit common CRM columns

ref_specs = {
    "sale_orders": ["name", "state", "date_order", "partner_id", "user_id", "team_id",
                    "amount_total", "amount_untaxed", "currency_id", "note",
                    "tenant_id", "id", "created_at", "updated_at", "custom_data"],
    "sale_order_lines": ["order_id", "product_id", "name", "product_uom_qty", "price_unit",
                         "price_subtotal", "price_total", "state",
                         "tenant_id", "id", "created_at", "updated_at"],
    "crm_leads": ["name", "partner_id", "partner_name", "user_id", "team_id", "stage_id",
                  "type", "probability", "expected_revenue", "description",
                  "date_open", "date_closed", "date_deadline", "priority",
                  "tag_ids", "phone", "email_from", "city", "country_id",
                  "tenant_id", "id", "created_at", "updated_at", "custom_data"],
    "crm_teams": ["name", "sequence", "active", "user_id", "member_ids",
                  "tenant_id", "id", "created_at", "updated_at"],
    "crm_stages": ["name", "sequence", "is_won", "requirements", "team_id",
                   "tenant_id", "id", "created_at", "updated_at"],
    "crm_tags": ["name", "color", "tenant_id", "id", "created_at", "updated_at"],
}

for table, columns in ref_specs.items():
    r = api("POST", f"/refs/apps/{APP}",
            {"table_name": table, "columns": columns, "permissions": ["read"]}, token)
    if r and "_error" not in r:
        print(f"  Created {table}: OK")
    else:
        print(f"  Created {table}: {json.dumps(r, ensure_ascii=False)[:200]}")

# Now test queries
print("\n=== Test queries ===")
for table in ref_specs.keys():
    r = api("POST", f"/proxy/{APP}/{table}/query",
            {"limit": 1, "columns": ["*"]}, token)
    if isinstance(r, list) and r:
        fields = list(r[0].keys())
        print(f"\n  {table}: {len(fields)} fields")
        print(f"    {fields}")
        print(f"    Sample: {json.dumps(r[0], ensure_ascii=False)[:300]}")
    elif isinstance(r, list):
        print(f"\n  {table}: empty")
    else:
        print(f"\n  {table}: error - {json.dumps(r, ensure_ascii=False)[:200]}")

print("\nDone!")
