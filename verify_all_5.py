# -*- coding: utf-8 -*-
"""5 個問題的完整驗證測試"""
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
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

passed = 0
failed = 0
results = []

def test(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  \u2705 {name}{' \u2014 ' + detail if detail else ''}")
    else:
        failed += 1
        results.append((name, detail))
        print(f"  \u274c {name}{' \u2014 ' + detail if detail else ''}")

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]
slug = app_data["slug"]

# ==========================================
print("=" * 60)
print("  [1] AI 回傳無 emoji")
print("=" * 60)
for action_name in ["dashboard", "analysis", "anomaly"]:
    r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
            {"params": {"action": action_name}}, token)
    result = (r or {}).get("result", {})
    
    ai_fields = {"dashboard": "ai_insight", "analysis": "ai_prediction", "anomaly": "ai_analysis"}
    ai_text = result.get(ai_fields[action_name], "")
    
    has_emoji = False
    for ch in ai_text:
        cp = ord(ch)
        if 0x1F300 <= cp <= 0x1FAFF or cp in (0x2705, 0x274C, 0x26A0, 0xFE0F, 0x2728, 0x2B50):
            has_emoji = True
            break
    
    test(f"AI {action_name} 無 emoji", not has_emoji, ai_text[:80])
    test(f"AI {action_name} 用條列格式 (- 開頭)", ai_text.strip().startswith("-"),
         ai_text[:50].replace("\n", " "))

# Also verify the prompt in code no longer mentions emoji
ai_code = vfs.get("actions/ai_hr_insights.py", "")
test("Action prompt 無 emoji 要求", "emoji" not in ai_code.lower())

# ==========================================
print("\n" + "=" * 60)
print("  [2] AI 功能列表 (驗證所有 AI 回傳)")
print("=" * 60)

# Dashboard
r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
        {"params": {"action": "dashboard"}}, token)
result = (r or {}).get("result", {})
test("Dashboard AI 洞察有內容", len(result.get("ai_insight", "")) > 10)
test("Dashboard KPI 數據完整", all(k in result.get("kpi", {}) for k in ["total_employees","pending_count","leave_rate"]))

# Analysis
r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
        {"params": {"action": "analysis"}}, token)
result = (r or {}).get("result", {})
test("Analysis AI 預測有內容", len(result.get("ai_prediction", "")) > 10)
test("Analysis 趨勢有 6 個月", len(result.get("trend", [])) == 6)

# Anomaly
r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights",
        {"params": {"action": "anomaly"}}, token)
result = (r or {}).get("result", {})
test("Anomaly AI 分析有內容", len(result.get("ai_analysis", "")) > 0 or len(result.get("anomalies", [])) == 0)
test("Anomaly KPI 有風險分級", all(k in result.get("kpi",{}) for k in ["high","medium","normal"]))

# ==========================================
print("\n" + "=" * 60)
print("  [3] 無 Mockup 數據")
print("=" * 60)

# Check no mock/demo/fake/hardcoded data in frontend
import re
mockup_count = 0
for path in sorted(vfs):
    if not path.endswith((".tsx", ".ts")) or path.startswith("actions/"):
        continue
    content = vfs[path]
    lower = content.lower()
    for kw in ["mock", "fake", "dummy", "hardcode", "test data", "假資料"]:
        if kw in lower:
            mockup_count += 1
            # Find line
            for i, line in enumerate(content.split("\n")):
                if kw in line.lower():
                    print(f"    {path}:L{i+1}: {line.strip()[:100]}")

# "demo" and "模擬" are OK if they're just UI text or comments
for path in sorted(vfs):
    if not path.endswith((".tsx", ".ts")) or path.startswith("actions/"):
        continue
    content = vfs[path]
    for i, line in enumerate(content.split("\n")):
        s = line.strip()
        if "demo" in s.lower() and not s.startswith("//") and not s.startswith("*"):
            # Check if it's a real data usage or just a comment/label
            if "For demo" in s or "demo data" in s.lower():
                print(f"    {path}:L{i+1}: {s[:100]}")
                mockup_count += 1

test("無 mockup/demo 硬編碼數據", mockup_count == 0, f"found {mockup_count}" if mockup_count else "clean")

# data.json is empty
data_json = vfs.get("src/data.json", "")
test("data.json 為空或不含數據", data_json.strip() in ("{}", "[]", ""))

# ==========================================
print("\n" + "=" * 60)
print("  [4] PayrollSettingsPage (#/payroll-settings)")
print("=" * 60)

# Custom tables exist
for table in ["payroll_settings", "payroll_brackets"]:
    r = api("GET", f"/data/objects/{table}/records", None, token)
    test(f"Custom table {table} 存在", isinstance(r, list), f"{len(r)} records")

# Page compiles OK (already verified by compile step)
test("PayrollSettingsPage 存在", "src/pages/PayrollSettingsPage.tsx" in vfs,
     f"{len(vfs.get('src/pages/PayrollSettingsPage.tsx',''))} chars")

# ==========================================
print("\n" + "=" * 60)
print("  [5] Settlement (#/settlement) 一鍵月結")
print("=" * 60)

# Test the action
r = api("POST", f"/actions/apps/{APP}/run/run_monthly_payroll",
        {"params": {"period": "2026-05"}}, token)
test("run_monthly_payroll 成功",
     r and r.get("status") == "success" and not r.get("error"),
     f"employees={r.get('result',{}).get('employee_count','?')}" if r else "")

# Custom tables for payroll
for table in ["payroll_records", "bonus_records"]:
    r = api("GET", f"/data/objects/{table}/records", None, token)
    test(f"Custom table {table} 存在", isinstance(r, list))

# payrollCalc.ts has defensive coding
calc = vfs.get("src/utils/payrollCalc.ts", "")
test("payrollCalc.ts 有防禦性 try/catch", "try {" in calc and "catch" in calc)

# ==========================================
print("\n" + "=" * 60)
print("  [6] 編譯")
print("=" * 60)
r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
test("編譯成功", r and r.get("success") == True)

# ==========================================
print(f"\n{'='*60}")
print(f"  結果：{passed} passed, {failed} failed")
print(f"{'='*60}")

if failed:
    print("\n需修正:")
    for name, detail in results:
        print(f"  - {name}: {detail}")
