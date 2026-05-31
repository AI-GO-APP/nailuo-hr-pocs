# -*- coding: utf-8 -*-
"""驗證 AI 按鈕觸發 + table 調整"""
import json, urllib.request, ssl, time
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
        return {"_error": e.code, "_detail": e.read().decode()[:300]}

passed = 0
failed = 0

def test(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  \u2705 {name}{' \u2014 ' + detail if detail else ''}")
    else:
        failed += 1
        print(f"  \u274c {name}{' \u2014 ' + detail if detail else ''}")

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]
slug = app_data["slug"]

print("=" * 60)
print("  驗證 AI 按鈕觸發 + Table 調整")
print("=" * 60)

# 1. Test skip_ai=true (快速，不呼叫 AI)
print("\n[1] skip_ai=true 測試（應快速、無 AI 文字）")
for action in ["dashboard", "analysis", "anomaly"]:
    t0 = time.time()
    r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
            {"params": {"action": action, "skip_ai": True}}, token)
    t1 = time.time()
    ms = (t1-t0)*1000
    result = (r or {}).get("result") or {}
    ai_fields = {"dashboard": "ai_insight", "analysis": "ai_prediction", "anomaly": "ai_analysis"}
    ai_text = result.get(ai_fields[action], "")
    test(f"{action} skip_ai=true 無 AI 文字", ai_text == "", f"{ms:.0f}ms, ai='{ai_text[:30]}'")
    # Verify data still exists
    if action == "dashboard":
        test(f"{action} 仍有 KPI", "kpi" in result)
        test(f"{action} 仍有 pending_list", "pending_list" in result)
    elif action == "analysis":
        test(f"{action} 仍有 trend", "trend" in result)
    elif action == "anomaly":
        test(f"{action} 仍有 anomalies", "anomalies" in result)

# 2. Test skip_ai=false (正常呼叫 AI)
print("\n[2] skip_ai=false 測試（應有 AI 文字）")
for action in ["dashboard", "analysis", "anomaly"]:
    t0 = time.time()
    r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
            {"params": {"action": action, "skip_ai": False}}, token)
    t1 = time.time()
    ms = (t1-t0)*1000
    result = (r or {}).get("result") or {}
    ai_fields = {"dashboard": "ai_insight", "analysis": "ai_prediction", "anomaly": "ai_analysis"}
    ai_text = result.get(ai_fields[action], "")
    has_ai = len(ai_text) > 10
    test(f"{action} skip_ai=false 有 AI 文字", has_ai, f"{ms:.0f}ms, {len(ai_text)} chars")

# 3. 前端有按鈕
print("\n[3] 前端按鈕驗證")
for page_name, btn_text in [
    ("DashboardPage", "產生 AI 洞察"),
    ("AnalysisPage", "產生 AI 預測"),
    ("AnomalyPage", "產生 AI 分析"),
]:
    page = vfs.get(f"src/pages/{page_name}.tsx", "")
    test(f"{page_name} 有按鈕", btn_text in page)
    test(f"{page_name} 有 aiLoading state", "aiLoading" in page)
    test(f"{page_name} 有 fetchAI 函式", "fetchAI" in page)
    test(f"{page_name} 有等待動畫 (Loader2)", "Loader2" in page and "animate-spin" in page)
    test(f"{page_name} 用 skip_ai: true 載入", "skip_ai: true" in page)

# 4. Table 使用驗證
print("\n[4] Table 使用")
# payroll_settings/payroll_brackets → custom table (proxy 只有 read 權限)
psp = vfs.get("src/pages/PayrollSettingsPage.tsx", "")
test("PayrollSettings 用 custom table (需讀寫)", 'listRecords("payroll_settings")' in psp)

# bonus_records → custom table (紀錄匯入歷史)
bp = vfs.get("src/pages/BonusImportPage.tsx", "")
test("BonusImport 用 custom table (匯入紀錄)", 'submitRecord("bonus_records"' in bp)

# payrollCalc 寫入 proxy table
calc = vfs.get("src/utils/payrollCalc.ts", "")
test("payrollCalc 寫入 hr_payroll_runs (proxy)", 'insert("hr_payroll_runs"' in calc)
test("payrollCalc 寫入 hr_payroll_slips (proxy)", 'insert("hr_payroll_slips"' in calc)

# 5. 編譯
print("\n[5] 編譯")
r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
test("編譯成功", r and r.get("success") == True)

print(f"\n{'='*60}")
print(f"  結果：{passed} passed, {failed} failed")
print(f"{'='*60}")
