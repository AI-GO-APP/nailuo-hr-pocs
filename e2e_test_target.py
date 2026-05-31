# -*- coding: utf-8 -*-
"""完整 E2E 測試 - 目標 App 全功能驗證"""
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
        with urllib.request.urlopen(req, timeout=30) as r:
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
        print(f"  ✅ {name}{' — ' + detail if detail else ''}")
    else:
        failed += 1
        results.append(("FAIL", name, detail))
        print(f"  ❌ {name}{' — ' + detail if detail else ''}")

# === Login ===
print("[1] Authentication")
auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
test("Login", auth and "access_token" in auth)
token = auth.get("access_token", "")

# === App exists ===
print("\n[2] App exists + VFS")
app_data = api("GET", f"/builder/apps/{APP}", None, token)
test("App exists", app_data and "vfs_state" in app_data)
vfs = app_data.get("vfs_state", {})
version = app_data.get("vfs_version", 0)
test("VFS has files", len(vfs) >= 40, f"{len(vfs)} files")

# === Check routes ===
print("\n[3] Route structure")
app_tsx = vfs.get("src/App.tsx", "")
for route in ["/", "/departments", "/employees", "/attendance", "/leaves", "/overtime", 
              "/shifts", "/settlement", "/bonus-import", "/history", "/payroll-settings",
              "/analysis", "/anomaly"]:
    has = f'path="{route}"' in app_tsx or f"path=\"{route}\"" in app_tsx
    test(f"Route {route}", has)

# === Check navigation ===
print("\n[4] Navigation items")
routes_ts = vfs.get("src/routes.ts", "")
for item in ["總覽儀表板", "部門管理", "員工清單", "班別設定", "出勤紀錄", "差勤審核", "加班申請",
             "請假分析", "異常出勤", "一鍵月結", "獎金匯入", "結算歷史", "薪資參數設定"]:
    has = item in routes_ts
    test(f"Nav: {item}", has)

# === Check page imports ===
print("\n[5] Page files exist")
for page in ["DashboardPage", "AnalysisPage", "AnomalyPage", "LeavesPage", "AttendancePage",
             "DepartmentsPage", "EmployeesPage", "ShiftsPage", "OvertimePage",
             "SettlementPage", "BonusImportPage", "HistoryPage", "PayrollSettingsPage"]:
    has = f"src/pages/{page}.tsx" in vfs
    test(f"Page: {page}.tsx", has, f"{len(vfs.get(f'src/pages/{page}.tsx',''))} chars")

# === Check components ===
print("\n[6] Component files exist")
for comp in ["AppLayout", "AppHeader", "AppSidebar", "LeaveDetailModal", "ConfirmDialog", 
             "DataTable", "FormCard", "ApprovalWidget"]:
    has = f"src/components/{comp}.tsx" in vfs
    test(f"Component: {comp}.tsx", has)

# === Check actions ===
print("\n[7] Server-Side Actions")
manifest = json.loads(vfs.get("actions/manifest.json", "{}"))
for action in ["fetch_dashboard", "run_monthly_payroll", "confirm_payroll_run", 
               "cancel_payroll_run", "import_bonus_data", "ai_hr_insights"]:
    has = action in manifest
    test(f"Action manifest: {action}", has)

for action_file in ["ai_hr_insights.py", "fetch_dashboard.py", "run_monthly_payroll.py",
                     "clock_in_out.py", "manage_leaves.py"]:
    has = f"actions/{action_file}" in vfs
    test(f"Action file: {action_file}", has)

# === Test AI Action (Dashboard) ===
print("\n[8] AI Action — Dashboard")
r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights", {"params": {"action": "dashboard"}}, token)
test("Dashboard action success", r and r.get("status") == "success")
result = (r or {}).get("result", {})
test("Dashboard has KPI", "kpi" in result)
test("Dashboard has attendance_grid", "attendance_grid" in result)
test("Dashboard has pending_list", "pending_list" in result)
test("Dashboard has ai_insight", "ai_insight" in result)
kpi = result.get("kpi", {})
test("KPI has total_employees", "total_employees" in kpi, str(kpi.get("total_employees")))
test("KPI has pending_count", "pending_count" in kpi, str(kpi.get("pending_count")))
test("KPI has leave_rate", "leave_rate" in kpi, str(kpi.get("leave_rate")))

# === Test AI Action (Analysis) ===
print("\n[9] AI Action — Analysis")
r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights", {"params": {"action": "analysis"}}, token)
test("Analysis action success", r and r.get("status") == "success")
result = (r or {}).get("result", {})
test("Analysis has type_distribution", "type_distribution" in result)
test("Analysis has weekday_distribution", "weekday_distribution" in result)
test("Analysis has trend", "trend" in result)
test("Analysis has ai_prediction", "ai_prediction" in result)
trend = result.get("trend", [])
test("Trend has 6 months", len(trend) == 6, f"got {len(trend)}")

