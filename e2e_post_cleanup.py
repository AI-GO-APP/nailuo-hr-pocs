# -*- coding: utf-8 -*-
"""清除後完整 E2E + 單元驗證"""
import json, urllib.request, ssl, re, time
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
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {"_ok": True}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:300]}

passed = 0; failed = 0; sections = {}

def test(section, name, ok, detail=""):
    global passed, failed
    sections.setdefault(section, [0, 0])
    if ok:
        passed += 1; sections[section][0] += 1
        print(f"  \u2705 {name}{' — ' + str(detail)[:100] if detail else ''}")
    else:
        failed += 1; sections[section][1] += 1
        print(f"  \u274c {name}{' — ' + str(detail)[:100] if detail else ''}")

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
test("認證", "登入成功", "access_token" in auth)

app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]
slug = app_data["slug"]

# =============================================================
S = "App 結構"
print(f"\n[{S}]")
active_files = {k: v for k, v in vfs.items() if v and v.strip()}
test(S, "App 存在", app_data.get("id") == APP)
test(S, f"有效檔案數量", 38 <= len(active_files) <= 45, f"{len(active_files)} files")

# =============================================================
S = "路由完整性"
print(f"\n[{S}]")
app_tsx = vfs.get("src/App.tsx", "")
routes_ts = vfs.get("src/routes.ts", "")
expected_routes = ["/", "/departments", "/employees", "/attendance", "/leaves",
                   "/overtime", "/shifts", "/settlement", "/bonus-import",
                   "/history", "/payroll-settings", "/analysis", "/anomaly"]
for r in expected_routes:
    test(S, f"路由 {r}", f'path="{r}"' in app_tsx or f"path=\"{r}\"" in app_tsx)

# =============================================================
S = "導航項目"
print(f"\n[{S}]")
nav_items = ["總覽儀表板", "部門管理", "員工清單", "班別設定", "出勤紀錄",
             "差勤審核", "請假分析", "異常出勤", "加班申請", "一鍵月結",
             "獎金匯入", "結算歷史", "薪資參數設定"]
for n in nav_items:
    test(S, f"Nav: {n}", n in routes_ts)

# =============================================================
S = "頁面檔案"
print(f"\n[{S}]")
page_files = ["DashboardPage", "AnalysisPage", "AnomalyPage", "LeavesPage",
              "AttendancePage", "DepartmentsPage", "EmployeesPage", "ShiftsPage",
              "OvertimePage", "SettlementPage", "BonusImportPage", "HistoryPage",
              "PayrollSettingsPage", "NotFoundPage"]
for pf in page_files:
    path = f"src/pages/{pf}.tsx"
    content = active_files.get(path, "")
    test(S, f"{pf}.tsx", len(content) > 100, f"{len(content)} chars")

# =============================================================
S = "元件檔案"
print(f"\n[{S}]")
comp_files = ["AppLayout", "AppHeader", "AppSidebar", "LeaveDetailModal",
              "ConfirmDialog", "FormCard", "ApprovalWidget"]
for cf in comp_files:
    path = f"src/components/{cf}.tsx"
    content = active_files.get(path, "")
    test(S, cf, len(content) > 50)

# =============================================================
S = "已清除檔案"
print(f"\n[{S}]")
cleaned = ["src/pages/ListPage.tsx", "src/pages/BonusRulesPage.tsx",
           "src/pages/PayslipsPage.tsx", "src/components/DataTable.tsx",
           "src/components/PayslipDetail.tsx", "src/data.json",
           "src/utils/dbHelper.ts", "actions/summarize_leads.py",
           "actions/manage_leaves.py", "actions/confirm_payroll_run.py"]
for f in cleaned:
    content = vfs.get(f, None)
    is_gone = content is None or content.strip() == ""
    test(S, f"{f.split('/')[-1]} 已清除", is_gone)

# =============================================================
S = "Action 定義"
print(f"\n[{S}]")
action_files = ["ai_hr_insights", "fetch_dashboard", "run_monthly_payroll",
                "clock_in_out", "import_bonus_data", "cancel_payroll_run"]
for af in action_files:
    path = f"actions/{af}.py"
    content = active_files.get(path, "")
    test(S, f"Action: {af}", len(content) > 50, f"{len(content)} chars")

# =============================================================
S = "Data References"
print(f"\n[{S}]")
refs = api("GET", f"/refs/apps/{APP}", None, token)
ref_names = [r["table_name"] for r in refs] if isinstance(refs, list) else []
expected_refs = ["hr_employees", "hr_leaves", "hr_leave_types", "hr_attendances",
                 "hr_departments", "hr_shifts", "hr_overtime_requests",
                 "hr_payroll_bonus_rules", "hr_payroll_contracts",
                 "hr_payroll_runs", "hr_payroll_slips"]
for er in expected_refs:
    test(S, f"Ref: {er}", er in ref_names)

removed_refs = ["hr_payroll_bonus_rule_results", "hr_payroll_settings",
                "hr_payroll_slip_lines", "crm_tags", "sale_orders"]
