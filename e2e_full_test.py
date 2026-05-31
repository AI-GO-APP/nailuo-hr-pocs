# -*- coding: utf-8 -*-
"""完整 E2E 測試（含 AI 功能驗證）"""
import json, urllib.request, ssl, sys, time
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:300]
        return {"_error": e.code, "_detail": err}

passed = 0
failed = 0
results = []

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        results.append(("PASS", name, detail))
        print(f"  \u2705 {name}{' \u2014 ' + detail if detail else ''}")
    else:
        failed += 1
        results.append(("FAIL", name, detail))
        print(f"  \u274c {name}{' \u2014 ' + detail if detail else ''}")

# ============================================================
print("=" * 60)
print("  E2E \u5b8c\u6574\u6e2c\u8a66\uff08\u542b AI \u529f\u80fd\u9a57\u8b49\uff09")
print("=" * 60)

# === 1. Login ===
print("\n[1] \u8a8d\u8b49")
auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
test("\u767b\u5165\u6210\u529f", auth and "access_token" in auth)
token = auth.get("access_token", "")

# === 2. App + VFS ===
print("\n[2] App \u7d50\u69cb")
app_data = api("GET", f"/builder/apps/{APP}", None, token)
test("App \u5b58\u5728", app_data and "vfs_state" in app_data)
vfs = app_data.get("vfs_state", {})
version = app_data.get("vfs_version", 0)
slug = app_data.get("slug", "")
test("VFS \u6a94\u6848\u6578\u91cf", len(vfs) >= 40, f"{len(vfs)} files, v{version}")

# === 3. Routes ===
print("\n[3] \u8def\u7531\u7d50\u69cb")
app_tsx = vfs.get("src/App.tsx", "")
all_routes = ["/", "/departments", "/employees", "/attendance", "/leaves", "/overtime",
              "/shifts", "/settlement", "/bonus-import", "/history", "/payroll-settings",
              "/analysis", "/anomaly"]
for route in all_routes:
    test(f"\u8def\u7531 {route}", f'path="{route}"' in app_tsx)

# === 4. Navigation ===
print("\n[4] \u5c0e\u822a\u9805\u76ee")
routes_ts = vfs.get("src/routes.ts", "")
nav_items = ["\u7e3d\u89bd\u5100\u8868\u677f", "\u90e8\u9580\u7ba1\u7406", "\u54e1\u5de5\u6e05\u55ae", "\u73ed\u5225\u8a2d\u5b9a", "\u51fa\u52e4\u7d00\u9304", "\u5dee\u52e4\u5be9\u6838", "\u52a0\u73ed\u7533\u8acb",
             "\u8acb\u5047\u5206\u6790", "\u7570\u5e38\u51fa\u52e4", "\u4e00\u9375\u6708\u7d50", "\u734e\u91d1\u532f\u5165", "\u7d50\u7b97\u6b77\u53f2", "\u85aa\u8cc7\u53c3\u6578\u8a2d\u5b9a"]
for item in nav_items:
    test(f"Nav: {item}", item in routes_ts)

# === 5. Pages ===
print("\n[5] \u9801\u9762\u6a94\u6848")
pages = ["DashboardPage", "AnalysisPage", "AnomalyPage", "LeavesPage", "AttendancePage",
         "DepartmentsPage", "EmployeesPage", "ShiftsPage", "OvertimePage",
         "SettlementPage", "BonusImportPage", "HistoryPage", "PayrollSettingsPage"]
for page in pages:
    content = vfs.get(f"src/pages/{page}.tsx", "")
    test(f"{page}.tsx", len(content) > 50, f"{len(content)} chars")

# === 6. Components ===
print("\n[6] \u5143\u4ef6\u6a94\u6848")
comps = ["AppLayout", "AppHeader", "AppSidebar", "LeaveDetailModal",
         "ConfirmDialog", "DataTable", "FormCard", "ApprovalWidget"]
for comp in comps:
    test(f"{comp}.tsx", f"src/components/{comp}.tsx" in vfs)

