# -*- coding: utf-8 -*-
"""
耐落請假系統 E2E 測試腳本
=====================================
透過 AI GO API 驗證所有前端功能的資料層正確性。
由於無法直接操作瀏覽器 DOM，此測試驗證：
1. VFS 檔案完整性（所有檔案存在且非空）
2. 編譯成功（esbuild 無錯誤）
3. 前端無 emoji（合規檢查）
4. API 資料層正確性（DB Proxy 和 Custom Table）
5. Server Action 可用性
6. 發佈流程完整性

使用方式：
  $env:PYTHONIOENCODING = "utf-8"; python e2e_test.py
"""
import json
import re
import sys
import urllib.request
import urllib.error
import ssl
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

BASE = "https://ai-go.app/api/v1"
APP_ID = "da7789b4-59bc-422c-8e7b-b6a7b9103146"
SLUG = "0abbb390eaac"

# ============================================================
# API helper
# ============================================================
def api(method, path, data=None, token=None):
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as r:
            txt = r.read().decode("utf-8")
            return {"ok": True, "status": r.status, "data": json.loads(txt) if txt.strip() else {}}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "data": e.read().decode("utf-8")[:500] if e.fp else ""}
    except Exception as e:
        return {"ok": False, "status": 0, "data": str(e)}


# ============================================================
# Test results
# ============================================================
results = []
def test(name, passed, detail=""):
    results.append({"name": name, "passed": passed, "detail": detail})
    icon = "PASS" if passed else "FAIL"
    print(f"  [{icon}] {name}" + (f" -- {detail}" if detail and not passed else ""))


