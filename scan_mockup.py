# -*- coding: utf-8 -*-
"""掃描 VFS 所有檔案中的 mockup / hardcoded / dummy data"""
import json, urllib.request, ssl, re
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

# Mock data 特徵關鍵字
MOCK_PATTERNS = [
    # 假資料陣列
    (r'\[\s*\{[^]]*(?:name|title|label)[^]]*\}(?:\s*,\s*\{[^]]*\}){2,}\s*\]', "hardcoded 陣列（可能是 mock data）"),
    # hardcoded UUID
    (r'["\'][\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}["\']', "hardcoded UUID"),
    # 假名字
    (r'(?:王小明|李小華|張三|李四|陳大|mock|dummy|fake|sample|example|placeholder|lorem|ipsum)', "疑似假資料名稱"),
    # hardcoded 員工/用戶資料
    (r'(?:employee_id|user_id)\s*[:=]\s*["\'][^"\']{5,}["\']', "hardcoded employee/user ID"),
]

# 需要排除的檔案（SDK / config）
SKIP_FILES = {"src/api.ts", "src/db.ts", "src/action.ts", "src/data.json", "src/db.json", "package.json", "_template_meta.json"}

print(f"掃描 {len(vfs)} 個檔案...\n")
total_issues = 0

for path in sorted(vfs):
    if path in SKIP_FILES:
        continue
    content = vfs[path]
    lines = content.split("\n")
    findings = []

    # 1. 搜尋 hardcoded 陣列（看起來像假資料列表）
    # 特徵：在 const/let/var 後面直接定義包含多筆物件的陣列
    for i, line in enumerate(lines):
        stripped = line.strip()

        # hardcoded UUID（排除 TYPE_ID_MAP 中的合法用途 + constants.ts）
        if re.search(r'[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}', stripped, re.I):
            # 排除：TYPE_ID_MAP, constants, import, comment
            if path == "src/constants.ts" or "TYPE_ID_MAP" in stripped or "// " in stripped[:5]:
                continue
            # 排除：動態取得的值（來自變數）
            if any(x in stripped for x in ["result", "res.", "data.", "get(", "params", "payload", ".id"]):
                continue
            findings.append((i+1, "hardcoded UUID", stripped[:120]))

        # 假中文名字
        for fake_name in ["王小明", "李小華", "張三", "李四", "陳大文", "測試員工", "測試用戶"]:
            if fake_name in stripped:
                findings.append((i+1, f"假名字 '{fake_name}'", stripped[:120]))

        # mock/dummy/fake/sample 關鍵字
        for kw in ["mock", "dummy", "fake", "sample_data", "placeholder", "lorem", "ipsum"]:
            if kw.lower() in stripped.lower() and "//" not in stripped[:stripped.lower().find(kw)]:
                findings.append((i+1, f"關鍵字 '{kw}'", stripped[:120]))

        # hardcoded 日期陣列（可能是假資料）
        if re.search(r'(?:const|let|var)\s+\w+\s*=\s*\[', stripped):
            # 看後面幾行是否有大量假物件
            block = "\n".join(lines[i:min(i+20, len(lines))])
            obj_count = block.count("{")
            if obj_count >= 4 and ("name" in block or "label" in block or "title" in block):
                findings.append((i+1, f"疑似 mock data 陣列 (含 {obj_count} 個物件)", stripped[:120]))

        # QUICK_CHIPS 或類似 hardcoded 示範文字（這些是 UX，不算 mock）
        # 但其他的 const 陣列要檢查

        # hardcoded 員工資料（非動態取得）
        if "衛佳穗" in stripped and "currentUser" not in stripped and "employee" not in stripped.lower():
            findings.append((i+1, "hardcoded 員工名字 '衛佳穗'", stripped[:120]))

        # hardcoded 假請假紀錄
        if re.search(r'(?:leaves|records)\s*[:=]\s*\[', stripped, re.I):
            block = "\n".join(lines[i:min(i+30, len(lines))])
            if block.count("{") >= 3 and ("date_from" in block or "leave_type" in block or "status" in block):
                findings.append((i+1, "疑似 hardcoded 請假紀錄陣列", stripped[:120]))

        # 假統計數字
        if re.search(r'(?:total|count|remaining|used)\s*[:=]\s*\d{1,3}(?:\s*[,}])', stripped, re.I):
            if "const" in stripped or "let" in stripped:
                findings.append((i+1, "疑似 hardcoded 統計數字", stripped[:120]))

    if findings:
        total_issues += len(findings)
        print(f"❌ {path} ({len(findings)} 處)")
        for line_no, issue_type, snippet in findings:
            print(f"   L{line_no} [{issue_type}]")
            print(f"      {snippet}")
        print()

if total_issues == 0:
    print("✅ 未發現 mockup data！")
else:
    print(f"\n共 {total_issues} 處疑似 mockup data")

# === 特別檢查：各頁面是否有 hardcoded 資料而非從 API 取得 ===
print("\n" + "=" * 70)
print("各頁面資料來源分析")
print("=" * 70)

pages = {p: vfs[p] for p in vfs if p.startswith("src/pages/") and p.endswith(".tsx")}
for page_path, content in sorted(pages.items()):
    page_name = page_path.split("/")[-1].replace(".tsx", "")
    has_api_call = any(x in content for x in ["listRecords", "query(", "queryAdvanced", "callAction", "runAction", "fetch(", "proxyInsert"])
    has_useEffect = "useEffect" in content
    has_static_array = bool(re.search(r'(?:const|let)\s+\w+\s*[:=]\s*\[[\s\S]{50,}?\]', content))
    
    # 檢查是否有大段 hardcoded JSX 資料
    hardcoded_items = len(re.findall(r'<(?:tr|li|div)[^>]*>\s*(?:<td|<span)[^>]*>[^<]{5,}', content))
    
    status = "✅" if has_api_call else "⚠️"
    print(f"  {status} {page_name}")
    print(f"     API 呼叫: {has_api_call} | useEffect: {has_useEffect} | 靜態陣列: {has_static_array} | 重複 JSX 項: {hardcoded_items}")