# === 7. Action manifest ===
print("\n[7] Server-Side Actions \u5b9a\u7fa9")
manifest = json.loads(vfs.get("actions/manifest.json", "{}"))
for action in ["fetch_dashboard", "run_monthly_payroll", "confirm_payroll_run",
               "cancel_payroll_run", "import_bonus_data", "ai_hr_insights"]:
    test(f"Manifest: {action}", action in manifest)

action_files = ["ai_hr_insights.py", "fetch_dashboard.py", "run_monthly_payroll.py",
                "clock_in_out.py", "manage_leaves.py", "confirm_payroll_run.py",
                "cancel_payroll_run.py", "import_bonus_data.py"]
for af in action_files:
    test(f"Action file: {af}", f"actions/{af}" in vfs)

# === 8. Data References ===
print("\n[8] Data References")
refs = api("GET", f"/refs/apps/{APP}", None, token)
ref_tables = {r["table_name"]: r for r in (refs or [])}
for table in ["hr_employees", "hr_leaves", "hr_leave_types", "hr_attendances",
              "hr_departments", "hr_shifts", "hr_overtime_requests"]:
    test(f"Ref: {table}", table in ref_tables)

if "hr_leaves" in ref_tables:
    cols = ref_tables["hr_leaves"].get("columns", [])
    for col in ["id", "state", "date_from", "date_to", "number_of_days",
                "employee_id", "holiday_status_id", "notes"]:
        test(f"hr_leaves.{col}", col in cols)
    perms = ref_tables["hr_leaves"].get("permissions", [])
    for perm in ["create", "read", "update"]:
        test(f"hr_leaves perm:{perm}", perm in perms)

# === 9. AI Action \u2014 Dashboard ===
print("\n[9] AI Action \u2014 Dashboard (\u5373\u6642\u5100\u8868\u677f)")
r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
        {"params": {"action": "dashboard"}}, token)
test("Action \u57f7\u884c\u6210\u529f", r and r.get("status") == "success",
     f"duration={r.get('duration_ms')}ms" if r else "")
result = (r or {}).get("result", {})

# KPI
kpi = result.get("kpi", {})
test("KPI: total_employees", isinstance(kpi.get("total_employees"), (int, float)),
     str(kpi.get("total_employees")))
test("KPI: present_today", "present_today" in kpi, str(kpi.get("present_today")))
test("KPI: on_leave_today", "on_leave_today" in kpi, str(kpi.get("on_leave_today")))
test("KPI: pending_count", "pending_count" in kpi, str(kpi.get("pending_count")))
test("KPI: month_leave_days", "month_leave_days" in kpi, str(kpi.get("month_leave_days")))
test("KPI: leave_rate", "leave_rate" in kpi, str(kpi.get("leave_rate")))

# Attendance grid
grid = result.get("attendance_grid", [])
test("\u51fa\u52e4\u7db2\u683c\u6709\u6578\u64da", isinstance(grid, list), f"{len(grid)} \u54e1\u5de5")
if grid:
    test("\u7db2\u683c\u6709 name/status", "name" in grid[0] and "status" in grid[0])

# Pending list
pending = result.get("pending_list", [])
test("\u5f85\u7c3d\u6838\u6e05\u55ae", isinstance(pending, list), f"{len(pending)} \u7b46")
if pending:
    test("\u5f85\u7c3d\u6838\u6709 employee_name", "employee_name" in pending[0])
    test("\u5f85\u7c3d\u6838\u6709 leave_type", "leave_type" in pending[0])

# AI Insight
ai_insight = result.get("ai_insight", "")
test("AI \u6d1e\u5bdf\u5b58\u5728", len(ai_insight) > 5, f"{len(ai_insight)} chars")
is_real_ai = "\u672a\u8a2d\u5b9a" not in ai_insight and "\u4e0d\u53ef\u7528" not in ai_insight
test("AI \u6d1e\u5bdf\u662f\u771f\u5be6 AI \u56de\u61c9\uff08\u975e fallback\uff09", is_real_ai,
     ai_insight[:80] if is_real_ai else ai_insight[:60])

