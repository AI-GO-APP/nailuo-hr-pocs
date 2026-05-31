# -*- coding: utf-8 -*-
"""E2E 驗證：呼叫所有 Action 確認功能正常"""
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
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

def run_action(name, params=None):
    return api("POST", f"/actions/apps/{APP}/run/{name}", params or {}, token)

# ========== Test 1: Dashboard (skip AI) ==========
print("=== Test 1: Dashboard ===")
r = run_action("analyze_churn", {"action": "dashboard", "skip_ai": True})
if "_error" in r:
    print(f"  FAIL: {json.dumps(r, ensure_ascii=False)[:300]}")
else:
    kpi = r.get("kpi", {})
    customers = r.get("customer_ranking", [])
    cats = r.get("category_distribution", [])
    top5 = r.get("top5_customers", [])
    print(f"  KPI: total_logs={kpi.get('total_logs')}, high_risk={kpi.get('high_risk_customers')}, top_cat={kpi.get('top_category')}")
    print(f"  Customers: {len(customers)} entries")
    if customers:
        c0 = customers[0]
        print(f"    Top: {c0.get('company')} (risk={c0.get('max_risk')}, grade={c0.get('grade')})")
    print(f"  Categories: {json.dumps(cats, ensure_ascii=False)}")
    print(f"  Top 5: {[c.get('company') for c in top5]}")

# ========== Test 2: Sales Analysis ==========
print("\n=== Test 2: Sales Analysis ===")
r = run_action("analyze_churn", {"action": "sales_analysis", "skip_ai": True})
if "_error" in r:
    print(f"  FAIL: {json.dumps(r, ensure_ascii=False)[:300]}")
else:
    kpi = r.get("kpi", {})
    staff = r.get("staff_ranking", [])
    quadrant = r.get("quadrant_data", [])
    print(f"  KPI: total_staff={kpi.get('total_staff')}, concentrated={kpi.get('concentrated_risk')}")
    print(f"  Staff ranking: {len(staff)} entries")
    for s in staff:
        print(f"    {s.get('name')}: {s.get('customer_count')}客戶 / {s.get('high_risk_count')}高風險 / {s.get('visits')}次拜訪")
    print(f"  Quadrant data: {len(quadrant)} points")

# ========== Test 3: Category Detail ==========
print("\n=== Test 3: Category Detail (競爭搶單) ===")
r = run_action("analyze_churn", {"action": "category_detail", "category": "競爭搶單", "skip_ai": True})
if "_error" in r:
    print(f"  FAIL: {json.dumps(r, ensure_ascii=False)[:300]}")
else:
    print(f"  Total logs: {r.get('total_logs')}")
    print(f"  Total customers: {r.get('total_customers')}")
    print(f"  Top customers: {json.dumps(r.get('top_customers', []), ensure_ascii=False)}")

# ========== Test 4: Data Source ==========
print("\n=== Test 4: Data Source (refs_status) ===")
r = run_action("fetch_crm_data", {"action": "refs_status"})
if "_error" in r:
    print(f"  FAIL: {json.dumps(r, ensure_ascii=False)[:300]}")
else:
    sources = r.get("sources", [])
    for s in sources:
        print(f"  {s.get('name')}: {s.get('status')} ({s.get('count', '?')} records) [{s.get('type', 'proxy')}]")

# ========== Test 5: Raw Logs ==========
print("\n=== Test 5: Raw Logs ===")
r = run_action("fetch_crm_data", {"action": "raw_logs"})
if "_error" in r:
    print(f"  FAIL: {json.dumps(r, ensure_ascii=False)[:300]}")
else:
    logs = r.get("logs", [])
    print(f"  Total logs: {len(logs)}")
    if logs:
        d = logs[0].get("data", {})
        print(f"  First log: {d.get('date')} | {d.get('salesperson')} | {d.get('company')} | {d.get('work_nature')}")
        print(f"    Desc: {d.get('description', '')[:80]}")
        # 檢查 emoji
        import re
        emoji_pattern = re.compile("[\U0001F300-\U0001F9FF]|[\u2600-\u27BF]|[\uFE00-\uFE0F]|[\u200D]|[\u20E3]|[\uFE0F]")
        all_text = " ".join([
            l.get("data", {}).get("description", "") + " " +
            l.get("data", {}).get("ai_reason", "") + " " +
            l.get("data", {}).get("work_nature", "")
            for l in logs
        ])
        emoji_matches = emoji_pattern.findall(all_text)
        if emoji_matches:
            print(f"  WARNING: Found {len(emoji_matches)} emoji characters!")
        else:
            print(f"  No emoji found in {len(logs)} logs")

# ========== Summary ==========
print("\n=== SUMMARY ===")
print("All 5 tests completed.")
print("Dashboard app deployed at: https://tslg-churn-analysis-manager.ai-go.app")
