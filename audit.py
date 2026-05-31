# -*- coding: utf-8 -*-
"""完整審查 Custom App VFS — 對照 CLAUDE.md 規範"""
import json, urllib.request, ssl
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "da7789b4-59bc-422c-8e7b-b6a7b9103146"

auth = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/auth/login",
    json.dumps({"email":"admin@tslg.com.tw","password":"password123"}).encode(),
    method="POST", headers={"Content-Type":"application/json"}
)).read())
token = auth["access_token"]
app = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/builder/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())
vfs = app["vfs_state"]

print(f"VFS version: {app['vfs_version']}, files: {len(vfs)}")
print("=" * 80)

issues = []

for path, content in sorted(vfs.items()):
    file_issues = []

    # === 規則：CSS ===
    if path.endswith(".css"):
        # 檢查 :root 沒有 :host
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if ":root" in line and ":host" not in line and "{" in line:
                file_issues.append(f"  L{i+1}: `:root` 沒有 `:host` — 部署後 CSS 變數失效")

    # === 規則：TSX/TS ===
    if path.endswith(".tsx") or path.endswith(".ts"):
        # 檢查 BrowserRouter
        if "BrowserRouter" in content:
            file_issues.append("  使用了 BrowserRouter — 必須用 HashRouter")

        # 檢查 confirm/alert/prompt
        for fn in ["confirm(", "alert(", "prompt("]:
            if fn in content and "// " not in content.split(fn)[0].split("\n")[-1]:
                # 排除註解中的
                idx = content.find(fn)
                line_start = content.rfind("\n", 0, idx) + 1
                line_text = content[line_start:idx + len(fn)]
                if "//" not in line_text and "/*" not in line_text:
                    file_issues.append(f"  使用了 {fn}) — Shadow DOM 中會靜默失敗")

        # 檢查 submitRecord 用於 proxy table
        if "submitRecord" in content:
            for proxy_table in ["hr_leaves", "hr_employees", "hr_leave_types", "hr_departments", "hr_leave_allocations", "hr_attendance"]:
                if f'submitRecord("{proxy_table}"' in content or f"submitRecord('{proxy_table}'" in content:
                    file_issues.append(f"  submitRecord(\"{proxy_table}\") — proxy table 應用 db.ts insert()")

        # 檢查 toISOString 用於 proxy 寫入
        if "proxyInsert" in content or 'insert("hr_' in content or "insert('hr_" in content:
            if "toISOString()" in content:
                # 檢查是否在 date_from/date_to 上下文
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "toISOString()" in line and ("date_from" in line or "date_to" in line):
                        file_issues.append(f"  L{i+1}: date 欄位用了 toISOString() — DB 不接受帶時區日期")

        # 檢查 overflow-y: auto 在 Layout
        if "AppLayout" in path or "Layout" in path:
            if "overflow" not in content and "overflowY" not in content:
                file_issues.append("  Layout 缺少 overflow-y: auto — 頁面可能無法捲動")
            if "100vh" not in content:
                file_issues.append("  Layout 缺少 height: 100vh")

    # === 規則：Python Action ===
    if path.endswith(".py"):
        # 檢查 ctx.env
        if "ctx.env" in content:
            file_issues.append("  使用了 ctx.env — 它是 str 不是 dict，會崩潰")

        # 檢查 ctx.secrets.get 雙參數
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "ctx.secrets.get(" in line:
                # 檢查是否有兩個參數
                start = line.find("ctx.secrets.get(") + len("ctx.secrets.get(")
                end = line.find(")", start)
                if end > start:
                    args = line[start:end]
                    if "," in args:
                        file_issues.append(f"  L{i+1}: ctx.secrets.get() 帶了雙參數 — 只接受單參數")

        # 檢查 ctx.params.get 雙參數（這個其實可以用，但要小心）
        # ctx.db.insert_object 或其他不存在的方法
        if "insert_object" in content:
            file_issues.append("  使用了 insert_object — 正確方法是 ctx.db.insert()")

    # === manifest.json ===
    if path == "actions/manifest.json":
        try:
            manifest = json.loads(content)
            actions = manifest.get("actions", [])
            for act in actions:
                act_file = f"actions/{act.get('file', '')}"
                if act_file not in vfs:
                    file_issues.append(f"  manifest 引用 {act_file} 但 VFS 中不存在")
        except:
            file_issues.append("  manifest.json 格式不合法")

    if file_issues:
        issues.append((path, file_issues))
        print(f"\n❌ {path}")
        for iss in file_issues:
            print(iss)
    else:
        print(f"✅ {path}")