for rr in removed_refs:
    test(S, f"已移除: {rr}", rr not in ref_names)

# =============================================================
S = "Custom Tables"
print(f"\n[{S}]")
all_tables = api("GET", "/data/objects", None, token) or []
our_slugs = [t["api_slug"] for t in all_tables if t.get("app_id") == APP]
test(S, "payroll_settings 存在", "payroll_settings" in our_slugs)
test(S, "payroll_brackets 存在", "payroll_brackets" in our_slugs)
test(S, "bonus_records 存在", "bonus_records" in our_slugs)
test(S, "bonus_records_8e0a2d 已移除", "bonus_records_8e0a2d" not in our_slugs)
test(S, "payroll_records 已移除", "payroll_records" not in our_slugs)

for slug_name in ["payroll_settings", "payroll_brackets", "bonus_records"]:
    r = api("GET", f"/data/objects/{slug_name}/records?limit=1", None, token)
    test(S, f"{slug_name} 可讀取", isinstance(r, list))

# =============================================================
S = "AI Action — skip_ai=true（快速）"
print(f"\n[{S}]")
for action in ["dashboard", "analysis", "anomaly"]:
    t0 = time.time()
    r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
            {"params": {"action": action, "skip_ai": True}}, token)
    ms = (time.time() - t0) * 1000
    result = (r or {}).get("result") or {}
    ai_map = {"dashboard": "ai_insight", "analysis": "ai_prediction", "anomaly": "ai_analysis"}
    ai_text = result.get(ai_map[action], "")
    test(S, f"{action} 成功", r and r.get("status") == "success", f"{ms:.0f}ms")
    test(S, f"{action} 無 AI 文字", ai_text == "")
    if action == "dashboard":
        kpi = result.get("kpi", {})
        test(S, "Dashboard KPI 完整", all(k in kpi for k in ["total_employees","pending_count","leave_rate"]))
        test(S, "Dashboard 出勤網格", len(result.get("attendance_grid", [])) > 0)
        test(S, "Dashboard 待簽核", isinstance(result.get("pending_list"), list))
        test(S, "Dashboard 假別分布", isinstance(result.get("type_distribution"), dict))
    elif action == "analysis":
        test(S, "Analysis 趨勢 6 個月", len(result.get("trend", [])) == 6)
        test(S, "Analysis 假別分布", isinstance(result.get("type_distribution"), dict))
        test(S, "Analysis 一週分布", len(result.get("weekday_distribution", [])) == 5)
    elif action == "anomaly":
        kpi = result.get("kpi", {})
        test(S, "Anomaly KPI 風險分級", all(k in kpi for k in ["high","medium","normal","total"]))
        test(S, "Anomaly 異常清單", isinstance(result.get("anomalies"), list))

# =============================================================
S = "AI Action — skip_ai=false（含 AI）"
print(f"\n[{S}]")
for action in ["dashboard", "analysis", "anomaly"]:
    t0 = time.time()
    r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
            {"params": {"action": action, "skip_ai": False}}, token)
    ms = (time.time() - t0) * 1000
    result = (r or {}).get("result") or {}
    ai_map = {"dashboard": "ai_insight", "analysis": "ai_prediction", "anomaly": "ai_analysis"}
    ai_text = result.get(ai_map[action], "")
    test(S, f"{action} 有 AI 文字", len(ai_text) > 10, f"{ms:.0f}ms, {len(ai_text)} chars")
    # 驗證無 emoji
    has_emoji = any(0x1F300 <= ord(c) <= 0x1FAFF or ord(c) in (0x2705,0x274C,0x26A0,0xFE0F,0x2728,0x2B50) for c in ai_text)
    test(S, f"{action} AI 無 emoji", not has_emoji)
    test(S, f"{action} AI 條列格式", ai_text.strip().startswith("-"))

# =============================================================
S = "其他 Action"
print(f"\n[{S}]")
# fetch_dashboard
r = api("POST", f"/actions/apps/{APP}/run/fetch_dashboard", {"params": {}}, token)
test(S, "fetch_dashboard 成功", r and r.get("status") == "success")

# run_monthly_payroll
r = api("POST", f"/actions/apps/{APP}/run/run_monthly_payroll",
        {"params": {"period": "2026-05"}}, token)
test(S, "run_monthly_payroll 成功", r and r.get("status") == "success")

# clock_in_out
r = api("POST", f"/actions/apps/{APP}/run/clock_in_out", {"params": {}}, token)
test(S, "clock_in_out 可執行", r and r.get("status") in ("success", "error"))

# import_bonus_data
r = api("POST", f"/actions/apps/{APP}/run/import_bonus_data",
        {"params": {"period": "2026-05"}}, token)
test(S, "import_bonus_data 可執行", r and r.get("status") in ("success", "error"))

