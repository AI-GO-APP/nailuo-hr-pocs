# -*- coding: utf-8 -*-
"""移除所有前端 TSX/TS 中的 emoji，替換為文字或圖示"""
import json, urllib.request, ssl, re, sys
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:300]}")
        return None

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]
version = app_data["vfs_version"]
slug = app_data["slug"]
print(f"v{version}")

fixes = {}

# ===================================================================
# 1. DashboardPage.tsx — 7 emoji
# ===================================================================
dash = vfs["src/pages/DashboardPage.tsx"]
# KPI icons: replace emoji strings with text-based icons
dash = dash.replace('icon="\U0001F465"', 'icon="出"')        # 👥 → 出
dash = dash.replace('icon="\u26A0\uFE0F"', 'icon="!"')       # ⚠️ → !
dash = dash.replace('icon="\U0001F4C5"', 'icon="月"')        # 📅 → 月
# But actually the KPI component uses icon as text inside a div.
# Better approach: replace the emoji icon prop with a simple character
# Let's replace the emoji in icon prop and in body text

# Actually let's look at how the KPI icon is used
# <div ...>{icon}</div> — it renders the icon string directly
# Better to use a simple symbol or letter

dash = dash.replace('\U0001F465', '')     # 👥
dash = dash.replace('\u26A0\uFE0F', '')   # ⚠️
dash = dash.replace('\U0001F4C5', '')     # 📅
dash = dash.replace('\U0001F916', '')     # 🤖
dash = dash.replace('\U0001F389', '')     # 🎉

# Fix icon props that are now empty — set meaningful text
dash = dash.replace('icon=""', 'icon="i"')  # fallback

# Actually, let me re-approach: replace emoji with appropriate text
# Re-read original and do targeted replacements
dash = vfs["src/pages/DashboardPage.tsx"]

# KPI icon props
dash = dash.replace('<KPI icon="\U0001F465"', '<KPI icon="A"')
dash = dash.replace('icon="\u23F3"', 'icon="P"')              # ⏳
dash = dash.replace('<KPI icon="\U0001F4C5"', '<KPI icon="C"')
dash = dash.replace('<KPI icon="\u26A0\uFE0F"', '<KPI icon="!"')

# Body text emoji
dash = dash.replace('\U0001F916 AI', 'AI')
dash = dash.replace('\U0001F389', '')
dash = dash.replace('\u23F3 ', '')         # ⏳
dash = dash.replace('\U0001F4C5 ', '')     # 📅
dash = dash.replace('\U0001F4C5', '')

# Check for any remaining emoji
remaining = []
for ch in dash:
    cp = ord(ch)
    if 0x1F300 <= cp <= 0x1FAFF or cp in (0x2705, 0x274C, 0x26A0, 0xFE0F, 0x2713, 0x2715, 0x2728):
        remaining.append(f"U+{cp:04X}")
if remaining:
    print(f"  Dashboard remaining: {set(remaining)}")

fixes["src/pages/DashboardPage.tsx"] = dash
print("  DashboardPage: fixed")

# ===================================================================
# 2. AnalysisPage.tsx — 4 emoji
# ===================================================================
analysis = vfs["src/pages/AnalysisPage.tsx"]
analysis = analysis.replace('\U0001F4CA ', '')     # 📊
analysis = analysis.replace('\U0001F4C5 ', '')     # 📅
analysis = analysis.replace('\U0001F4C8 ', '')     # 📈
analysis = analysis.replace('\U0001F916 AI', 'AI') # 🤖 AI
fixes["src/pages/AnalysisPage.tsx"] = analysis
print("  AnalysisPage: fixed")

# ===================================================================
# 3. AnomalyPage.tsx — 9 emoji
# ===================================================================
anomaly = vfs["src/pages/AnomalyPage.tsx"]
# Risk labels
anomaly = anomaly.replace('\U0001F534 ', '')       # 🔴
anomaly = anomaly.replace('\U0001F7E1 ', '')       # 🟡
anomaly = anomaly.replace('\U0001F7E2 ', '')       # 🟢
# Title
anomaly = anomaly.replace('\u26A0\uFE0F ', '')     # ⚠️
anomaly = anomaly.replace('\u26A0\uFE0F', '')
# KPI icons
anomaly = anomaly.replace('\U0001F6A8', '')         # 🚨
anomaly = anomaly.replace('\u2705', '')             # ✅
anomaly = anomaly.replace('\U0001F389 ', '')        # 🎉
anomaly = anomaly.replace('\U0001F389', '')
anomaly = anomaly.replace('\U0001F534', '')         # 🔴
anomaly = anomaly.replace('\U0001F916 AI', 'AI')   # 🤖 AI
fixes["src/pages/AnomalyPage.tsx"] = anomaly
print("  AnomalyPage: fixed")

