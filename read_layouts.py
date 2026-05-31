# -*- coding: utf-8 -*-
"""讀取成功 app 的 AppLayout.tsx 完整內容"""
import json, urllib.request, ssl
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
GOOD_APP = "da7789b4-59bc-422c-8e7b-b6a7b9103146"
OUR_APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"

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

good = api("GET", f"/builder/apps/{GOOD_APP}", None, token)
pvfs = good.get("published_vfs", {})

# 完整 AppLayout
layout = pvfs.get("src/components/AppLayout.tsx", "")
print("=== 成功 App: AppLayout.tsx ===")
for i, line in enumerate(layout.split("\n"), 1):
    print("%3d: %s" % (i, line))

# 完整 AppSidebar
print("\n\n=== 成功 App: AppSidebar.tsx ===")
sidebar = pvfs.get("src/components/AppSidebar.tsx", "")
for i, line in enumerate(sidebar.split("\n"), 1):
    print("%3d: %s" % (i, line))

# 我們的 AppLayout
print("\n\n=== 我們的 AppLayout.tsx ===")
our = api("GET", f"/builder/apps/{OUR_APP}", None, token)
our_layout = our.get("published_vfs", {}).get("src/components/AppLayout.tsx", "")
for i, line in enumerate(our_layout.split("\n"), 1):
    print("%3d: %s" % (i, line))

# types.ts
print("\n\n=== 成功 App: types.ts ===")
types = pvfs.get("src/types.ts", "")
for i, line in enumerate(types.split("\n"), 1):
    print("%3d: %s" % (i, line))