# =============================================================
S = "前端編碼模式"
print(f"\n[{S}]")
# Dashboard
dash = active_files.get("src/pages/DashboardPage.tsx", "")
test(S, "Dashboard 用 runAction", "runAction" in dash)
test(S, "Dashboard import ../action", "../action" in dash)
test(S, "Dashboard 有 KPI 元件", "KPI" in dash)
test(S, "Dashboard 有出勤網格", "attendance_grid" in dash)
test(S, "Dashboard 有待簽核", "pending_list" in dash)
test(S, "Dashboard AI 按鈕觸發", "fetchAI" in dash and "skip_ai: true" in dash)
test(S, "Dashboard 有 Loader2 動畫", "Loader2" in dash and "animate-spin" in dash)

# Analysis
an = active_files.get("src/pages/AnalysisPage.tsx", "")
test(S, "Analysis 用 runAction", "runAction" in an)
test(S, "Analysis 有 SVG 圖表", "<svg" in an or "SVG" in an or "<rect" in an)
test(S, "Analysis AI 按鈕觸發", "fetchAI" in an and "skip_ai: true" in an)

# Anomaly
am = active_files.get("src/pages/AnomalyPage.tsx", "")
test(S, "Anomaly 用 runAction", "runAction" in am)
test(S, "Anomaly 有風險分級", "risk" in am)
test(S, "Anomaly AI 按鈕觸發", "fetchAI" in am and "skip_ai: true" in am)

# Modal
modal = active_files.get("src/components/LeaveDetailModal.tsx", "")
test(S, "Modal 有核准按鈕", "validate" in modal)
test(S, "Modal 有拒絕按鈕", "refuse" in modal)
test(S, "Modal 用 PATCH proxy", "PATCH" in modal or "update" in modal)

# Leaves
lv = active_files.get("src/pages/LeavesPage.tsx", "")
test(S, "Leaves 有批次核准", "batch" in lv.lower() or "selectedIds" in lv)
test(S, "Leaves import LeaveDetailModal", "LeaveDetailModal" in lv)

# Attendance
att = active_files.get("src/pages/AttendancePage.tsx", "")
test(S, "Attendance 有網格", "grid" in att.lower() or "table" in att.lower())
test(S, "Attendance 有篩選", "search" in att.lower() or "filter" in att.lower())

# =============================================================
S = "Import 引用正確性"
print(f"\n[{S}]")
import_ok = True
for path in sorted(active_files):
    if not path.endswith((".tsx", ".ts")) or path.startswith("actions/"):
        continue
    content = active_files[path]
    for m in re.finditer(r'from\s+"(\.[^"]+)"', content):
        mod = m.group(1)
        parts = path.split("/")
        if mod.startswith("../"):
            base = "/".join(parts[:-2]); rest = mod[3:]
        elif mod.startswith("./"):
            base = "/".join(parts[:-1]); rest = mod[2:]
        else:
            continue
        candidates = [f"{base}/{rest}.tsx", f"{base}/{rest}.ts",
                      f"{base}/{rest}/index.tsx", f"{base}/{rest}/index.ts",
                      f"{base}/{rest}"]
        found = any(c in active_files for c in candidates)
        if not found:
            test(S, f"{path.split('/')[-1]} → {mod}", False, "not found")
            import_ok = False
if import_ok:
    test(S, "所有 import 引用正確", True)

# =============================================================
S = "CSS 規範"
print(f"\n[{S}]")
css = active_files.get("src/App.css", "")
test(S, "CSS 有 :host", ":host" in css)
test(S, f"CSS 大小合理", len(css) < 120000, f"{len(css):,} chars")
# 驗證關鍵 className 都在 CSS 中
key_classes = ["page-title", "page-sub", "page-head", "panel", "panel-head",
               "panel-title", "kpi-grid", "btn", "badge", "form-input",
               "dialog-title", "dialog-close", "animate-spin", "app-layout",
               "app-sidebar", "app-header", "app-content"]
for cls in key_classes:
    test(S, f".{cls} 在 CSS 中", f".{cls}" in css)

# 無 emoji
S2 = "前端無 emoji"
print(f"\n[{S2}]")
emoji_count = 0
for path in sorted(active_files):
    if not path.endswith((".tsx", ".ts")) or path.startswith("actions/"):
        continue
    for ch in active_files[path]:
        cp = ord(ch)
        if 0x1F300 <= cp <= 0x1FAFF or cp in (0x2705,0x274C,0x26A0,0xFE0F,0x2713,0x2715,0x2728,0x2B50):
            emoji_count += 1
test(S2, "TSX/TS 無 emoji", emoji_count == 0, f"found {emoji_count}" if emoji_count else "clean")

# =============================================================
S = "編譯驗證"
print(f"\n[{S}]")
r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
test(S, "編譯成功", r and r.get("success") == True)

# =============================================================
print(f"\n{'='*60}")
print(f"  測試結果：{passed} passed, {failed} failed, {passed+failed} total")
print(f"  Pass rate: {passed/(passed+failed)*100:.1f}%")
print(f"{'='*60}")
print(f"\n  各區塊:")
for sec, (p, f) in sections.items():
    icon = "\u2705" if f == 0 else "\u274c"
    print(f"    {icon} {sec}: {p}/{p+f}")
