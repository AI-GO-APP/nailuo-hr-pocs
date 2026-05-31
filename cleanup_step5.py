# -*- coding: utf-8 -*-
"""修正 ref/custom table 刪除 + 最終驗證"""
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
            raw = r.read().decode("utf-8")
            if not raw.strip():
                return {"_ok": True}
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:300]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# Step 5: 移除 Data References
print("[Step 5] 移除未使用的 Data References")
refs_to_remove = ["hr_payroll_bonus_rule_results", "hr_payroll_settings",
                   "hr_payroll_slip_lines", "crm_tags", "sale_orders"]

refs = api("GET", f"/refs/apps/{APP}", None, token)
if isinstance(refs, list):
    for ref in refs:
        table = ref.get("table_name", "")
        ref_id = ref.get("id", "")
        if table in refs_to_remove:
            # Try multiple delete paths
            for path in [f"/refs/apps/{APP}/{ref_id}", f"/refs/{ref_id}",
                         f"/refs/apps/{APP}/refs/{ref_id}"]:
                r = api("DELETE", path, None, token)
                if r and "_error" not in r:
                    print(f"  移除 ref {table}: OK ({path})")
                    break
            else:
                print(f"  移除 ref {table}: 需手動操作（API 不支持刪除）")
else:
    print(f"  無法取得 refs: {refs}")

# Step 6: 移除 Custom Tables
print("\n[Step 6] 移除舊 Custom Tables")
all_tables = api("GET", "/data/objects", None, token) or []
for t in (all_tables if isinstance(all_tables, list) else []):
    slug_name = t.get("api_slug", "")
    if slug_name in ["bonus_records_8e0a2d", "payroll_records"]:
        tid = t.get("id", "")
        r = api("DELETE", f"/data/objects/{tid}", None, token)
        if r and "_error" not in r:
            print(f"  移除 {slug_name}: OK")
        else:
            print(f"  移除 {slug_name}: {r}")

# Step 7: 最終驗證
print("\n[Step 7] 最終驗證")
app_final = api("GET", f"/builder/apps/{APP}", None, token)
vfs_final = app_final["vfs_state"]

# Check deleted files
deleted_files = [
    "src/pages/ListPage.tsx", "src/pages/BonusRulesPage.tsx",
    "src/pages/PayslipsPage.tsx", "src/components/DataTable.tsx",
    "src/components/PayslipDetail.tsx", "src/data.json",
    "src/utils/dbHelper.ts", "actions/summarize_leads.py",
    "actions/manage_leaves.py", "actions/confirm_payroll_run.py",
]
for f in deleted_files:
    content = vfs_final.get(f, None)
    if content is None:
        status = "已刪除"
    elif content.strip() == "":
        status = "已清空"
    else:
        status = f"仍有內容 ({len(content)} chars)"
    print(f"  {f.split('/')[-1]}: {status}")

# Active files count
active_files = [f for f in vfs_final if vfs_final[f] and vfs_final[f].strip()]
print(f"\n  有效檔案: {len(active_files)} (原 52)")

# CSS size
css_final = vfs_final.get("src/App.css", "")
print(f"  CSS: {len(css_final):,} chars")

# Remaining refs
refs_final = api("GET", f"/refs/apps/{APP}", None, token) or []
ref_names = [r.get("table_name") for r in refs_final] if isinstance(refs_final, list) else []
print(f"  Refs: {len(ref_names)} — {ref_names}")

# Custom tables
tables_final = api("GET", "/data/objects", None, token) or []
our_tables = [t for t in tables_final if t.get("app_id") == APP]
print(f"  Custom Tables: {[t.get('api_slug') for t in our_tables]}")

# Compile check
slug_name = app_final["slug"]
r = api("POST", f"/compile/compile/{slug_name}?dev=true", None, token)
print(f"  編譯: {'OK' if r and r.get('success') else 'FAILED'}")

print("\nDone!")