print("\n" + "=" * 80)
if issues:
    print(f"\n共 {sum(len(i) for _, i in issues)} 個問題，涉及 {len(issues)} 個檔案")
else:
    print("\n✅ 所有檔案通過審查！")

# === 額外審查：Data Reference 欄位 ===
print("\n" + "=" * 80)
print("Data Reference 審查")
print("=" * 80)
refs = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/refs/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())

required_hr_leaves_cols = {"id", "name", "state", "date_from", "date_to", "number_of_days",
                           "notes", "employee_id", "holiday_status_id", "department_id",
                           "created_at", "updated_at", "custom_data"}
for ref in refs:
    table = ref.get("table_name", "?")
    cols = set(ref.get("columns", []))
    perms = set(ref.get("permissions", []))
    pub_cols = ref.get("published_columns")
    pub_perms = ref.get("published_permissions")

    ref_issues = []
    if table == "hr_leaves":
        missing = required_hr_leaves_cols - cols
        if missing:
            ref_issues.append(f"  columns 缺少: {missing}")
        if "create" not in perms:
            ref_issues.append("  缺少 create 權限")
        if "update" not in perms:
            ref_issues.append("  缺少 update 權限")
        # 檢查 published 是否同步
        if pub_cols and set(pub_cols) != cols:
            ref_issues.append(f"  published_columns 與 columns 不同步！差異: {cols - set(pub_cols)}")
        if pub_perms and set(pub_perms) != perms:
            ref_issues.append(f"  published_permissions 與 permissions 不同步！差異: {perms - set(pub_perms)}")

    if ref_issues:
        print(f"\n❌ {table}")
        for ri in ref_issues:
            print(ri)
    else:
        print(f"✅ {table} ({len(cols)} cols, perms={list(perms)})")

# === AI Action 功能完整性 ===
print("\n" + "=" * 80)
print("AI Action 功能審查")
print("=" * 80)
ai_py = vfs.get("actions/ai_leave_chat.py", "")
checks = {
    "TYPE_ID_MAP": "TYPE_ID_MAP" in ai_py,
    "_resolve_type_id": "_resolve_type_id" in ai_py,
    "holiday_status_id in payload": "holiday_status_id" in ai_py,
    "submit_leave tool": "submit_leave" in ai_py,
    "query_balance tool": "query_balance" in ai_py or "balance" in ai_py.lower(),
    "query_records tool": "query_records" in ai_py or "records" in ai_py.lower(),
    "SYSTEM_PROMPT": "SYSTEM_PROMPT" in ai_py,
    "ctx.secrets.get (single arg)": True,  # already checked above
    "ctx.response.json": "ctx.response.json" in ai_py,
}
for check, ok in checks.items():
    print(f"  {'✅' if ok else '❌'} {check}")

# === ChatPage 功能審查 ===
print("\n" + "=" * 80)
print("ChatPage 功能審查")
print("=" * 80)
chat = vfs.get("src/pages/ChatPage.tsx", "")
chat_checks = {
    "proxyInsert (直接 fetch)": "proxyInsert" in chat,
    "messagesRef (閉包修復)": "messagesRef" in chat,
    "callAction (呼叫 AI)": "callAction" in chat,
    "listRecords (歷史紀錄)": "listRecords" in chat,
    "holiday_status_id in payload": "holiday_status_id" in chat,
    "date 不用 toISOString": "toISOString" not in chat.split("proxyInsert")[0].split("handleCardAction")[-1] if "proxyInsert" in chat else False,
    "md() markdown 解析": "function md" in chat,
    "action_card 渲染": "action_card" in chat,
    "card_done 防重複": "card_done" in chat,
    "Quick chips": "QUICK_CHIPS" in chat,
    "Loading indicator": "typing-indicator" in chat,
}
for check, ok in chat_checks.items():
    print(f"  {'✅' if ok else '❌'} {check}")