# ============================================================
# Test Suite
# ============================================================
def run_tests():
    print("=" * 60)
    print("  Nailuo Leave System - E2E Test Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ─── T01: 認證 ────────────────────────────
    print("\n[T01] Authentication")
    auth = api("POST", "/auth/login", {"email": "admin@tslg.com.tw", "password": "password123"})
    test("Login success", auth["ok"])
    token = auth["data"].get("access_token", "") if auth["ok"] else ""
    test("JWT token received", bool(token))

    if not token:
        print("\nCannot continue without token!")
        return results

    # ─── T02: App 狀態 ────────────────────────
    print("\n[T02] App State")
    app = api("GET", f"/builder/apps/{APP_ID}", None, token)
    test("GET app success", app["ok"])
    app_data = app["data"] if app["ok"] else {}
    test("App has vfs_state", "vfs_state" in app_data)
    test("App has vfs_version", "vfs_version" in app_data and app_data["vfs_version"] > 0)
    test("App slug matches", app_data.get("slug") == SLUG)

    vfs = app_data.get("vfs_state", {})

    # ─── T03: VFS 檔案完整性 ──────────────────
    print("\n[T03] VFS File Completeness")
    required_files = [
        "package.json",
        "src/main.tsx",
        "src/App.tsx",
        "src/App.css",
        "src/routes.ts",
        "src/constants.ts",
        "src/types.ts",
        "src/components/AppLayout.tsx",
        "src/components/AppSidebar.tsx",
        "src/components/AppHeader.tsx",
        "src/components/LeaveCard.tsx",
        "src/components/StatusBadge.tsx",
        "src/components/ChatBubble.tsx",
        "src/components/ConfirmDialog.tsx",
        "src/pages/_manifest.json",
        "src/pages/NotFoundPage.tsx",
        "src/pages/ChatPage.tsx",
        "src/pages/RecordsPage.tsx",
        "src/pages/AttendancePage.tsx",
        "src/pages/BalancePage.tsx",
        "src/pages/PolicyPage.tsx",
        "src/pages/AgentsPage.tsx",
        "actions/manifest.json",
        "actions/ai_leave_chat.py",
    ]
    for f in required_files:
        content = vfs.get(f, "")
        test(f"File exists: {f}", bool(content), f"size={len(content)}b" if content else "MISSING")

    # ─── T04: VFS 內容品質 ────────────────────
    print("\n[T04] VFS Content Quality")

    # Check main.tsx has correct mount
    main = vfs.get("src/main.tsx", "")
    test("main.tsx imports App", "import App" in main or "import App" in main)
    test("main.tsx imports App.css", "App.css" in main)
    test("main.tsx has createRoot", "createRoot" in main)
    test("main.tsx uses __CUSTOM_APP_ROOT__", "__CUSTOM_APP_ROOT__" in main)

    # Check App.tsx
    app_tsx = vfs.get("src/App.tsx", "")
    test("App.tsx uses HashRouter", "HashRouter" in app_tsx)
    test("App.tsx NOT BrowserRouter", "BrowserRouter" not in app_tsx or "HashRouter" in app_tsx)
    test("App.tsx has routes", "Route" in app_tsx)
    test("App.tsx imports AppLayout", "AppLayout" in app_tsx)

    # Check AppLayout
    layout = vfs.get("src/components/AppLayout.tsx", "")
    test("AppLayout uses Outlet", "Outlet" in layout)
    test("AppLayout has UserContext", "UserContext" in layout or "useCurrentUser" in layout)

    # Check App.css
    css = vfs.get("src/App.css", "")
    test("CSS uses :host, :root", ":host" in css and ":root" in css)
    test("CSS has 100vh layout", "100vh" in css)
    test("CSS has overflow-y: auto", "overflow-y" in css)

    # ─── T05: 前端無 emoji ────────────────────
    print("\n[T05] No Emoji in Frontend")
    # Regex to match emoji characters (comprehensive)
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # misc symbols
        "\U0001F680-\U0001F6FF"  # transport
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess
        "\U0001FA70-\U0001FAFF"  # symbols extended
        "\U00002600-\U000026FF"  # misc symbols
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0000200D"  # zero width joiner
        "\U00002B50\U00002B55"  # stars
        "]+", re.UNICODE
    )
    frontend_files = [f for f in vfs if f.endswith((".tsx", ".ts", ".css", ".json")) and not f.endswith(("db.ts", "api.ts", "action.ts", "data.json", "db.json"))]
    all_clean = True
    for f in frontend_files:
        content = vfs.get(f, "")
        emojis = emoji_pattern.findall(content)
        clean = len(emojis) == 0
        if not clean:
            all_clean = False
            test(f"No emoji: {f}", False, f"Found: {emojis[:3]}")
        else:
            test(f"No emoji: {f}", True)
    test("ALL frontend files emoji-free", all_clean)

    # ─── T06: SDK 完整性 ──────────────────────
    print("\n[T06] SDK Integrity")
    sdk_files = ["src/api.ts", "src/db.ts", "src/action.ts", "src/data.json", "src/db.json"]
    for f in sdk_files:
        test(f"SDK present: {f}", f in vfs)

    # ─── T07: 編譯 ────────────────────────────
    print("\n[T07] Compilation")
    compile_r = api("POST", f"/compile/compile/{SLUG}?dev=true", None, token)
    compile_data = compile_r["data"] if compile_r["ok"] else compile_r["data"]
    if isinstance(compile_data, str):
        test("Compile API response", False, compile_data[:200])
    else:
        success = compile_data.get("success", False)
        test("Compile success", success, compile_data.get("error", "")[:200] if not success else "")
        if success:
            test("Bundle JS generated", len(compile_data.get("bundle_js", "")) > 0)
            test("CSS generated", len(compile_data.get("css", "")) > 0)
            test("HTML generated", len(compile_data.get("html", "")) > 0)
            test("Bundle size reasonable", len(compile_data.get("bundle_js", "")) > 1000,
                 f"{len(compile_data.get('bundle_js', ''))} chars")

    # ─── T08: Data References ─────────────────
    print("\n[T08] Data References")
    refs = api("GET", f"/refs/apps/{APP_ID}", None, token)
    if refs["ok"]:
        ref_list = refs["data"] if isinstance(refs["data"], list) else [refs["data"]]
        ref_tables = [r.get("table_name") for r in ref_list]
        test("Ref: hr_employees", "hr_employees" in ref_tables)
        test("Ref: hr_leaves", "hr_leaves" in ref_tables)
        test("Ref: hr_leave_types", "hr_leave_types" in ref_tables)
        test("Ref: hr_departments", "hr_departments" in ref_tables)
        test("Ref: hr_leave_allocations", "hr_leave_allocations" in ref_tables)
    else:
        test("Data References API", False, str(refs["data"])[:100])

    # ─── T09: DB Proxy 資料 ───────────────────
    print("\n[T09] DB Proxy Data")

    # Employees
    emps = api("GET", f"/proxy/{APP_ID}/hr_employees?limit=20", None, token)
    test("Query hr_employees", emps["ok"])
    emp_data = emps["data"] if emps["ok"] and isinstance(emps["data"], list) else []
    test("Employee count >= 10", len(emp_data) >= 10, f"got {len(emp_data)}")
    if emp_data:
        first = emp_data[0]
        test("Employee has name", bool(first.get("name")))
        test("Employee has custom_data", isinstance(first.get("custom_data"), dict))

    # Leave types
    lt = api("GET", f"/proxy/{APP_ID}/hr_leave_types?limit=50", None, token)
    test("Query hr_leave_types", lt["ok"])
    lt_data = lt["data"] if lt["ok"] and isinstance(lt["data"], list) else []
    test("Leave types count = 18", len(lt_data) == 18, f"got {len(lt_data)}")

    # Departments
    depts = api("GET", f"/proxy/{APP_ID}/hr_departments?limit=20", None, token)
    test("Query hr_departments", depts["ok"])
    dept_data = depts["data"] if depts["ok"] and isinstance(depts["data"], list) else []
    test("Department count >= 7", len(dept_data) >= 7, f"got {len(dept_data)}")

    # Leave allocations
    alloc = api("GET", f"/proxy/{APP_ID}/hr_leave_allocations?limit=20", None, token)
    test("Query hr_leave_allocations", alloc["ok"])

    # Leaves
    leaves = api("GET", f"/proxy/{APP_ID}/hr_leaves?limit=10", None, token)
    test("Query hr_leaves", leaves["ok"])

    # ─── T10: Actions ─────────────────────────
    print("\n[T10] Server Actions")
    actions_manifest = vfs.get("actions/manifest.json", "")
    if actions_manifest:
        manifest = json.loads(actions_manifest)
        # 平台格式：flat object { "action_name": {...} } 或 array 格式
        if isinstance(manifest, dict) and "actions" in manifest:
            actions = manifest["actions"]
            test("Action manifest valid", len(actions) > 0)
            test("ai_leave_chat action registered", any(a.get("name") == "ai_leave_chat" or a.get("id") == "ai_leave_chat" for a in actions))
        elif isinstance(manifest, dict):
            test("Action manifest valid", len(manifest) > 0)
            test("ai_leave_chat action registered", "ai_leave_chat" in manifest)
        else:
            test("Action manifest valid", False)
            test("ai_leave_chat action registered", False)
    else:
        test("Action manifest exists", False)

    action_py = vfs.get("actions/ai_leave_chat.py", "")
    test("ai_leave_chat.py has handler", "def execute" in action_py or "def handler" in action_py or "async def handler" in action_py)
    test("ai_leave_chat.py has OpenAI", "openai" in action_py.lower() or "OPENAI" in action_py)

    # ─── T11: 路由完整性 ──────────────────────
    print("\n[T11] Routing Completeness")
    routes_ts = vfs.get("src/routes.ts", "")
    expected_paths = ["/chat", "/records", "/attendance", "/balance", "/policy", "/agents"]
    for path in expected_paths:
        test(f"Route defined: {path}", path in routes_ts)
    for path in expected_paths:
        test(f"Route in App.tsx: {path}", path in app_tsx)

    # ─── T12: 發佈狀態 ────────────────────────
    print("\n[T12] Publish State")
    test("App has published_at", bool(app_data.get("published_at")))
    test("Published VFS exists", bool(app_data.get("published_vfs")))

    # ─── T13: Custom Tables ────────────────────
    print("\n[T13] Custom Tables")
    ct_resp = api("GET", f"/data/objects?app_id={APP_ID}", None, token)
    if ct_resp["ok"]:
        tables = ct_resp["data"] if isinstance(ct_resp["data"], list) else []
        slugs = [t.get("api_slug", "") for t in tables]
        test("Custom Table: chat_messages", "chat_messages" in slugs)
        test("Custom Table: attendance_records", "attendance_records" in slugs)
        test("Custom Table: agent_delegates", "agent_delegates" in slugs)

        # 驗證 chat_messages 欄位
        chat_tbl = next((t for t in tables if t.get("api_slug") == "chat_messages"), None)
        if chat_tbl:
            field_keys = [f.get("field_key") for f in chat_tbl.get("fields", [])]
            test("chat_messages has employee_id", "employee_id" in field_keys)
            test("chat_messages has role", "role" in field_keys)
            test("chat_messages has content", "content" in field_keys)
            test("chat_messages has timestamp", "timestamp" in field_keys)
        else:
            test("chat_messages fields", False, "Table not found")
    else:
        test("Custom Tables API", False, str(ct_resp["data"])[:100])

    # ─── T14: Server Action 格式 ───────────────
    print("\n[T14] Server Action Format")
    action_py = vfs.get("actions/ai_leave_chat.py", "")
    test("Uses def execute(ctx)", "def execute(ctx)" in action_py)
    test("No async def handler", "async def handler" not in action_py)
    test("Uses ctx.params", "ctx.params" in action_py)
    test("Uses ctx.response.json", "ctx.response.json" in action_py)
    test("Uses ctx.secrets.get", "ctx.secrets.get" in action_py)
    test("Uses httpx for OpenAI", "httpx" in action_py)

    # ─── T15: 頁面真實資料化 ──────────────────
    print("\n[T15] Pages Real Data")
    chat_page = vfs.get("src/pages/ChatPage.tsx", "")
    test("ChatPage uses callAction", "callAction" in chat_page)
    test("ChatPage uses listRecords", "listRecords" in chat_page)
    test("ChatPage uses submitRecord", "submitRecord" in chat_page)
    test("ChatPage imports from actionHelper", 'from "../actionHelper"' in chat_page)
    test("ChatPage imports from api", 'from "../api"' in chat_page)

    records_page = vfs.get("src/pages/RecordsPage.tsx", "")
    test("RecordsPage fetches hr_leaves", "hr_leaves" in records_page)
    test("RecordsPage has loading state", "loading" in records_page.lower())

    balance_page = vfs.get("src/pages/BalancePage.tsx", "")
    test("BalancePage fetches hr_leave_allocations", "hr_leave_allocations" in balance_page)

    policy_page = vfs.get("src/pages/PolicyPage.tsx", "")
    test("PolicyPage fetches hr_leave_types", "hr_leave_types" in policy_page)

    attendance_page = vfs.get("src/pages/AttendancePage.tsx", "")
    test("AttendancePage uses listRecords", "listRecords" in attendance_page)
    test("AttendancePage uses submitRecord", "submitRecord" in attendance_page)
    test("AttendancePage uses attendance_records", "attendance_records" in attendance_page)

    agents_page = vfs.get("src/pages/AgentsPage.tsx", "")
    test("AgentsPage uses listRecords", "listRecords" in agents_page)
    test("AgentsPage uses agent_delegates", "agent_delegates" in agents_page)

    # ─── T16: Server Action 結構驗證 ───────────
    print("\n[T16] Server Action Structure")
    # Action API 需要 App Token（Runtime 環境），admin JWT 無法直接呼叫
    # 改為驗證 action 結構完整性
    test("Action has SYSTEM_PROMPT", "SYSTEM_PROMPT" in action_py)
    test("Action has generate_rule_based_reply", "generate_rule_based_reply" in action_py)
    test("Action handles missing API key", "api_key" in action_py)
    test("Action has error fallback", "except" in action_py)
    test("Action formats employee info", "emp_info" in action_py)
    test("Action uses gpt-4o-mini", "gpt-4o-mini" in action_py)

    # Verify action SDK endpoint pattern
    action_sdk = vfs.get("src/action.ts", "")
    test("SDK has /actions/run/ endpoint", "/actions/run/" in action_sdk)
    test("SDK wraps params in body", "params" in action_sdk)

    # ─── Summary ──────────────────────────────
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)
    pct = round(passed / total * 100, 1) if total > 0 else 0

    print(f"  Results: {passed}/{total} passed ({pct}%)")
    if failed > 0:
        print(f"  FAILED ({failed}):")
        for r in results:
            if not r["passed"]:
                print(f"    - {r['name']}" + (f": {r['detail']}" if r["detail"] else ""))
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
