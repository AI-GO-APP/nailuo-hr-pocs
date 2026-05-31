# -*- coding: utf-8 -*-
"""確認 3 個失敗項的根因並修正"""
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

# 1. AI Action 回傳結構分析
print("=== AI Action 回傳結構 ===")
params = {"message": "我想請明天特休一天", "employee": {"id": "040c9d2a-279f-42f0-8ec8-19c29eb3185c", "name": "衛佳穗"}, "history": []}
req = urllib.request.Request(
    f"{BASE}/actions/apps/{APP}/run/ai_leave_chat",
    json.dumps(params).encode(), method="POST",
    headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"}
)
r = json.loads(urllib.request.urlopen(req, timeout=30).read())

# 列出所有 key
print("Top-level keys:", list(r.keys()))
result = r.get("result", {})
print("result keys:", list(result.keys()) if isinstance(result, dict) else type(result))
reply = result.get("reply", "") if isinstance(result, dict) else ""
card = result.get("action_card") if isinstance(result, dict) else None
print("reply:", repr(reply[:120]))
print("action_card:", card is not None)
if card:
    print("  title:", card.get("title", "?"))
    for a in card.get("actions", []):
        pl = a.get("payload", {})
        print("  action:", a.get("action"), "hsid:", pl.get("holiday_status_id", "?"))

# 2. hr_attendance reference
print("\n=== hr_attendance Reference ===")
refs = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/refs/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())
for ref in refs:
    t = ref.get("table_name", "")
    if "attend" in t:
        print("  table:", t, "cols:", ref.get("columns", []))
        print("  ref_id:", ref["id"])

# 3. 確認前端 ChatPage 的 result 解構是否正確
app_data = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/builder/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())
vfs = app_data["vfs_state"]

# 看 actionHelper.ts 回傳什麼
helper = vfs.get("src/actionHelper.ts", "")
print("\n=== actionHelper.ts ===")
for i, line in enumerate(helper.split("\n")):
    if "return" in line or "result" in line or "data" in line or "json" in line:
        print(f"  L{i+1}: {line.rstrip()[:100]}")

# 看 ChatPage 怎麼解構
chat = vfs.get("src/pages/ChatPage.tsx", "")
for i, line in enumerate(chat.split("\n")):
    if "callAction" in line or "data" in line and ("reply" in line or "action_card" in line):
        print(f"  ChatPage L{i+1}: {line.rstrip()[:120]}")
