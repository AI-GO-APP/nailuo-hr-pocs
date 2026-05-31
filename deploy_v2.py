# -*- coding: utf-8 -*-
"""
全面前端視覺修復 v2 — 對齊 manager-dashboard 目標設計
更新：App.css, DashboardPage, AppSidebar, AppLayout
部署：html + bundle_js + css 完整 publish
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
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

# ========== 登入 ==========
auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
print("1. Login OK")

# ========== 讀取目前 VFS ==========
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data.get("vfs_state", {})
print("2. VFS loaded, %d files" % len(vfs))

# ========== CSS 補丁 ==========
# 讀取目前 CSS，附加新樣式
current_css = vfs.get("src/App.css", "")

css_additions = """
/* === v2 Additions === */

/* KPI danger card background */
.kpi-card.danger { background: var(--danger-light); border-color: #FCA5A5; }
.kpi-card.danger .kpi-icon { background: var(--danger); color: white; }

/* Donut Chart */
.chart-container { display: flex; align-items: center; gap: 20px; }
.donut-wrap { position: relative; width: 140px; height: 140px; flex-shrink: 0; }
.donut-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.donut-center-value { font-size: 28px; font-weight: 700; color: var(--text); line-height: 1; }
.donut-center-label { font-size: 11px; color: var(--text-3); margin-top: 2px; }
.legend { flex: 1; font-size: 13px; }
.legend-item { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.legend-dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.legend-name { flex: 1; color: var(--text-2); }
.legend-value { font-weight: 600; }

/* Risk Circle */
.risk-circle {
  display: inline-flex; align-items: center; justify-content: center;
  width: 26px; height: 26px; border-radius: 50%;
  font-size: 12px; font-weight: 700; color: white;
}
.risk-circle.r4 { background: var(--danger); }
.risk-circle.r3 { background: var(--warning); }
.risk-circle.r2 { background: var(--yellow); }
.risk-circle.r1 { background: #CBD5E1; color: var(--text-2); }

/* Export Button */
.btn-export { background: var(--teal); color: white; }
.btn-export:hover { background: #0E7490; }

/* Icon Button */
.icon-btn { width: 30px; height: 30px; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: var(--text-3); cursor: pointer; transition: all .15s; }
.icon-btn:hover { background: var(--primary-light); color: var(--primary); }

/* NEW tag */
.new-tag { margin-left: auto; font-size: 10px; padding: 2px 6px; border-radius: 4px; background: var(--danger); color: white; font-weight: 500; }

/* Nav sub items */
.nav-sub { margin-left: 14px; border-left: 1px solid var(--border); padding-left: 8px; margin-bottom: 6px; }
.nav-sub .sidebar-item { padding: 6px 12px; font-size: 13px; }

/* Sort arrow */
.sort-arrow { color: var(--text-3); margin-left: 4px; font-size: 10px; cursor: pointer; }
"""

# 如果 CSS 中已經有 v2 additions，先移除再重新加
if "v2 Additions" in current_css:
    idx = current_css.index("/* === v2 Additions")
    current_css = current_css[:idx].rstrip()

new_css = current_css + "\n" + css_additions
print("3. CSS updated: %d -> %d bytes" % (len(current_css), len(new_css)))

# ========== DashboardPage.tsx 完整重寫 ==========
dashboard_tsx = r'''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { FileText, AlertTriangle, Clock, Star, RefreshCw, Loader2, Brain, Eye, Download } from "lucide-react";

function RiskBadge({ score }: { score: number }) {
  const cls = score >= 4 ? "risk-4" : score >= 3 ? "risk-3" : score >= 2 ? "risk-2" : "risk-1";
  const label = score >= 4 ? "\u6975\u9ad8" : score >= 3 ? "\u9ad8" : score >= 2 ? "\u4e2d" : "\u4f4e";
  return <span className={`badge ${cls}`}>{label} ({score})</span>;
}

function RiskCircle({ score }: { score: number }) {
  const cls = score >= 4 ? "r4" : score >= 3 ? "r3" : score >= 2 ? "r2" : "r1";
  return <span className={`risk-circle ${cls}`}>{score}</span>;
}

function CatBadge({ cat }: { cat: string }) {
  const map: Record<string, string> = { "\u7af6\u722d\u6436\u55ae": "cat-competition", "\u54c1\u8cea\u5ba2\u8a34": "cat-quality", "\u71df\u904b\u4e0b\u6ed1": "cat-decline", "\u5e33\u6b3e\u554f\u984c": "cat-payment", "\u95dc\u4fc2\u60e1\u5316": "cat-relation" };
  return <span className={`badge ${map[cat] || ""}`}>{cat}</span>;
}

const CAT_COLORS: Record<string, string> = {
  "\u7af6\u722d\u6436\u55ae": "#DC2626", "\u54c1\u8cea\u5ba2\u8a34": "#EA580C",
  "\u71df\u904b\u4e0b\u6ed1": "#7C3AED", "\u5e33\u6b3e\u554f\u984c": "#CA8A04", "\u95dc\u4fc2\u60e1\u5316": "#BE185D"
};

function DonutChart({ data }: { data: { name: string; count: number }[] }) {
  const total = data.reduce((s, d) => s + d.count, 0);
  if (total === 0) return <p style={{color:"var(--text-3)",textAlign:"center",padding:40}}>{"\u7121\u8cc7\u6599"}</p>;
  const R = 40, C = 2 * Math.PI * R;
  let offset = 0;
  const segments = data.map(d => {
    const len = (d.count / total) * C;
    const seg = { ...d, len, offset, color: CAT_COLORS[d.name] || "#94A3B8" };
    offset += len;
    return seg;
  });
  return (
    <div className="chart-container">
      <div className="donut-wrap">
        <svg viewBox="0 0 100 100" style={{width:"100%",height:"100%",transform:"rotate(-90deg)"}}>
          {segments.map((s, i) => (
            <circle key={i} cx="50" cy="50" r={R} fill="none" stroke={s.color} strokeWidth="18"
              strokeDasharray={`${s.len} ${C}`} strokeDashoffset={-s.offset} />
          ))}
        </svg>
        <div className="donut-center">
          <div className="donut-center-value">{total}</div>
          <div className="donut-center-label">{"\u9ad8\u98a8\u96aa\u65e5\u8a8c"}</div>
        </div>
      </div>
      <div className="legend">
        {data.map(d => (
          <div key={d.name} className="legend-item">
            <div className="legend-dot" style={{background: CAT_COLORS[d.name] || "#94A3B8"}} />
            <div className="legend-name">{d.name}</div>
            <div className="legend-value">{d.count}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiInsight, setAiInsight] = useState("");
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const r = await runAction("analyze_churn", { action: "dashboard", skip_ai: true });
      setData(r.data || r);
    } catch (e: any) { setError(e.message || "\u8f09\u5165\u5931\u6557"); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  const loadAI = async () => {
    setAiLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "dashboard", skip_ai: false });
      setAiInsight((r.data || r).ai_insight || "");
    } catch (e: any) { setAiInsight("AI \u5206\u6790\u5931\u6557: " + (e.message || "")); }
    setAiLoading(false);
  };

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /><p style={{marginTop:12,color:"var(--text-3)"}}>{"\u8f09\u5165\u4e2d..."}</p></div>;
  if (error) return <div className="page"><div className="panel" style={{textAlign:"center"}}><p style={{color:"var(--danger)",marginBottom:12}}>{"\u8f09\u5165\u5931\u6557"}</p><p style={{fontSize:13,color:"var(--text-3)"}}>{error}</p><button className="btn btn-primary" onClick={load} style={{marginTop:16}}><RefreshCw size={14} /> {"\u91cd\u8a66"}</button></div></div>;
  if (!data) return <div className="page"><p>{"\u7121\u8cc7\u6599"}</p></div>;

  const kpi = data.kpi || {};
  const customers = (data.customer_ranking || []).filter((c: any) =>
    !search || c.company?.includes(search) || c.salesperson?.includes(search)
  );
  const highRiskCount = kpi.high_risk_customers || 0;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">{"\u98a8\u96aa\u7e3d\u89bd"}</h1>
          <p className="page-subtitle">{"\u696d\u52d9\u65e5\u8a8c AI \u98a8\u96aa\u5224\u8b80\u7d50\u679c\u5f59\u6574\uff0c\u5171 "}{highRiskCount}{" \u500b\u5ba2\u6236\u88ab\u5224\u5b9a\u70ba\u9ad8\u98a8\u96aa\uff0c\u9700\u512a\u5148\u95dc\u6ce8"}</p>
        </div>
        <div style={{display:"flex",gap:8}}>
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> {"\u66f4\u65b0\u8cc7\u6599"}</button>
          <button className="btn btn-export"><Download size={14} /> {"\u532f\u51fa Excel"}</button>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card"><div className="kpi-icon blue"><FileText size={18} /></div><div className="kpi-label">{"\u5206\u6790\u65e5\u8a8c\u7e3d\u6578"}</div><div className="kpi-value">{kpi.total_logs || 0}</div><div className="kpi-meta">{"\u6db5\u84cb "}{(data.customer_ranking || []).length}{" \u500b\u5ba2\u6236"}</div></div>
        <div className="kpi-card danger"><div className="kpi-icon red"><AlertTriangle size={18} /></div><div className="kpi-label">{"\u9ad8\u98a8\u96aa\u5ba2\u6236"}</div><div className="kpi-value">{highRiskCount}</div><div className="kpi-meta">{"\u98a8\u96aa\u5206\u6578 3 \u4ee5\u4e0a"}</div></div>
        <div className="kpi-card"><div className="kpi-icon orange"><Clock size={18} /></div><div className="kpi-label">{"\u9ad8\u98a8\u96aa\u65e5\u8a8c"}</div><div className="kpi-value">{kpi.high_risk_logs || 0}</div><div className="kpi-meta">Risk 3 + Risk 4</div></div>
        <div className="kpi-card"><div className="kpi-icon purple"><Star size={18} /></div><div className="kpi-label">{"\u4e3b\u8981\u98a8\u96aa\u985e\u578b"}</div><div className="kpi-value" style={{fontSize:22}}>{kpi.top_category || "-"}</div><div className="kpi-meta">{"\u672c\u671f\u6700\u591a\u7b46\u6578\u985e\u578b"}</div></div>
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">{"\u5ba2\u6236\u98a8\u96aa\u6392\u540d"}</div><div className="panel-sub">{"\u9ede\u64ca\u53ef\u770b AI \u5224\u8b80\u53f0\u5e33"}</div></div></div>
          <div className="search-row"><input className="search-input" placeholder={"\u641c\u5c0b\u516c\u53f8\u7c21\u7a31\u3001\u696d\u52d9\u4eba\u54e1..."} value={search} onChange={e => setSearch(e.target.value)} /></div>
          <table>
            <thead><tr><th>{"\u516c\u53f8\u7c21\u7a31"}</th><th>{"\u696d\u52d9\u4eba\u54e1"}</th><th>{"\u7b49\u7d1a"}</th><th>{"\u63a5\u89f8\u6b21\u6578"}</th><th>{"\u6700\u9ad8\u98a8\u96aa"}</th><th>{"\u9ad8\u98a8\u96aa\u65e5\u8a8c"}</th><th>{"\u4e3b\u8981\u98a8\u96aa\u985e\u5225"}</th><th>{"\u7d9c\u5408\u98a8\u96aa"}</th><th></th></tr></thead>
            <tbody>
              {customers.map((c: any) => {
                const compScore = ((c.max_risk || 0) * 2.5 + (c.high_risk_count || 0) * 1.5 + (c.contact_count || 0) * 0.3).toFixed(2);
                return (
                <tr key={c.company}>
                  <td><div className="company-cell">{c.company}</div></td>
                  <td>{c.salesperson}</td>
                  <td><span className="badge grade">{c.grade}</span></td>
                  <td>{c.contact_count}</td>
                  <td><RiskCircle score={c.max_risk} /></td>
                  <td className={`score-cell ${c.high_risk_count > 0 ? "high" : ""}`}>{c.high_risk_count}</td>
                  <td><CatBadge cat={c.main_category} /></td>
                  <td className="score-cell">{compScore}</td>
                  <td><div className="icon-btn"><Eye size={14} /></div></td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:16}}>
          <div className="panel">
            <div className="panel-head"><div><div className="panel-title">{"\u98a8\u96aa\u985e\u5225\u5206\u5e03"}</div><div className="panel-sub">{kpi.high_risk_logs || 0}{" \u7b46\u9ad8\u98a8\u96aa\u65e5\u8a8c"}</div></div></div>
            <DonutChart data={data.category_distribution || []} />
          </div>
          <div className="panel">
            <div className="panel-head"><div><div className="panel-title">{"\u6700\u8a72\u95dc\u6ce8\u7684 5 \u500b\u5ba2\u6236"}</div><div className="panel-sub">{"\u9ede\u64ca\u53ef\u770b AI \u5224\u8b80\u53f0\u5e33"}</div></div></div>
            <div className="top-list">
              {(data.top5_customers || []).map((c: any, i: number) => {
                const compScore = ((c.max_risk || 0) * 2.5 + (c.high_risk_count || 0) * 1.5).toFixed(1);
                return (
                <div key={c.company} className="top-item">
                  <div className="top-rank">{i + 1}</div>
                  <div className="top-content"><div className="top-name">{c.company}</div><div className="top-reason">{c.salesperson}{" - "}{c.main_category}{c.ai_reason ? ("\uff1a" + c.ai_reason) : ""}</div></div>
                  <div className="top-score">{compScore}</div>
                </div>
                );
              })}
            </div>
          </div>
          <div className="panel">
            <div className="panel-head"><div><div className="panel-title">AI {"\u6d1e\u5bdf"}</div></div>
              <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>
                {aiLoading ? <><Loader2 size={14} className="spin" /> {"\u5206\u6790\u4e2d..."}</> : <><Brain size={14} /> {"\u7522\u751f\u6d1e\u5bdf"}</>}
              </button>
            </div>
            {aiInsight ? (
              <div className="ai-reason-box">
                <div className="ai-icon">AI</div>
                <div className="ai-reason-content"><div className="ai-reason-label">AI {"\u4e3b\u7ba1\u6d1e\u5bdf"}</div><div className="ai-reason-text">{aiInsight}</div></div>
              </div>
            ) : !aiLoading ? (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>{"\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf"}</p>) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
'''

# ========== AppSidebar.tsx 增強 ==========
sidebar_tsx = r'''import React from "react";
import { routes, RouteItem } from "../routes";
import { useNavigate, useLocation } from "react-router-dom";
import { LayoutDashboard, ExternalLink, Settings } from "lucide-react";

interface Props { collapsed?: boolean; appName: string; }

export default function AppSidebar({ collapsed, appName }: Props) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <aside className={`app-sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-brand">
        <div className="brand-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l1.9 5.8L19 10.7l-4.1 3 1.6 5.3-4.5-3.3-4.5 3.3 1.6-5.3-4.1-3 5.1-1.9z"/></svg>
        </div>
        <div className="brand-name">{appName}</div>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-group-label">{"\u7e3d\u89bd"}</div>
        <button className="sidebar-item" style={{color:"var(--text-2)"}}>
          <LayoutDashboard size={16} />
          <span>{"\u9996\u9801\u7e3d\u89bd"}</span>
        </button>

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

        <div className="nav-group-label">{"\u7ba1\u7406"}</div>
        <button className="sidebar-item" style={{color:"var(--text-2)"}}>
          <ExternalLink size={16} />
          <span>{"\u5171\u52e4\u53e3\u4ee4\u6bd4"}</span>
        </button>
        <button className="sidebar-item" style={{color:"var(--text-2)"}}>
          <ExternalLink size={16} />
          <span>{"\u5c0f\u5175\u4f30\u9041"}</span>
        </button>
        <button className="sidebar-item" style={{color:"var(--text-2)"}}>
          <Settings size={16} />
          <span>{"\u7cfb\u7d71\u8a2d\u5b9a"}</span>
        </button>
      </nav>
      <div className="user-card">
        <div className="user-avatar">{"\u4e3b"}</div>
        <div className="user-info">
          <div className="user-name">{"\u696d\u52d9\u4e3b\u7ba1"}</div>
          <div className="user-role">manager@company.tw</div>
        </div>
      </div>
    </aside>
  );
}
'''

# ========== AppLayout.tsx 同步時間增強 ==========
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

# ========== 上傳 ==========
files_to_upload = {
    "src/App.css": new_css,
    "src/pages/DashboardPage.tsx": dashboard_tsx,
    "src/components/AppSidebar.tsx": sidebar_tsx,
    "src/components/AppLayout.tsx": layout_tsx,
}

print("\n3. Uploading %d files:" % len(files_to_upload))
for p in sorted(files_to_upload):
    print("   - %s (%d chars)" % (p, len(files_to_upload[p])))

r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": files_to_upload}, token)
if r and "_error" not in r:
    print("   Upload OK")
else:
    print("   Upload FAIL:", r)
    exit(1)

# ========== 強制 publish 來同步 published_vfs ==========
print("\n4. Force sync published_vfs...")
old_html = app_data.get("published_assets", {}).get("html", "")
old_js = app_data.get("published_assets", {}).get("bundle_js", "")
old_css_pub = app_data.get("published_assets", {}).get("css", "")
r = api("POST", f"/builder/apps/{APP}/publish", {
    "published_assets": {"html": old_html, "bundle_js": old_js, "css": old_css_pub}
}, token)
print("   Sync:", "OK" if r and "_error" not in r else "FAIL")

# ========== 編譯 ==========
print("\n5. Compiling...")
time.sleep(2)
c = api("POST", f"/compile/compile/{SLUG}", None, token)
success = c.get("success", False)
errs = c.get("compile_errors", [])
html = c.get("html", "")
bundle_js = c.get("bundle_js", "")
css = c.get("css", "")
print("   success=%s, errors=%d" % (success, len(errs)))
print("   html=%d, bundle_js=%d, css=%d" % (len(html), len(bundle_js), len(css)))
for e in errs:
    print("   ERROR:", json.dumps(e, ensure_ascii=False)[:200])

if not success:
    print("\n   Compile failed! Trying retry...")
    time.sleep(3)
    c = api("POST", f"/compile/compile/{SLUG}", None, token)
    success = c.get("success", False)
    errs = c.get("compile_errors", [])
    html = c.get("html", "")
    bundle_js = c.get("bundle_js", "")
    css = c.get("css", "")
    print("   Retry: success=%s, errors=%d" % (success, len(errs)))
    for e in errs:
        print("   ERROR:", json.dumps(e, ensure_ascii=False)[:200])

# ========== 發佈（完整 assets） ==========
if success:
    print("\n6. Publishing with FULL assets (html + bundle_js + css)...")
    assets = {"html": html}
    if bundle_js:
        assets["bundle_js"] = bundle_js
    if css:
        assets["css"] = css
    r = api("POST", f"/builder/apps/{APP}/publish", {"published_assets": assets}, token)
    print("   Publish:", "OK" if r and "_error" not in r else "FAIL")

    # 驗證
    time.sleep(1)
    app2 = api("GET", f"/builder/apps/{APP}", None, token)
    pa = app2.get("published_assets", {})
    print("\n7. Verification:")
    for k, v in pa.items():
        print("   %s: %d bytes" % (k, len(v) if isinstance(v, str) else 0))
else:
    print("\n6. Skipping publish due to compile failure")

print("\n===== DONE =====")
print("App URL: https://tslg-churn-analysis-manager.ai-go.app")
