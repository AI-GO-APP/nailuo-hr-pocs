# -*- coding: utf-8 -*-
"""三合一調查: 模板App + Manager Dashboard分析 + CRM tables"""
import json, urllib.request, ssl, re, os
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
        return {"_error": e.code, "_detail": e.read().decode()[:300]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# ==========================================
# Part 1: Template App
# ==========================================
print("=" * 60)
print("  Part 1: Template App 7c80cf79")
print("=" * 60)
app_data = api("GET", f"/builder/apps/{APP}", None, token)
print(f"  Name: {app_data.get('name')}")
print(f"  Slug: {app_data.get('slug')}")
print(f"  VFS Version: {app_data.get('vfs_version')}")

vfs = app_data.get("vfs_state", {})
print(f"  Files: {len(vfs)}")
for path in sorted(vfs):
    content = vfs[path] or ""
    print(f"    {path} ({len(content)} chars)")

refs = api("GET", f"/refs/apps/{APP}", None, token)
print(f"\n  Data References: {len(refs) if isinstance(refs, list) else 0}")
if isinstance(refs, list):
    for r in refs:
        print(f"    {r.get('table_name')} (model: {r.get('model_name','?')})")

tables = api("GET", "/data/objects", None, token) or []
app_tables = [t for t in tables if t.get("app_id") == APP]
print(f"\n  Custom Tables: {len(app_tables)}")
for t in app_tables:
    print(f"    {t.get('api_slug')} ({t.get('name')})")

# Print key file contents (App.tsx, routes, db, action, api)
for key_file in ["src/App.tsx", "src/routes.ts", "src/db.ts", "src/action.ts",
                  "src/api.ts", "manifest.json", "package.json"]:
    content = vfs.get(key_file, "") or ""
    if content.strip():
        print(f"\n  --- {key_file} ---")
        for i, line in enumerate(content.split("\n")[:30]):
            print(f"    L{i+1}: {line[:150]}")
        if len(content.split("\n")) > 30:
            print(f"    ... ({len(content.split(chr(10)))} total lines)")

# ==========================================
# Part 2: CRM/Sales proxy tables discovery
# ==========================================
print("\n" + "=" * 60)
print("  Part 2: CRM/Sales Proxy Tables")
print("=" * 60)

# Try known table names
candidates = [
    "sale_orders", "sale_order_lines",
    "crm_leads", "crm_tags", "crm_teams", "crm_stages",
    "res_partners",
    "mail_activities",
    "account_moves", "account_move_lines",
    "product_products", "product_templates",
    "stock_pickings",
    "discuss_channels",
]

for table in candidates:
    r = api("GET", f"/proxy/tables/{table}?limit=2", None, token)
    if r and "_error" not in r:
        if isinstance(r, list):
            count = len(r)
            fields = list(r[0].keys()) if r else []
            print(f"\n  FOUND: {table} ({count}+ records)")
            print(f"    Fields: {fields}")
        elif isinstance(r, dict) and "results" in r:
            count = len(r.get("results", []))
            fields = list(r["results"][0].keys()) if r.get("results") else []
            print(f"\n  FOUND: {table} ({count}+ records)")
            print(f"    Fields: {fields}")
    else:
        # Silently skip
        pass

# Also try the HR app's existing ref table names that are CRM-related
HR_APP = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"
hr_refs = api("GET", f"/refs/apps/{HR_APP}", None, token)
if isinstance(hr_refs, list):
    for r in hr_refs:
        tn = r.get("table_name", "")
        if tn.startswith(("sale", "crm")):
            print(f"\n  HR App has ref: {tn} (model: {r.get('model_name','?')})")
            # Query it
            data = api("GET", f"/proxy/tables/{tn}?limit=2", None, token)
            if isinstance(data, list) and data:
                print(f"    Fields: {list(data[0].keys())}")
                print(f"    Sample: {json.dumps(data[0], ensure_ascii=False)[:300]}")

# Try to find the actual query method used in the HR app
print("\n  --- Query method from HR db.ts ---")
hr_app = api("GET", f"/builder/apps/{HR_APP}", None, token)
hr_db = hr_app.get("vfs_state", {}).get("src/db.ts", "")
# Extract query function
for i, line in enumerate(hr_db.split("\n")):
    if "query" in line.lower() and ("function" in line or "export" in line or "fetch" in line or "proxy" in line):
        for j in range(i, min(i+5, len(hr_db.split("\n")))):
            print(f"    L{j+1}: {hr_db.split(chr(10))[j][:150]}")
        print()

# ==========================================
# Part 3: Manager Dashboard feature summary
# ==========================================
print("\n" + "=" * 60)
print("  Part 3: Manager Dashboard 功能摘要")
print("=" * 60)

fpath = r"c:\Users\User\dev project\AI GO-MODEL\nailuo-hr-pocs\churn-analysis\manager-dashboard.html"
with open(fpath, "r", encoding="utf-8") as f:
    content = f.read()

# Extract nav items
nav_items = re.findall(r'nav-item[^>]*>.*?<span[^>]*>([^<]+)</span>.*?</div>', content, re.DOTALL)
# Also try simple pattern
nav_items2 = re.findall(r'onclick="goTo\(\'(\w+)\'\)"', content)
print(f"\n  Screens/Pages: {nav_items2}")

# Extract screen IDs
screens = re.findall(r'id="screen-(\w+)"', content)
print(f"  Screen IDs: {screens}")

# KPI cards
kpi_labels = re.findall(r'kpi-label["\']?>([^<]+)<', content)
print(f"\n  KPI 指標: {kpi_labels}")

# Panel titles
panel_titles = re.findall(r'panel-title["\']?>([^<]+)<', content)
print(f"\n  Panel 標題: {panel_titles}")

# Table headers
th_items = re.findall(r'<th>([^<]+)</th>', content)
print(f"\n  表格欄位: {th_items}")

# Data structures (JS)
data_vars = re.findall(r'const\s+(\w+)\s*=\s*\[', content)
print(f"\n  資料變數: {data_vars}")

# Risk categories
categories = re.findall(r"categories:\s*\[([\s\S]*?)\]", content)
print(f"\n  風險分類數: {len(categories)}")

print("\nDone!")
