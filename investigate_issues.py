# -*- coding: utf-8 -*-
"""調查 4 個問題"""
import json, urllib.request, ssl, re
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

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]

# =============================================================
# 問題 1: AI 回傳文字中的 emoji
# =============================================================
print("=" * 60)
print("  [1] AI 回傳文字中的 emoji")
print("=" * 60)

# 檢查 ai_hr_insights.py 中的 prompt — 它要求 AI "每行以 emoji 開頭"
ai_action = vfs.get("actions/ai_hr_insights.py", "")
for i, line in enumerate(ai_action.split("\n")):
    if "emoji" in line.lower() or "開頭" in line:
        print(f"  L{i+1}: {line.strip()}")

# =============================================================
# 問題 2: 列出所有 AI 功能
# =============================================================
print("\n" + "=" * 60)
print("  [2] 所有 AI 功能")
print("=" * 60)

# 掃描 action 檔案中所有 AI 呼叫
for path in sorted(vfs):
    if not path.startswith("actions/") or not path.endswith(".py"):
        continue
    content = vfs[path]
    if "openai" in content.lower() or "httpx" in content.lower() or "_call_ai" in content:
        print(f"\n  {path}:")
        for i, line in enumerate(content.split("\n")):
            if "_call_ai" in line or "api.openai" in line or "def _" in line or "def execute" in line:
                print(f"    L{i+1}: {line.strip()[:100]}")

# 掃描前端哪些頁面呼叫 action
print("\n  前端 AI 觸發點:")
for path in sorted(vfs):
    if not path.endswith(".tsx"):
        continue
    content = vfs[path]
    if "ai_hr_insights" in content or "runAction" in content:
        for i, line in enumerate(content.split("\n")):
            if "runAction" in line and "ai_hr_insights" in line:
                print(f"    {path.split('/')[-1]}:L{i+1}: {line.strip()[:100]}")

# =============================================================
# 問題 3: Mockup 數據
# =============================================================
print("\n" + "=" * 60)
print("  [3] Mockup 數據掃描")
print("=" * 60)

# 搜索所有 TSX/TS 中的硬編碼數據
mockup_keywords = ["mock", "demo", "sample", "fake", "hardcode", "dummy",
                   "test data", "範例", "模擬", "假資料"]
for path in sorted(vfs):
    if not path.endswith((".tsx", ".ts")):
        continue
    content = vfs[path].lower()
    for kw in mockup_keywords:
        if kw in content:
            print(f"  {path}: contains '{kw}'")

# 搜索硬編碼的數字陣列或物件（可能是 mockup）
print("\n  硬編碼數據檢查:")
for path in sorted(vfs):
    if not path.endswith((".tsx", ".ts")):
        continue
    content = vfs[path]
    lines = content.split("\n")
    for i, line in enumerate(lines):
        s = line.strip()
        # 找 const xxx = [ 或 const xxx = { 的硬編碼數據
        if re.match(r'const \w+ = \[.*\{', s) and len(s) > 80:
            print(f"  {path}:L{i+1}: {s[:100]}")
        # 找 data.json import
        if "data.json" in s:
            print(f"  {path}:L{i+1}: {s[:100]}")

# 檢查 data.json
if "src/data.json" in vfs:
    dj = vfs["src/data.json"]
    print(f"\n  src/data.json ({len(dj)} chars):")
    print(f"    {dj[:300]}")

# 檢查 AI action 中是否有硬編碼回傳
print("\n  AI Action 硬編碼回傳檢查:")
for i, line in enumerate(ai_action.split("\n")):
    s = line.strip()
    if "return" in s and ("{" in s or "[" in s) and len(s) > 40:
        # skip ctx.response.json
        if "ctx.response.json" not in s:
            print(f"    L{i+1}: {s[:120]}")

# =============================================================
# 問題 4: PayrollSettingsPage 白頁
# =============================================================
print("\n" + "=" * 60)
print("  [4] PayrollSettingsPage 分析")
print("=" * 60)

psp = vfs.get("src/pages/PayrollSettingsPage.tsx", "")
print(f"  檔案大小: {len(psp)} chars, {len(psp.split(chr(10)))} lines")

# 顯示 import 和 API 呼叫
for i, line in enumerate(psp.split("\n")):
    s = line.strip()
    if s.startswith("import ") or "listRecords" in s or "submitRecord" in s or \
       "runAction" in s or "fetch(" in s or "useState" in s or "useEffect" in s or \
       "error" in s.lower() or "catch" in s.lower() or "throw" in s:
        print(f"  L{i+1}: {s[:120]}")

# 檢查 PayrollSettings 所用的 custom table
print("\n  PayrollSettings 使用的 table:")
for i, line in enumerate(psp.split("\n")):
    if "listRecords" in line or "submitRecord" in line:
        # extract table name
        m = re.search(r'(?:listRecords|submitRecord)\("([^"]+)"', line)
        if m:
            print(f"    {m.group(1)} (L{i+1})")

# 檢查這些 custom table 是否存在 (需要用 api.ts，就是 custom table)
print("\n  VFS 中的 api.ts:")
api_ts = vfs.get("src/api.ts", "")
for i, line in enumerate(api_ts.split("\n")[:30]):
    print(f"    L{i+1}: {line[:120]}")

# 同時看 PayrollSettingsPage 完整的 useEffect
print("\n  PayrollSettingsPage useEffect 區塊:")
in_effect = False
for i, line in enumerate(psp.split("\n")):
    if "useEffect" in line:
        in_effect = True
    if in_effect:
        print(f"    L{i+1}: {line[:120]}")
        if line.strip() == "}, []);" or line.strip() == "});":
            in_effect = False
            print()