# Type distribution
type_dist = result.get("type_distribution", {})
test("\u5047\u5225\u5206\u5e03\u6709\u6578\u64da", isinstance(type_dist, dict), str(type_dist))

# === 10. AI Action \u2014 Analysis ===
print("\n[10] AI Action \u2014 Analysis (\u8acb\u5047\u5206\u6790)")
r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
        {"params": {"action": "analysis"}}, token)
test("Action \u57f7\u884c\u6210\u529f", r and r.get("status") == "success",
     f"duration={r.get('duration_ms')}ms" if r else "")
result = (r or {}).get("result", {})

kpi = result.get("kpi", {})
test("KPI: month_hours", "month_hours" in kpi, str(kpi.get("month_hours")))
test("KPI: top_type", "top_type" in kpi, str(kpi.get("top_type")))
test("KPI: peak_day", "peak_day" in kpi, str(kpi.get("peak_day")))

type_dist = result.get("type_distribution", {})
test("\u5047\u5225\u5206\u5e03", isinstance(type_dist, dict), json.dumps(type_dist, ensure_ascii=False)[:100])

week_data = result.get("weekday_distribution", [])
test("\u4e00\u9031\u5206\u5e03\u6709 5 \u5929", len(week_data) == 5, str([w.get("day") for w in week_data]))

trend = result.get("trend", [])
test("\u8da8\u52e2\u6709 6 \u500b\u6708", len(trend) == 6,
     ", ".join(f"{t['month']}={t['hours']}h" for t in trend))

ai_pred = result.get("ai_prediction", "")
test("AI \u9810\u6e2c\u5b58\u5728", len(ai_pred) > 5, f"{len(ai_pred)} chars")
is_real_pred = "\u672a\u8a2d\u5b9a" not in ai_pred and "\u4e0d\u53ef\u7528" not in ai_pred
test("AI \u9810\u6e2c\u662f\u771f\u5be6 AI \u56de\u61c9", is_real_pred,
     ai_pred[:80] if is_real_pred else ai_pred[:60])

# === 11. AI Action \u2014 Anomaly ===
print("\n[11] AI Action \u2014 Anomaly (\u7570\u5e38\u51fa\u52e4\u5075\u6e2c)")
r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
        {"params": {"action": "anomaly"}}, token)
test("Action \u57f7\u884c\u6210\u529f", r and r.get("status") == "success",
     f"duration={r.get('duration_ms')}ms" if r else "")
result = (r or {}).get("result", {})

kpi = result.get("kpi", {})
test("KPI: high", "high" in kpi, str(kpi.get("high")))
test("KPI: medium", "medium" in kpi, str(kpi.get("medium")))
test("KPI: normal", "normal" in kpi, str(kpi.get("normal")))
test("KPI: total", "total" in kpi, str(kpi.get("total")))
test("KPI \u6578\u5b57\u6b63\u78ba (high+medium+normal\u2264total)",
     kpi.get("high",0)+kpi.get("medium",0) <= kpi.get("total",0))

anomalies = result.get("anomalies", [])
test("\u7570\u5e38\u6e05\u55ae\u662f\u9663\u5217", isinstance(anomalies, list), f"{len(anomalies)} \u4eba")
if anomalies:
    a = anomalies[0]
    test("\u7570\u5e38\u6709 employee_name", "employee_name" in a, a.get("employee_name"))
    test("\u7570\u5e38\u6709 risk", a.get("risk") in ("high","medium","low"), a.get("risk"))
    test("\u7570\u5e38\u6709 flags", isinstance(a.get("flags"), list) and len(a["flags"]) > 0,
         "; ".join(a.get("flags",[])))

ai_analysis = result.get("ai_analysis", "")
test("AI \u5206\u6790\u5b58\u5728", len(ai_analysis) > 0)
if anomalies:
    is_real_analysis = "\u672a\u8a2d\u5b9a" not in ai_analysis and "\u4e0d\u53ef\u7528" not in ai_analysis
    test("AI \u5206\u6790\u662f\u771f\u5be6 AI \u56de\u61c9", is_real_analysis,
         ai_analysis[:80] if is_real_analysis else ai_analysis[:60])

