# -*- coding: utf-8 -*-
"""
精確還原：用 deploy_v2.py 中的原始 AppLayout 結構
只修改 Sidebar 的 user-card 部分（加入 /auth/me）
"""
import json, urllib.request, ssl, time
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

# ========== 精確還原 AppLayout（從 deploy_v2.py 逐字複製）==========
# 關鍵：用 children（不是 Outlet），因為 App.tsx 用 <AppLayout>{Routes}</AppLayout> 模式
layout_tsx = r'''import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import AppSidebar from "./AppSidebar";

interface Props { children: React.ReactNode; appName: string; }

const ROUTE_NAMES: Record<string, string> = {
  "/": "\u98a8\u96aa\u7e3d\u89bd",
  "/sales": "\u696d\u52d9\u5206\u6790",
  "/categories": "\u98a8\u96aa\u985e\u5225\u5206\u6790",
  "/datasource": "\u8cc7\u6599\u4f86\u6e90",
};

export default function AppLayout({ children, appName }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const [syncMin, setSyncMin] = useState(0);
  const location = useLocation();
  const currentPage = ROUTE_NAMES[location.pathname] || "";

  useEffect(() => {
    const check = () => { if (window.innerWidth < 768) setCollapsed(true); };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  useEffect(() => {
    setSyncMin(0);
    const iv = setInterval(() => setSyncMin(m => m + 1), 60000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="app-layout">
      <AppSidebar collapsed={collapsed} appName={appName} />
      <div className="app-main">
        <div className="app-topbar">
          <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
          </button>
          <div className="breadcrumb">
            <span>{"\u5ba2\u6236\u6d41\u5931\u98a8\u96aa\u5206\u6790"}</span>
            <span className="sep">{"\u203a"}</span>
            <span className="current">{currentPage}</span>
          </div>
          <div className="topbar-spacer" />
          <div className="sync-badge">
            <div className="sync-dot" />
            {"\u5df2\u540c\u6b65"} {syncMin > 0 ? `${syncMin} \u5206\u9418\u524d` : "\u525b\u525b"}
          </div>
        </div>
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}
'''

# ========== Sidebar：保持原始 Props 介面，只加 useEffect 抓 user ==========
sidebar_tsx = r'''import React, { useState, useEffect } from "react";
import { routes, RouteItem } from "../routes";
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
          setUserName(me.name || me.display_name || me.email?.split("@")[0] || "");
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

# Upload
print("=== Upload ===")
r = api("PATCH", f"/builder/apps/{APP}/source/files", {
    "files": {
        "src/components/AppLayout.tsx": layout_tsx,
        "src/components/AppSidebar.tsx": sidebar_tsx,
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
print("\n=== Verify ===")
print("Layout has 'children':", "children" in lay2)
print("Layout has 'Outlet':", "Outlet" in lay2, "(should be False)")
print("Layout has 'app-content':", "app-content" in lay2)
print("Layout has 'appName':", "appName" in lay2)
print("Sidebar has '/auth/me':", "/auth/me" in pvfs2.get("src/components/AppSidebar.tsx", ""))

# 額外驗證：App.tsx 還是 children 模式
app_tsx = pvfs2.get("src/App.tsx", "")
print("App.tsx uses <AppLayout appName=...>:", "<AppLayout appName=" in app_tsx or "AppLayout appName" in app_tsx)

print("\n===== DONE =====")
