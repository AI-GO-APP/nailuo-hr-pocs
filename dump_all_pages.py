# -*- coding: utf-8 -*-
"""只輸出 SalesPage.tsx — 檢查散點圖是否使用 mockup data"""
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

sales = pvfs.get("src/pages/SalesPage.tsx", "")
print("SalesPage.tsx (%d chars)" % len(sales))
print("=" * 70)
for i, line in enumerate(sales.split("\n"), 1):
    print(f"{i:3d}: {line}")

print("\n\n" + "=" * 70)
print("DashboardPage.tsx (%d chars)" % len(pvfs.get("src/pages/DashboardPage.tsx", "")))
print("=" * 70)
dash = pvfs.get("src/pages/DashboardPage.tsx", "")
for i, line in enumerate(dash.split("\n"), 1):
    print(f"{i:3d}: {line}")

print("\n\n" + "=" * 70)
print("CategoriesPage.tsx (%d chars)" % len(pvfs.get("src/pages/CategoriesPage.tsx", "")))
print("=" * 70)
cat = pvfs.get("src/pages/CategoriesPage.tsx", "")
for i, line in enumerate(cat.split("\n"), 1):
    print(f"{i:3d}: {line}")

print("\n\n" + "=" * 70)
print("DataSourcePage.tsx (%d chars)" % len(pvfs.get("src/pages/DataSourcePage.tsx", "")))
print("=" * 70)
ds = pvfs.get("src/pages/DataSourcePage.tsx", "")
for i, line in enumerate(ds.split("\n"), 1):
    print(f"{i:3d}: {line}")
