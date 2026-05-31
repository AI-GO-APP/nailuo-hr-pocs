# -*- coding: utf-8 -*-
"""
詳細輸出每個頁面的完整 TSX 內容，確認實際部署狀態
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

# 完整輸出 CategoriesPage
cat = pvfs.get("src/pages/CategoriesPage.tsx", "")
print("=" * 60)
print("CategoriesPage.tsx FULL CONTENT (%d chars)" % len(cat))
print("=" * 60)
for i, line in enumerate(cat.split("\n"), 1):
    print("%3d: %s" % (i, line))

# 完整輸出 AppSidebar
print("\n" + "=" * 60)
sidebar = pvfs.get("src/components/AppSidebar.tsx", "")
print("AppSidebar.tsx FULL CONTENT (%d chars)" % len(sidebar))
print("=" * 60)
for i, line in enumerate(sidebar.split("\n"), 1):
    print("%3d: %s" % (i, line))

# 完整輸出 AppLayout
print("\n" + "=" * 60)
layout = pvfs.get("src/components/AppLayout.tsx", "")
print("AppLayout.tsx FULL CONTENT (%d chars)" % len(layout))
print("=" * 60)
for i, line in enumerate(layout.split("\n"), 1):
    print("%3d: %s" % (i, line))
