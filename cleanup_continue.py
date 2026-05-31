# -*- coding: utf-8 -*-
"""Step 3~6: 刪除 refs + 編譯 + 發布 + 驗證"""
import json, urllib.request, ssl, sys
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "da7789b4-59bc-422c-8e7b-b6a7b9103146"

auth = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/auth/login",
    json.dumps({"email":"admin@tslg.com.tw","password":"password123"}).encode(),
    method="POST", headers={"Content-Type":"application/json"}
)).read())
token = auth["access_token"]

# Step 3: 刪除 refs
print("[Step 3] 刪除未使用的 Data Reference")
refs_to_delete = ["hr_leave_requests", "contacts", "res_partner", "crm_tags"]
refs = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/refs/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())

for ref in refs:
    table = ref.get("table_name", "")
    ref_id = ref.get("id", "")
    if table in refs_to_delete:
        print(f"  DELETE {table} ({ref_id[:8]})...", end="")
        req = urllib.request.Request(
            f"{BASE}/refs/{ref_id}",
            method="DELETE",
            headers={"Authorization": f"Bearer {token}"}
        )
        try:
            with urllib.request.urlopen(req) as r:
                r.read()  # 不解析 JSON
            print(" OK")
        except urllib.error.HTTPError as e:
            print(f" {e.code}: {e.read().decode()[:100]}")

# 驗證
refs2 = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/refs/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())
print(f"  剩餘引用: {[r.get('table_name') for r in refs2]}")

# Step 4: 編譯
app_data = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/builder/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())
slug = app_data["slug"]
vfs_count = len(app_data["vfs_state"])
version = app_data["vfs_version"]
print(f"\n[Step 4] 編譯 (VFS {vfs_count} 檔, v{version})")

compile_req = urllib.request.Request(
    f"{BASE}/compile/compile/{slug}?dev=true",
    method="POST",
    headers={"Authorization": f"Bearer {token}"}
)
with urllib.request.urlopen(compile_req) as r:
    result = json.loads(r.read().decode())
    if result.get("success"):
        print("  OK")
    else:
        print(f"  FAILED: {result.get('error','')[:500]}")
        sys.exit(1)

# Step 5: 發布
print("\n[Step 5] 發布")
pub_req = urllib.request.Request(
    f"{BASE}/builder/apps/{APP}/publish",
    json.dumps({"published_assets": {}}).encode(),
    method="POST",
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
)
with urllib.request.urlopen(pub_req) as r:
    r.read()
print("  OK")

# Step 6: E2E
print("\n[Step 6] E2E 驗證")

# 6a: proxy POST
print("  [6a] proxy POST hr_leaves...")
leave = {
    "employee_id": "040c9d2a-279f-42f0-8ec8-19c29eb3185c",
    "holiday_status_id": "560f4c32-91d5-4a35-8699-a1b8a58aab2a",
    "date_from": "2026-09-01T09:00:00",
    "date_to": "2026-09-01T18:00:00",
    "number_of_days": 1,
    "notes": "cleanup-e2e",
    "state": "draft",
}
req = urllib.request.Request(
    f"{BASE}/proxy/{APP}/hr_leaves",
    json.dumps({"data": leave}).encode(), method="POST",
    headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"}
)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        res = json.loads(r.read().decode())
        print(f"    SUCCESS! id={res.get('id','?')}")
except urllib.error.HTTPError as e:
    print(f"    FAIL: {e.code} {e.read().decode()[:200]}")

# 6b: Action
print("  [6b] AI action...")
params = json.dumps({"message": "你好", "employee": {"id": "040c9d2a", "name": "test"}, "history": []}).encode()
req = urllib.request.Request(
    f"{BASE}/actions/apps/{APP}/run/ai_leave_chat",
    params, method="POST",
    headers={"Content-Type":"application/json","Authorization":f"Bearer {token}"}
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.loads(r.read().decode())
        data = res.get("data", res)
        reply = str(data.get("reply", ""))[:80]
        print(f"    reply: {reply if reply else '(empty)'}")
except urllib.error.HTTPError as e:
    print(f"    {e.code}: {e.read().decode()[:200]}")

# 6c: 最終狀態
app_final = json.loads(urllib.request.urlopen(urllib.request.Request(
    f"{BASE}/builder/apps/{APP}",
    headers={"Authorization": f"Bearer {token}"}
)).read())
final_count = len(app_final["vfs_state"])
print(f"\n  最終: {final_count} 檔案, version={app_final['vfs_version']}")
print(f"  檔案列表:")
for f in sorted(app_final["vfs_state"].keys()):
    print(f"    {f}")

print("\n" + "=" * 70)
print(f"清理完成！36 → {final_count} 檔案 (刪除 {36 - final_count} 個)")
print("=" * 70)
