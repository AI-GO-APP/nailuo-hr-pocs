# -*- coding: utf-8 -*-
"""
AI GO Custom App 標準部署腳本範本

使用方式：
1. 修改 FILES_TO_UPLOAD 中要更新的檔案
2. python deploy_template.py

流程：
1. 登入取得 token
2. PATCH /source/files 上傳修改的檔案
3. POST /publish 同步 vfs_state → published_vfs（published_assets 保持為空）
4. GET 驗證 published_vfs 已更新
5. (可選) POST /compile 驗證無編譯錯誤
"""
import json, urllib.request, ssl, time
ssl._create_default_https_context = ssl._create_unverified_context

BASE = "https://ai-go.app/api/v1"
APP_ID = "YOUR_APP_ID"           # ← 替換為你的 App ID
SLUG = "YOUR_APP_SLUG"           # ← 替換為你的 App Slug

# ========== 要上傳的檔案 ==========
FILES_TO_UPLOAD = {
    # "src/App.css": css_content,
    # "src/pages/DashboardPage.tsx": tsx_content,
}

# ========== 驗證條件（用來確認部署成功） ==========
VERIFY_CHECKS = {
    # "src/App.css": ":host, :root",         # 檔案中必須包含的關鍵字串
    # "src/pages/DashboardPage.tsx": "DonutChart",
}


def api(method, path, data=None, token=None):
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(f"{BASE}{path}", data=body, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}


def main():
    # 1. 登入
    print("1. 登入...")
    auth = api("POST", "/auth/login", {
        "email": "admin@tslg.com.tw",
        "password": "password123"
    })
    token = auth["access_token"]
    print("   OK")

    # 2. 上傳檔案
    print(f"\n2. 上傳 {len(FILES_TO_UPLOAD)} 個檔案...")
    for path in sorted(FILES_TO_UPLOAD):
        print(f"   - {path} ({len(FILES_TO_UPLOAD[path])} chars)")

    r = api("PATCH", f"/builder/apps/{APP_ID}/source/files",
            {"files": FILES_TO_UPLOAD}, token)
    assert r and "_error" not in r, f"上傳失敗: {r}"
    print("   OK")

    # 3. Publish（published_assets 保持為空 — 平台從 VFS 即時編譯）
    print("\n3. Publish (sync vfs_state → published_vfs)...")
    r = api("POST", f"/builder/apps/{APP_ID}/publish", {
        "published_assets": {"html": "", "bundle_js": "", "css": ""}
    }, token)
    assert r and "_error" not in r, f"Publish 失敗: {r}"
    print("   OK")

    # 4. GET 驗證
    print("\n4. 驗證 published_vfs...")
    time.sleep(1)
    app = api("GET", f"/builder/apps/{APP_ID}", None, token)
    pvfs = app.get("published_vfs", {})
    pa = app.get("published_assets", {})

    # 確認 published_assets 為空
    for k in ["html", "bundle_js", "css"]:
        size = len(pa.get(k, ""))
        status = "OK (empty)" if size == 0 else f"WARNING: {size} bytes"
        print(f"   published_assets.{k}: {status}")

    # 確認檔案內容
    all_ok = True
    for path, keyword in VERIFY_CHECKS.items():
        content = pvfs.get(path, "")
        found = keyword in content
        print(f"   {path} contains '{keyword}': {'OK' if found else 'FAIL'}")
        if not found:
            all_ok = False

    # 5. (可選) Compile 驗證
    print("\n5. Compile 驗證...")
    c = api("POST", f"/compile/compile/{SLUG}", None, token)
    success = c.get("success", False)
    errors = c.get("compile_errors", [])
    print(f"   success={success}, errors={len(errors)}")
    for e in errors:
        print(f"   ERROR: {json.dumps(e, ensure_ascii=False)[:200]}")

    # 結果
    print("\n" + "=" * 50)
    if all_ok and success:
        print("✅ 部署成功！請 Ctrl+Shift+R 重整瀏覽器確認。")
    else:
        print("❌ 部署有問題，請檢查上方輸出。")


if __name__ == "__main__":
    main()
