# -*- coding: utf-8 -*-
"""診斷側邊欄樣式問題"""
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
vfs = app_data.get("vfs_state", {})

print("=" * 60)
print("AppLayout.tsx")
print("=" * 60)
print(vfs.get("src/components/AppLayout.tsx", ""))

print("\n" + "=" * 60)
print("AppSidebar.tsx")
print("=" * 60)
print(vfs.get("src/components/AppSidebar.tsx", ""))

print("\n" + "=" * 60)
print("AppHeader.tsx")
print("=" * 60)
print(vfs.get("src/components/AppHeader.tsx", ""))

print("\n" + "=" * 60)
print("CSS sidebar-related classes")
print("=" * 60)
css = vfs.get("src/App.css", "")
in_sidebar = False
for line in css.split("\n"):
    stripped = line.strip()
    # 找所有含 sidebar, app-layout, header, main-content, mobile 的 CSS
    if any(kw in stripped.lower() for kw in ["sidebar", "app-layout", "app-header", "header", "main-content", "mobile", "layout"]):
        print(f"  {stripped}")
    # 也看看是否有 class 定義
    if stripped.startswith(".sidebar") or stripped.startswith(".app-"):
        in_sidebar = True
    if in_sidebar:
        print(f"  CSS> {stripped}")
        if "}" in stripped:
            in_sidebar = False