# === Test AI Action (Anomaly) ===
print("\n[10] AI Action — Anomaly")
r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights", {"params": {"action": "anomaly"}}, token)
test("Anomaly action success", r and r.get("status") == "success")
result = (r or {}).get("result", {})
test("Anomaly has KPI", "kpi" in result)
test("Anomaly has anomalies list", "anomalies" in result)
test("Anomaly has ai_analysis", "ai_analysis" in result)
anomaly_kpi = result.get("kpi", {})
test("Anomaly KPI has risk levels", "high" in anomaly_kpi and "medium" in anomaly_kpi)

# === Data References ===
print("\n[11] Data References")
refs = api("GET", f"/refs/apps/{APP}", None, token)
ref_tables = {r["table_name"]: r for r in (refs or [])}
for table in ["hr_employees", "hr_leaves", "hr_leave_types", "hr_attendances", 
              "hr_departments", "hr_shifts", "hr_overtime_requests"]:
    has = table in ref_tables
    test(f"Ref: {table}", has)

# Check hr_leaves has needed columns
if "hr_leaves" in ref_tables:
    cols = ref_tables["hr_leaves"].get("columns", [])
    for col in ["id", "state", "date_from", "date_to", "number_of_days", "employee_id", "holiday_status_id"]:
        test(f"hr_leaves col: {col}", col in cols)

# Check hr_leaves permissions
if "hr_leaves" in ref_tables:
    perms = ref_tables["hr_leaves"].get("permissions", [])
    for perm in ["create", "read", "update"]:
        test(f"hr_leaves perm: {perm}", perm in perms)

# === DashboardPage uses runAction ===
print("\n[12] Frontend patterns")
dash = vfs.get("src/pages/DashboardPage.tsx", "")
test("Dashboard uses runAction", "runAction" in dash)
test("Dashboard imports from ../action", 'from "../action"' in dash)
test("Dashboard does NOT use callAction", "callAction" not in dash)

analysis = vfs.get("src/pages/AnalysisPage.tsx", "")
test("AnalysisPage uses runAction", "runAction" in analysis)
test("AnalysisPage has SVG chart", "<svg" in analysis.lower() or "svg" in analysis.lower())

anomaly_page = vfs.get("src/pages/AnomalyPage.tsx", "")
test("AnomalyPage uses runAction", "runAction" in anomaly_page)
test("AnomalyPage has risk colors", "high" in anomaly_page and "medium" in anomaly_page)

# === LeaveDetailModal ===
print("\n[13] LeaveDetailModal")
modal = vfs.get("src/components/LeaveDetailModal.tsx", "")
test("LeaveDetailModal exists", len(modal) > 100)
test("Modal has approve button", "核准" in modal or "validate" in modal)
test("Modal has reject button", "拒絕" in modal or "refuse" in modal)

# === LeavesPage enhancements ===
print("\n[14] LeavesPage enhancements")
leaves = vfs.get("src/pages/LeavesPage.tsx", "")
test("LeavesPage has batch approve", "batchApprove" in leaves or "批次" in leaves)
test("LeavesPage has selectedIds", "selectedIds" in leaves)
test("LeavesPage imports LeaveDetailModal", "LeaveDetailModal" in leaves)
test("LeavesPage has detailLeave state", "detailLeave" in leaves)

# === AttendancePage enhancements ===
print("\n[15] AttendancePage enhancements")
att = vfs.get("src/pages/AttendancePage.tsx", "")
test("AttendancePage has grid", "grid" in att.lower() or "網格" in att)
test("AttendancePage has filter", "gridFilter" in att or "filter" in att.lower())

# === CSS rules ===
print("\n[16] CSS rules")
app_css = vfs.get("src/App.css", "")
test("CSS has :host selector", ":host" in app_css)
test("CSS exists", len(app_css) > 100)

# === Compilation ===
print("\n[17] Compilation")
slug = app_data.get("slug", "")
r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
test("Compile success", r and r.get("success") == True, str(r.get("error", ""))[:100] if r and not r.get("success") else "")

# === Summary ===
print(f"\n{'='*50}")
print(f"E2E Test Results: {passed} passed, {failed} failed, {passed+failed} total")
print(f"Pass rate: {passed/(passed+failed)*100:.1f}%")

if failed > 0:
    print("\nFailed tests:")
    for status, name, detail in results:
        if status == "FAIL":
            print(f"  ❌ {name}: {detail}")
