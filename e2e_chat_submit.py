# -*- coding: utf-8 -*-
"""完整端到端測試：模擬 AI 對話 → 卡片送出 → proxy 寫入"""
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

print("=" * 60)
print("  E2E Chat → Submit Leave Test")
print("=" * 60)

# Step 1: 模擬前端 callAction("ai_leave_chat")
print("\n[1] callAction('ai_leave_chat', '我想請明天特休一天')")
action_body = {
    "action_name": "ai_leave_chat",
    "params": {
        "message": "我想請明天特休一天",
        "employee": {
            "id": "040c9d2a-279f-42f0-8ec8-19c29eb3185c",
            "name": "衛佳穗",
            "email": "admin@tslg.com.tw"
        },
        "history": []
    }
}
slug = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/builder/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())["slug"]

req = urllib.request.Request(
    f"{BASE}/actions/run/{slug}/ai_leave_chat",
    json.dumps(action_body["params"]).encode(),
    method="POST",
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read().decode())
        data = result.get("data", result)
        print(f"  reply: {str(data.get('reply',''))[:100]}")
        card = data.get("action_card")
        if card:
            print(f"  action_card: {card.get('title','?')}")
            for f in card.get("fields", []):
                print(f"    {f['label']}: {f['value']}")
            for a in card.get("actions", []):
                print(f"    [{a['action']}] {a['label']} payload={json.dumps(a.get('payload',{}), ensure_ascii=False)[:200]}")
            
            # Step 2: 模擬點「送出」
            submit_act = next((a for a in card["actions"] if a["action"] == "submit"), None)
            if submit_act and submit_act.get("payload"):
                pl = submit_act["payload"]
                print(f"\n[2] Simulating submit button click...")
                print(f"  payload: {json.dumps(pl, ensure_ascii=False)[:300]}")
                
                # 檢查 holiday_status_id 是否存在
                hsid = pl.get("holiday_status_id", "")
                if hsid:
                    print(f"  holiday_status_id: {hsid} OK")
                else:
                    print(f"  WARNING: holiday_status_id is EMPTY!")
                
                # Step 3: 模擬 proxyInsert
                leave_data = {
                    "employee_id": pl.get("employee_id", ""),
                    "holiday_status_id": hsid,
                    "date_from": pl.get("date_from", "") + "T09:00:00" if "T" not in pl.get("date_from", "") else pl.get("date_from", ""),
                    "date_to": pl.get("date_to", "") + "T18:00:00" if "T" not in pl.get("date_to", "") else pl.get("date_to", ""),
                    "number_of_days": pl.get("number_of_days", 1),
                    "notes": pl.get("reason", ""),
                    "state": "draft",
                }
                print(f"\n[3] proxyInsert('hr_leaves', ...)")
                print(f"  data: {json.dumps(leave_data, ensure_ascii=False)}")
                
                req2 = urllib.request.Request(
                    f"{BASE}/proxy/{APP}/hr_leaves",
                    json.dumps({"data": leave_data}).encode(),
                    method="POST",
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
                )
                try:
                    with urllib.request.urlopen(req2, timeout=15) as r2:
                        result2 = json.loads(r2.read().decode())
                        rid = result2.get("id", "?")
                        print(f"  RESULT: SUCCESS! leave_id={rid}")
                except urllib.error.HTTPError as e:
                    err = e.read().decode()[:300]
                    print(f"  RESULT: FAIL! HTTP {e.code}: {err}")
            else:
                print("\n  No submit action in card")
        else:
            print("  No action_card (text-only reply)")
except urllib.error.HTTPError as e:
    err = e.read().decode()[:500]
    print(f"  FAIL: HTTP {e.code}: {err}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)
