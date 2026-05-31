# -*- coding: utf-8 -*-
"""清理殘留檔案 + 最終驗證"""
import json, urllib.request, ssl, time
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# ===== 1. 清理殘留檔案 =====
# 無法刪除 VFS 檔案，只能清空或保留
# 但空檔案不會影響編譯，所以只處理 manifest

# 更新 manifest — 只保留有用的 action
manifest = {
    "actions": [
        {"name": "analyze_churn", "file": "actions/analyze_churn.py", "description": "客戶流失風險分析"},
        {"name": "fetch_crm_data", "file": "actions/fetch_crm_data.py", "description": "CRM 資料來源查詢"}
    ]
}

# 清空殘留檔案 + 更新 manifest
cleanup = {
    "actions/manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2),
    "actions/debug_ctx.py": "",
    "actions/summarize_leads.py": "",
    "src/data.json": "",
    "src/pages/ListPage.tsx": "",
}

print("=== 1. 清理殘留檔案 ===")
r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": cleanup}, token)
print(f"  {'OK' if r and '_error' not in r else 'FAIL'}")

# ===== 2. 重新編譯 + 發佈 =====
slug = "da1900f990b0"
time.sleep(1)
c = api("POST", f"/compile/compile/{slug}", None, token)
errors = c.get("compile_errors", [])
print(f"\n=== 2. 編譯 ===")
print(f"  success={c.get('success')}, errors={len(errors)}")
for e in errors:
    print(f"  Error: {json.dumps(e, ensure_ascii=False)[:200]}")

html = c.get("html", "")
if c.get("success"):
    r = api("POST", f"/builder/apps/{APP}/publish", {"published_assets": {"html": html}}, token)
    print(f"  Publish: {'OK' if r and '_error' not in r else 'FAIL'}")

# ===== 3. E2E Action 驗證 =====
print(f"\n=== 3. Action E2E 驗證 ===")

# Dashboard
r = api("POST", f"/actions/apps/{APP}/run/analyze_churn", {"params": {"action": "dashboard", "skip_ai": True}}, token)
result = r.get("result") or {}
kpi = result.get("kpi", {})
customers = result.get("customer_ranking", [])
cats = result.get("category_distribution", [])
top5 = result.get("top5_customers", [])
print(f"\n  [Dashboard]")
print(f"    KPI: total_logs={kpi.get('total_logs')}, high_risk_customers={kpi.get('high_risk_customers')}, high_risk_logs={kpi.get('high_risk_logs')}, top_category={kpi.get('top_category')}")
print(f"    customer_ranking: {len(customers)} entries")
print(f"    category_distribution: {len(cats)} categories: {json.dumps(cats, ensure_ascii=False)}")
print(f"    top5_customers: {[c.get('company') for c in top5]}")

# Sales
r = api("POST", f"/actions/apps/{APP}/run/analyze_churn", {"params": {"action": "sales_analysis", "skip_ai": True}}, token)
result = r.get("result") or {}
staff = result.get("staff_ranking", [])
quadrant = result.get("quadrant_data", [])
sales_kpi = result.get("kpi", {})
print(f"\n  [Sales]")
print(f"    KPI: total_staff={sales_kpi.get('total_staff')}, concentrated_risk={sales_kpi.get('concentrated_risk')}")
print(f"    staff_ranking: {len(staff)} entries")
for s in staff:
    print(f"      {s.get('name')}: {s.get('customer_count')} customers, {s.get('high_risk_count')} high risk, {s.get('visits')} visits, avg_risk={s.get('avg_risk')}")
print(f"    quadrant_data: {len(quadrant)} points")

# Category Detail
for cat_name in ["競爭搶單", "品質客訴", "帳款問題"]:
    r = api("POST", f"/actions/apps/{APP}/run/analyze_churn", {"params": {"action": "category_detail", "category": cat_name, "skip_ai": True}}, token)
    result = r.get("result") or {}
    print(f"\n  [Category: {cat_name}]")
    print(f"    total_logs={result.get('total_logs')}, total_customers={result.get('total_customers')}")
    print(f"    top_customers: {json.dumps(result.get('top_customers', []), ensure_ascii=False)}")
    print(f"    top_staff: {json.dumps(result.get('top_staff', []), ensure_ascii=False)}")

# Data Source
r = api("POST", f"/actions/apps/{APP}/run/fetch_crm_data", {"params": {"action": "refs_status"}}, token)
result = r.get("result") or {}
sources = result.get("sources", [])
print(f"\n  [DataSource]")
for s in sources:
    print(f"    {s.get('name')}: {s.get('status')} ({s.get('count', '?')} records) [{s.get('type', 'proxy')}]")

# Raw Logs
r = api("POST", f"/actions/apps/{APP}/run/fetch_crm_data", {"params": {"action": "raw_logs"}}, token)
result = r.get("result") or {}
logs = result.get("logs", [])
print(f"\n  [Raw Logs]")
print(f"    Total: {len(logs)} logs")
if logs:
    d = logs[0].get("data", {})
    print(f"    Sample: {d.get('date')} | {d.get('salesperson')} | {d.get('company')} | {d.get('work_nature')}")
    print(f"    Description: {d.get('description', '')[:100]}")

# ===== 4. VFS 最終清單 =====
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data.get("vfs_state", {})
print(f"\n=== 4. VFS 最終檔案清單 ({len(vfs)} files) ===")
for path in sorted(vfs.keys()):
    size = len(vfs[path])
    status = "OK" if size > 0 else "EMPTY"
    print(f"  [{status}] {path}: {size} chars")

print("\n=== 盤點完成 ===")
print("App URL: https://tslg-churn-analysis-manager.ai-go.app")
