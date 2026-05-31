# -*- coding: utf-8 -*-
"""
檢查所有前端頁面和後端 Action 中的 mockup data
"""
import json, urllib.request, ssl
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"

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
pvfs = app_data.get("published_vfs", {})

# 搜尋所有檔案中的 mock/硬編碼資料關鍵字
MOCK_KEYWORDS = [
    "mock", "Mock", "MOCK",
    "fake", "Fake",
    "dummy", "Dummy",
    "hardcode", "hard-code",
    "sample", "Sample",
    "demo_data", "demoData",
    "test_data", "testData",
    "模擬", "假資料", "測試資料",
    "Math.random",
    "// TODO",
    "placeholder",
]

# 硬編碼資料模式：直接在 TSX 中定義的陣列/物件
HARDCODE_PATTERNS = [
    "const STAFF",
    "const staff",
    "const CUSTOMERS",
    "const customers",
    "const DATA",
    "const data =",
    "const MOCK",
    "useState([{",
    'company: "',
    'name: "張',
    'name: "王',
    'name: "李',
    'name: "陳',
    'name: "林',
    "散點圖",
    "scatter",
    "SCATTER",
]

print("=" * 70)
print("MOCKUP DATA 完整掃描")
print("=" * 70)

for filepath in sorted(pvfs.keys()):
    content = pvfs[filepath]
    if not content or len(content) < 10:
        continue
    
    findings = []
    lines = content.split("\n")
    
    for keyword in MOCK_KEYWORDS + HARDCODE_PATTERNS:
        for i, line in enumerate(lines, 1):
            if keyword in line:
                findings.append((i, keyword, line.strip()[:120]))
    
    if findings:
        print(f"\n--- {filepath} ({len(content)} chars) ---")
        seen = set()
        for lineno, kw, preview in findings:
            key = (lineno, kw)
            if key not in seen:
                seen.add(key)
                print(f"  L{lineno} [{kw}]: {preview}")

# 特別深入檢查 SalesPage（業務分析頁）
print("\n\n" + "=" * 70)
print("SalesPage.tsx 完整內容（業務人員風險地圖）")
print("=" * 70)
sales = pvfs.get("src/pages/SalesPage.tsx", "")
for i, line in enumerate(sales.split("\n"), 1):
    print(f"{i:3d}: {line}")

# 也輸出 Action
print("\n\n" + "=" * 70)
print("analyze_churn.py 完整內容（後端 Action）")
print("=" * 70)
action = pvfs.get("actions/analyze_churn.py", "")
for i, line in enumerate(action.split("\n"), 1):
    print(f"{i:3d}: {line}")