# ===================================================================
# 4. AttendancePage.tsx — 1 emoji
# ===================================================================
att = vfs["src/pages/AttendancePage.tsx"]
att = att.replace('\U0001F4C5 ', '')               # 📅
fixes["src/pages/AttendancePage.tsx"] = att
print("  AttendancePage: fixed")

# ===================================================================
# 5. LeaveDetailModal.tsx — 3 emoji (✕ and ✓)
# ===================================================================
modal = vfs["src/components/LeaveDetailModal.tsx"]
modal = modal.replace('\u2715 ', 'x ')              # ✕ →  x
modal = modal.replace('\u2715', 'x')
modal = modal.replace('\u2713 ', '')                 # ✓ → remove prefix
fixes["src/components/LeaveDetailModal.tsx"] = modal
print("  LeaveDetailModal: fixed")

# ===================================================================
# 6. PayslipDetail.tsx — 1 emoji (✕)
# ===================================================================
payslip = vfs["src/components/PayslipDetail.tsx"]
payslip = payslip.replace('\u2715', 'x')
fixes["src/components/PayslipDetail.tsx"] = payslip
print("  PayslipDetail: fixed")

# ===================================================================
# 7. ListPage.tsx — 2 emoji
# ===================================================================
listpage = vfs["src/pages/ListPage.tsx"]
listpage = listpage.replace('\U0001F4CA ', '')       # 📊
listpage = listpage.replace('\U0001F4CB', '')        # 📋
fixes["src/pages/ListPage.tsx"] = listpage
print("  ListPage: fixed")

# ===================================================================
# Final verification — scan all fixed files for remaining emoji
# ===================================================================
print("\n--- 修正後驗證 ---")
found_any = False
for path, content in fixes.items():
    remaining = []
    for i, line in enumerate(content.split("\n")):
        for ch in line:
            cp = ord(ch)
            if (0x1F300 <= cp <= 0x1FAFF) or \
               (cp in (0x2705, 0x274C, 0x26A0, 0xFE0F, 0x2713, 0x2715, 0x2728,
                       0x2714, 0x2716, 0x23F3, 0x231A, 0x231B)):
                remaining.append((i + 1, ch, f"U+{cp:04X}", line.strip()[:80]))
                found_any = True
    if remaining:
        print(f"\n  {path} still has emoji:")
        for lineno, ch, cp_str, ctx in remaining:
            print(f"    L{lineno}: {ch} ({cp_str}) → {ctx}")

if not found_any:
    print("  All emoji removed successfully!")

# ===================================================================
# PATCH
# ===================================================================
print(f"\nPATCH {len(fixes)} files (v{version})...")
r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": fixes, "expected_version": version}, token)
if r is None:
    app2 = api("GET", f"/builder/apps/{APP}", None, token)
    version = app2["vfs_version"]
    r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": fixes, "expected_version": version}, token)
    if r is None:
        print("PATCH FAILED")
        sys.exit(1)
print("  OK")

# Compile
print("Compile...")
r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
if r and r.get("success"):
    print("  OK")
else:
    err = (r or {}).get("error", "")
    print(f"  FAILED: {err[:400]}")
    # Try auto-fix
    if err:
        app3 = api("GET", f"/builder/apps/{APP}", None, token)
        vfs3 = app3["vfs_state"]
        v3 = app3["vfs_version"]
        # Show error context
        import re as _re
        error_files = _re.findall(r'(src/\S+\.tsx):(\d+):(\d+)', err)
        for ef, eline, ecol in error_files[:5]:
            content = vfs3.get(ef, "")
            lines = content.split("\n")
            ln = int(eline) - 1
            if 0 <= ln < len(lines):
                print(f"    {ef}:{eline}: {lines[ln].strip()[:100]}")
    sys.exit(1)

# Publish
print("Publish...")
api("POST", f"/builder/apps/{APP}/publish", {"published_assets": {}}, token)
print("  OK")

print("\nDone!")