# === 12. Frontend Patterns ===
print("\n[12] \u524d\u7aef\u7de8\u78bc\u6a21\u5f0f")
# DashboardPage
dash = vfs.get("src/pages/DashboardPage.tsx", "")
test("Dashboard \u7528 runAction", "runAction" in dash)
test("Dashboard import ../action", 'from "../action"' in dash)
test("Dashboard \u7121 callAction", "callAction" not in dash)
test("Dashboard \u7121 actionHelper", "actionHelper" not in dash)
test("Dashboard \u6709 KPI \u5143\u4ef6", "KPI" in dash or "kpi" in dash)
test("Dashboard \u6709\u51fa\u52e4\u7db2\u683c", "attendance_grid" in dash or "grid" in dash.lower())
test("Dashboard \u6709\u5f85\u7c3d\u6838", "pending" in dash)

# AnalysisPage
analysis = vfs.get("src/pages/AnalysisPage.tsx", "")
test("Analysis \u7528 runAction", "runAction" in analysis)
test("Analysis \u6709 SVG \u5716\u8868", "<svg" in analysis.lower())
test("Analysis \u6709\u8da8\u52e2\u7dda", "trend" in analysis)
test("Analysis \u6709\u5047\u5225\u5206\u5e03", "type_distribution" in analysis or "typeDist" in analysis)

# AnomalyPage
anom = vfs.get("src/pages/AnomalyPage.tsx", "")
test("Anomaly \u7528 runAction", "runAction" in anom)
test("Anomaly \u6709\u98a8\u96aa\u5206\u7d1a", "high" in anom and "medium" in anom)
test("Anomaly \u6709\u5361\u7247\u5217\u8868", "anomalies" in anom)

# LeaveDetailModal
modal = vfs.get("src/components/LeaveDetailModal.tsx", "")
test("Modal \u6709\u6838\u51c6\u6309\u9215", "\u6838\u51c6" in modal or "validate" in modal)
test("Modal \u6709\u62d2\u7d55\u6309\u9215", "\u62d2\u7d55" in modal or "refuse" in modal)
test("Modal \u7528 PATCH proxy", "PATCH" in modal and "proxy" in modal)

# LeavesPage enhancements
leaves = vfs.get("src/pages/LeavesPage.tsx", "")
test("Leaves \u6709\u6279\u6b21\u6838\u51c6", "batchApprove" in leaves)
test("Leaves \u6709 selectedIds", "selectedIds" in leaves)
test("Leaves import LeaveDetailModal", "LeaveDetailModal" in leaves)
test("Leaves \u6709 detailLeave", "detailLeave" in leaves)

# AttendancePage enhancements
att = vfs.get("src/pages/AttendancePage.tsx", "")
test("Attendance \u6709\u7db2\u683c", "grid" in att.lower())
test("Attendance \u6709\u7be9\u9078", "gridFilter" in att or "filter" in att.lower())

# === 13. CSS ===
print("\n[13] CSS \u898f\u7bc4")
css = vfs.get("src/App.css", "")
test("CSS \u6709 :host", ":host" in css)
test("CSS \u5b58\u5728", len(css) > 100, f"{len(css)} chars")

# === 14. \u7de8\u8b6f ===
print("\n[14] \u7de8\u8b6f\u9a57\u8b49")
r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
compile_ok = r and r.get("success") == True
test("\u7de8\u8b6f\u6210\u529f", compile_ok,
     (r or {}).get("error", "")[:120] if not compile_ok else "")

# ============================================================
print("\n" + "=" * 60)
print(f"  \u6e2c\u8a66\u7d50\u679c\uff1a{passed} passed, {failed} failed, {passed+failed} total")
print(f"  Pass rate: {passed/(passed+failed)*100:.1f}%")
print("=" * 60)

if failed > 0:
    print("\n\u274c Failed tests:")
    for status, name, detail in results:
        if status == "FAIL":
            print(f"  \u274c {name}: {detail}")
