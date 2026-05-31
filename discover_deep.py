# -*- coding: utf-8 -*-
"""深挖所有可用的 proxy tables 和 ref"""
import json, urllib.request, ssl
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
HR = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"
TARGET = "7c80cf79-7225-49b6-9657-3f8c719658ec"

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

# 1) 列出所有 apps 及其 refs
print("=== All Apps & Refs ===")
all_apps = api("GET", "/builder/apps", None, token)
if isinstance(all_apps, list):
    for a in all_apps:
        aid = a.get("id", "")
        refs = api("GET", f"/refs/apps/{aid}", None, token)
        if isinstance(refs, list) and refs:
            print(f"\nApp: {a.get('name','?')} ({aid[:8]}...)")
            for r in refs:
                print(f"  {r.get('table_name')} (model: {r.get('model_name','?')})")

# 2) 透過 HR app 查詢 sale_orders (已有 ref)
print("\n=== sale_orders via HR app ===")
r = api("GET", f"/proxy/{HR}/sale_orders?limit=3", None, token)
if isinstance(r, list) and r:
    print(f"  Records: {len(r)}")
    print(f"  Fields: {list(r[0].keys())}")
    print(f"  Sample: {json.dumps(r[0], ensure_ascii=False)[:300]}")
else:
    print(f"  Result: {r}")

# 3) 透過 HR app 查詢 crm_tags (已有 ref... 但已被移除)
# 嘗試透過 target app 查詢
print("\n=== crm_tags via target app ===")
refs_target = api("GET", f"/refs/apps/{TARGET}", None, token)
print(f"  Target app refs: {refs_target}")

# 4) 嘗試新增 ref 到 target app
# First, let's see what models are available for ref
print("\n=== Available models for ref ===")
models = api("GET", "/refs/models", None, token)
if isinstance(models, list):
    for m in models:
        name = m.get("name", "") if isinstance(m, dict) else str(m)
        if any(k in name.lower() for k in ["crm", "sale", "res.partner", "mail", "account", "product"]):
            print(f"  {name}")
elif isinstance(models, dict):
    for k in sorted(models.keys()):
        if any(t in k.lower() for t in ["crm", "sale", "partner", "mail", "product"]):
            print(f"  {k}: {models[k]}")
else:
    print(f"  (unexpected: {type(models).__name__})")
    print(f"  {str(models)[:500]}")

# 5) List all proxy tables available on the platform
print("\n=== All proxy tables (via HR app) ===")
# Try to list tables
for table in [
    "sale_orders", "sale_order_lines",
    "crm_leads", "crm_lead_tags", "crm_tags",
    "res_partners", "res_users",
    "mail_activities", "mail_messages",
    "account_moves", "account_move_lines",
    "product_products", "product_templates",
    "crm_teams", "crm_stages",
    "hr_employees", "hr_departments",
]:
    r = api("GET", f"/proxy/{HR}/{table}?limit=1", None, token)
    if r and "_error" not in r:
        if isinstance(r, list):
            fields = list(r[0].keys()) if r else "empty"
            count = f"{len(r)}+ records"
            print(f"  {table}: {count}, fields={fields}")
        else:
            print(f"  {table}: exists (format: {type(r).__name__})")

# 6) Check ref creation API
print("\n=== Try creating ref for target app ===")
# We need to find the right API to add a ref
# Check existing ref structure
hr_refs = api("GET", f"/refs/apps/{HR}", None, token)
if isinstance(hr_refs, list) and hr_refs:
    sample = hr_refs[0]
    print(f"  Ref structure: {json.dumps(sample, ensure_ascii=False)[:300]}")

print("\nDone!")
