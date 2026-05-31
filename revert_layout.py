# -*- coding: utf-8 -*-
"""
策略：完全不動 AppLayout，只讓 Sidebar 自己抓 user info
1. 讀取 user group 修改前的 AppLayout（從 deploy_v2.py 或 deploy_full_redesign.py 中取得）
2. Sidebar 用自己的 useEffect 抓 /auth/me
"""
import json, urllib.request, ssl, time, re
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"
SLUG = "da1900f990b0"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:1000]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# 1. 取得成功 app 做參考，找出我們原本可運作的 AppLayout
# 先從 compile 歷史看。其實最可靠的是重新用 deploy_v2.py 裡面的版本
# 但更快的方式是：直接讀成功 app 的結構當參考，重建我們原本的 Layout

# 讀取目前已壞的 layout 結構
app_data = api("GET", f"/builder/apps/{APP}", None, token)
pvfs = app_data.get("published_vfs", {})

# 原本可運作的 AppLayout（deploy_v2.py 中的版本）
# 重點：保持原結構不變
original_layout = r'''import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import AppSidebar from "./AppSidebar";

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const syncMin = Math.floor(Math.random() * 3) + 1;

  return (
    <div className="app-layout">
      <AppSidebar collapsed={collapsed} appName={"\u696d\u52d9\u5206\u6790\u5100\u8868\u677f"} />
      <div className="app-topbar">
        <button className="collapse-btn" onClick={() => setCollapsed(c => !c)}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12h18M3 6h18M3 18h18" /></svg>
        </button>
        <div className="breadcrumb">{"\u5ba2\u6236\u6d41\u5931\u98a8\u96aa\u5206\u6790"}</div>
        <div className="spacer"></div>
        <div className="sync-badge"><div className="sync-dot"></div>{"\u5df2\u540c\u6b65 \u00b7 "}{syncMin}{" \u5206\u9418\u524d"}</div>
      </div>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
'''

# Sidebar：自己用 useEffect 抓 user info，不需要 AppLayout 傳 props
new_sidebar = r'''import React, { useState, useEffect } from "react";
import { routes } from "../routes";
import { useNavigate, useLocation } from "react-router-dom";

interface Props { collapsed?: boolean; appName: string; }

const getApiBase = () => (window as any).__API_BASE__ || "/api/v1";
const getToken = () => (window as any).__APP_TOKEN__ || "";

export default function AppSidebar({ collapsed, appName }: Props) {
  const navigate = useNavigate();
  const location = useLocation();
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    fetch(`${getApiBase()}/auth/me`, { headers, credentials: "include" })
      .then(r => r.ok ? r.json() : null)
      .then(me => {
        if (me) {
          setUserName(me.name || me.display_name || me.email?.split("@")[0] || "\u4f7f\u7528\u8005");
          setUserEmail(me.email || "");
        }
      })
      .catch(() => {});
  }, []);

  const avatar = userName ? userName[0] : "U";

  return (
    <aside className={`app-sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-brand">
        <div className="brand-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l1.9 5.8L19 10.7l-4.1 3 1.6 5.3-4.5-3.3-4.5 3.3 1.6-5.3-4.1-3 5.1-1.9z"/></svg>
        </div>
        <div className="brand-name">{appName}</div>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-group-label">{"\u5ba2\u6236\u6d41\u5931\u98a8\u96aa\u5206\u6790"}</div>
        {routes.map((item, i) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <button key={i} className={`sidebar-item ${isActive ? "active" : ""}`} onClick={() => navigate(item.path)}>
              {Icon && <Icon size={16} />}
              <span>{item.title}</span>
              {i === 0 && <span className="new-tag">NEW</span>}
            </button>
          );
        })}
      </nav>
      <div className="user-card">
        <div className="user-avatar">{avatar}</div>
        <div className="user-info">
          <div className="user-name">{userName || "\u4f7f\u7528\u8005"}</div>
          <div className="user-role">{userEmail}</div>
        </div>
      </div>
    </aside>
  );
}
'''

# 還原 CSS：移除 .app-content-area，還原 .app-main overflow
css = pvfs.get("src/App.css", "")
# 移除之前加的 .app-content-area
css = css.replace("""
/* Content area (右側主內容) */
.app-content-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
""", "")
# 還原 .app-main overflow
css = css.replace("overflow-y: auto; background: var(--bg);", "overflow: hidden; background: var(--bg);")
print("CSS restored")

# Upload
print("\n=== Upload ===")
r = api("PATCH", f"/builder/apps/{APP}/source/files", {
    "files": {
        "src/components/AppLayout.tsx": original_layout,
        "src/components/AppSidebar.tsx": new_sidebar,
        "src/App.css": css,
    }
}, token)
print("Upload:", "OK" if r and "_error" not in r else "FAIL: " + str(r))

# Publish
print("\n=== Publish ===")
r = api("POST", f"/builder/apps/{APP}/publish", {
    "published_assets": {"html": "", "bundle_js": "", "css": ""}
}, token)
print("Publish:", "OK" if r and "_error" not in r else "FAIL")

# Compile
time.sleep(1)
print("\n=== Compile ===")
c = api("POST", f"/compile/compile/{SLUG}", None, token)
print("Success:", c.get("success"))
for e in c.get("compile_errors", []):
    print("  ERROR:", json.dumps(e, ensure_ascii=False)[:200])

# Verify
time.sleep(1)
app2 = api("GET", f"/builder/apps/{APP}", None, token)
pvfs2 = app2.get("published_vfs", {})
lay2 = pvfs2.get("src/components/AppLayout.tsx", "")
sb2 = pvfs2.get("src/components/AppSidebar.tsx", "")
print("\n=== Verify ===")
print("Layout has app-content-area:", "app-content-area" in lay2, "(should be False)")
print("Layout has app-content:", "app-content" in lay2, "(should be False)")
print("Layout has Outlet:", "Outlet" in lay2)
print("Layout has app-layout:", "app-layout" in lay2)
print("Layout structure: sidebar + topbar + main:", 
      "AppSidebar" in lay2 and "app-topbar" in lay2 and "app-main" in lay2)
print("Sidebar has /auth/me:", "/auth/me" in sb2)
print("Sidebar has userName:", "userName" in sb2)
print("Sidebar Props unchanged:", 'appName: string' in sb2 and 'collapsed' in sb2)
print("Sidebar does NOT need user prop:", "user:" not in sb2)
print("\n===== DONE =====")
