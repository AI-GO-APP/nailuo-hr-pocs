# -*- coding: utf-8 -*-
"""修正 LeavesPage + AttendancePage 的 JS 模板字串問題，重新編譯"""
import json, urllib.request, ssl, sys
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
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:500]
        print(f"  HTTP {e.code}: {err}")
        return None

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]
version = app_data["vfs_version"]
slug = app_data["slug"]
print(f"v{version}, {len(vfs)} files")

# Read LeavesPage to understand current structure
leaves_page = vfs.get("src/pages/LeavesPage.tsx", "")
print(f"\nLeavesPage: {len(leaves_page)} chars, {len(leaves_page.split(chr(10)))} lines")

# Show first 10 lines
for i, line in enumerate(leaves_page.split("\n")[:15]):
    print(f"  L{i+1}: {line[:120]}")

# Show line around 128
lines = leaves_page.split("\n")
for i in range(max(0,125), min(len(lines), 135)):
    print(f"  L{i+1}: {lines[i][:120]}")

# The problem is the template literal backticks are escaped wrong
# Let me rebuild LeavesPage from scratch based on the original version

# Show full original LeavesPage before our changes
print("\n=== Original LeavesPage (first file content in VFS) ===")
# Find batchApprove pattern
for i, line in enumerate(lines):
    s = line.strip()
    if "batch" in s.lower() or "selectedIds" in s.lower() or "detailLeave" in s.lower() or "LeaveDetailModal" in s.lower():
        print(f"  L{i+1}: {s[:120]}")
