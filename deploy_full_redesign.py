# -*- coding: utf-8 -*-
"""
完整前端重設計部署腳本
一次性上傳所有檔案到 VFS，然後編譯發佈。
"""
import json, urllib.request, ssl, time
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"
SLUG = "da1900f990b0"

def api(m, p, d=None, t=None):
    """API 呼叫工具函式"""
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        print(f"  HTTP {e.code}: {detail}")
        return {"_error": e.code, "_detail": detail}

# === 登入 ===
print("=== 1. 登入 ===")
auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth.get("access_token")
if not token:
    print("登入失敗:", json.dumps(auth, ensure_ascii=False)[:200])
    exit(1)
print("  OK: 取得 token")

# ===========================================================
# 定義所有檔案
# ===========================================================

# --- 1. src/App.css ---
app_css = r''':root {
  --primary: #2563EB;
  --primary-dark: #1D4ED8;
  --primary-light: #DBEAFE;
  --danger: #DC2626;
  --danger-light: #FEE2E2;
  --warning: #EA580C;
  --warning-light: #FFEDD5;
  --yellow: #CA8A04;
  --yellow-light: #FEF3C7;
  --success: #16A34A;
  --success-light: #DCFCE7;
  --purple: #7C3AED;
  --purple-light: #EDE9FE;
  --teal: #0891B2;
  --teal-light: #CFFAFE;
  --pink: #BE185D;
  --text: #0F172A;
  --text-2: #475569;
  --text-3: #94A3B8;
  --border: #E2E8F0;
  --bg: #F8FAFC;
  --bg-card: #FFFFFF;
  --sidebar-w: 232px;
  --radius: 12px;
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(15,23,42,0.08);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
button { font-family: inherit; cursor: pointer; border: none; background: none; color: inherit; }

html, body, #root { height: 100%; overflow: hidden; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", sans-serif;
  color: var(--text);
  background: var(--bg);
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* Layout */
.app-layout { display: flex; height: 100vh; height: 100dvh; overflow: hidden; }

/* Sidebar */
.app-sidebar {
  width: var(--sidebar-w); min-width: var(--sidebar-w);
  background: #FFFFFF; border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  flex-shrink: 0; overflow: hidden;
  transition: margin-left 0.25s ease, opacity 0.25s ease;
}
.app-sidebar.collapsed { margin-left: calc(var(--sidebar-w) * -1); opacity: 0; pointer-events: none; }

.sidebar-brand {
  display: flex; align-items: center; gap: 10px;
  padding: 16px 18px; border-bottom: 1px solid var(--border);
}
.brand-logo {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, #2563EB, #7C3AED);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: white; flex-shrink: 0;
}
.brand-name { font-weight: 600; font-size: 15px; color: var(--text); }

.nav-group-label {
  font-size: 11px; color: var(--text-3);
  padding: 14px 12px 6px; font-weight: 500;
  letter-spacing: 0.5px;
}
.sidebar-nav { flex: 1; overflow-y: auto; padding: 0 8px; }
.sidebar-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 8px 12px; border-radius: 8px;
  color: var(--text-2); font-family: inherit;
  font-size: 14px; font-weight: 400;
  cursor: pointer; margin: 1px 0;
  text-align: left; text-decoration: none;
  transition: background 0.15s, color 0.15s;
  background: none;
}
.sidebar-item:hover { background: #F1F5F9; color: var(--text); }
.sidebar-item.active { background: var(--primary-light); color: var(--primary); font-weight: 500; }

.user-card {
  padding: 12px; margin: 8px;
  border: 1px solid var(--border); border-radius: 10px;
  display: flex; align-items: center; gap: 10px;
  flex-shrink: 0;
}
.user-avatar {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, #2563EB, #7C3AED);
  color: white; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; font-size: 14px; flex-shrink: 0;
}
.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 13px; font-weight: 500; }
.user-role { font-size: 11px; color: var(--text-3); }

/* Main */
.app-main {
  flex: 1; min-width: 0;
  display: flex; flex-direction: column;
  overflow: hidden; background: var(--bg);
}

/* Topbar */
.app-topbar {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 28px; border-bottom: 1px solid var(--border);
  background: white; flex-shrink: 0; min-height: 48px;
}
.collapse-btn { padding: 6px; border-radius: 6px; color: var(--text-2); display: flex; align-items: center; }
.collapse-btn:hover { background: #F1F5F9; }
.breadcrumb { font-size: 14px; color: var(--text-2); display: flex; align-items: center; gap: 6px; }
.breadcrumb .sep { color: var(--text-3); }
.breadcrumb .current { color: var(--text); font-weight: 500; }
.topbar-spacer { flex: 1; }
.sync-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 10px; background: var(--success-light);
  border-radius: 999px; font-size: 12px;
  color: var(--success); font-weight: 500;
}
.sync-dot { width: 6px; height: 6px; background: var(--success); border-radius: 50%; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

/* Content */
.app-content { flex: 1; overflow-y: auto; overflow-x: hidden; background: var(--bg); }

/* Mobile */
@media (max-width: 768px) {
  .app-sidebar { position: absolute; top: 0; left: 0; bottom: 0; z-index: 30; margin-left: calc(var(--sidebar-w) * -1); box-shadow: 4px 0 16px rgba(0,0,0,0.12); }
  .app-sidebar:not(.collapsed) { margin-left: 0; opacity: 1; pointer-events: auto; }
}

/* Page */
.page { padding: 28px 32px; max-width: 1400px; }
.page-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; gap: 20px; flex-wrap: wrap; }
.page-title { font-size: 24px; font-weight: 600; margin-bottom: 4px; }
.page-subtitle { color: var(--text-2); font-size: 14px; }

/* Animations */
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
.page { animation: fadeIn 0.25s ease; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }

/* Buttons */
.btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 14px; border-radius: 8px;
  font-size: 13px; font-weight: 500; font-family: inherit;
  transition: all .15s; cursor: pointer; border: none;
}
.btn-primary { background: var(--primary); color: white; }
.btn-primary:hover:not(:disabled) { background: var(--primary-dark); }
.btn-primary:disabled { background: #CBD5E1; cursor: not-allowed; }
.btn-ghost { color: var(--text-2); border: 1px solid var(--border); background: white; }
.btn-ghost:hover { background: var(--bg); color: var(--text); }

/* KPI */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
@media (max-width: 900px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
.kpi-card { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; transition: box-shadow 0.2s; }
.kpi-card:hover { box-shadow: var(--shadow-md); }
.kpi-icon { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; }
.kpi-icon.blue { background: var(--primary-light); color: var(--primary); }
.kpi-icon.red { background: var(--danger-light); color: var(--danger); }
.kpi-icon.orange { background: var(--warning-light); color: var(--warning); }
.kpi-icon.purple { background: var(--purple-light); color: var(--purple); }
.kpi-icon.teal { background: var(--teal-light); color: var(--teal); }
.kpi-label { font-size: 13px; color: var(--text-2); margin-bottom: 6px; }
.kpi-value { font-size: 28px; font-weight: 700; line-height: 1.1; }
.kpi-meta { font-size: 12px; color: var(--text-3); margin-top: 4px; }
.kpi-card.danger .kpi-value { color: var(--danger); }

/* Panel */
.panel { background: white; border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 10px; }
.panel-title { font-size: 16px; font-weight: 600; }
.panel-sub { font-size: 12px; color: var(--text-3); margin-top: 2px; }

/* Dashboard Grid */
.dashboard-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
.sales-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; }
.cat-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
@media (max-width: 900px) { .dashboard-grid, .sales-grid, .cat-detail-grid { grid-template-columns: 1fr; } }

/* Table */
.search-row { margin-bottom: 14px; display: flex; gap: 10px; align-items: center; }
.search-input {
  flex: 1; padding: 9px 14px 9px 38px;
  border: 1px solid var(--border); border-radius: 8px;
  font-size: 14px; font-family: inherit;
  background: var(--bg) url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2' stroke-linecap='round'><circle cx='11' cy='11' r='8'/><line x1='21' y1='21' x2='16.65' y2='16.65'/></svg>") no-repeat 12px center;
  outline: none;
}
.search-input:focus { border-color: var(--primary); background-color: white; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead th {
  text-align: left; padding: 12px 14px; font-weight: 500;
  color: var(--text-2); font-size: 12px;
  border-bottom: 1px solid var(--border);
  background: var(--bg); white-space: nowrap;
}
tbody td { padding: 14px; border-bottom: 1px solid #F1F5F9; }
tbody tr:hover { background: #FAFBFC; }
tbody tr:last-child td { border-bottom: none; }
.company-cell { display: flex; align-items: center; gap: 8px; font-weight: 500; white-space: nowrap; }
.score-cell { font-weight: 600; font-size: 14px; }
.score-cell.high { color: var(--danger); }

/* Badges */
.badge {
  display: inline-flex; align-items: center;
  padding: 3px 10px; border-radius: 999px;
  font-size: 11px; font-weight: 500; white-space: nowrap;
}
.badge.risk-4 { background: var(--danger); color: white; }
.badge.risk-3 { background: var(--warning); color: white; }
.badge.risk-2 { background: var(--yellow-light); color: var(--yellow); }
.badge.risk-1 { background: #F1F5F9; color: var(--text-2); }
.badge.cat-competition { background: var(--danger-light); color: var(--danger); }
.badge.cat-quality { background: var(--warning-light); color: var(--warning); }
.badge.cat-decline { background: var(--purple-light); color: var(--purple); }
.badge.cat-payment { background: var(--yellow-light); color: var(--yellow); }
.badge.cat-relation { background: #FCE7F3; color: #BE185D; }
.badge.grade { padding: 2px 8px; border: 1px solid var(--border); background: white; color: var(--text-2); font-weight: 600; }

/* Bar Chart */
.bar-chart { padding: 4px 0; }
.bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; font-size: 13px; }
.bar-label { width: 96px; color: var(--text-2); flex-shrink: 0; text-align: right; }
.bar-track { flex: 1; height: 22px; background: var(--bg); border-radius: 4px; overflow: hidden; position: relative; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
.bar-value { width: 40px; text-align: right; font-weight: 600; flex-shrink: 0; }

/* Top List */
.top-list { margin-top: 8px; }
.top-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 8px;
  cursor: pointer; transition: background .15s;
}
.top-item:hover { background: var(--danger-light); }
.top-rank {
  width: 24px; height: 24px; background: var(--danger); color: white;
  border-radius: 6px; display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.top-content { flex: 1; min-width: 0; }
.top-name { font-weight: 500; font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.top-reason { font-size: 11px; color: var(--text-2); }
.top-score { font-size: 13px; font-weight: 700; color: var(--danger); }

/* AI Insight */
.ai-reason-box {
  background: linear-gradient(135deg, #DBEAFE 0%, #EDE9FE 100%);
  border-radius: 10px; padding: 14px 16px;
  display: flex; gap: 12px; align-items: flex-start;
  margin-top: 12px;
}
.ai-icon {
  width: 32px; height: 32px; flex-shrink: 0;
  background: white; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: var(--primary);
}
.ai-reason-content { flex: 1; }
.ai-reason-label { font-size: 11px; font-weight: 600; color: var(--primary); letter-spacing: 0.3px; margin-bottom: 2px; }
.ai-reason-text { font-size: 14px; font-weight: 500; color: var(--text); line-height: 1.6; white-space: pre-line; }

/* Warn Card */
.warn-card {
  background: linear-gradient(135deg, #FEE2E2 0%, #FED7AA 100%);
  border: 1px solid #FCA5A5; border-radius: var(--radius);
  padding: 16px; margin-bottom: 12px;
}
.warn-card.green {
  background: linear-gradient(135deg, #DBEAFE 0%, #DCFCE7 100%);
  border-color: #93C5FD;
}
.warn-card-title { font-size: 13px; font-weight: 600; color: #991B1B; margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
.warn-card.green .warn-card-title { color: #065F46; }
.warn-card-desc { font-size: 12px; color: #7F1D1D; line-height: 1.5; }
.warn-card.green .warn-card-desc { color: #047857; }
.warn-card-list { margin-top: 10px; }
.warn-staff-item { display: flex; align-items: center; gap: 10px; padding: 8px; background: rgba(255,255,255,0.6); border-radius: 8px; margin-bottom: 6px; }
.warn-staff-avatar { width: 28px; height: 28px; background: var(--danger); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 12px; flex-shrink: 0; }
.warn-card.green .warn-staff-avatar { background: var(--success); }
.warn-staff-info { flex: 1; min-width: 0; }
.warn-staff-name { font-weight: 600; font-size: 13px; color: var(--text); }
.warn-staff-meta { font-size: 11px; color: var(--text-2); }
.warn-staff-stat { font-size: 13px; font-weight: 700; color: var(--danger); }
.warn-card.green .warn-staff-stat { color: var(--success); }

/* Grade Matrix */
.grade-matrix { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 16px; }
.grade-cell { background: white; border: 1px solid var(--border); border-radius: 10px; padding: 14px; text-align: center; }
.grade-cell-label { font-size: 11px; color: var(--text-3); }
.grade-cell-letter { font-size: 24px; font-weight: 700; margin: 4px 0; }
.grade-cell-letter.A { color: var(--danger); }
.grade-cell-letter.B { color: var(--warning); }
.grade-cell-letter.C { color: var(--yellow); }
.grade-cell-letter.D { color: var(--purple); }
.grade-cell-letter.E { color: var(--text-2); }
.grade-cell-stat { font-size: 12px; color: var(--text-2); }
.grade-cell-stat strong { font-size: 14px; color: var(--text); }

/* Action List */
.action-list { }
.action-item {
  display: flex; gap: 12px; padding: 12px;
  border: 1px solid var(--border); border-radius: 10px;
  margin-bottom: 10px; cursor: pointer; transition: all 0.15s;
}
.action-item:hover { border-color: var(--primary); background: var(--primary-light); }
.action-priority {
  width: 28px; height: 28px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 12px; flex-shrink: 0;
}
.action-priority.p1 { background: var(--danger); color: white; }
.action-priority.p2 { background: var(--warning); color: white; }
.action-content { flex: 1; min-width: 0; }
.action-title { font-weight: 600; font-size: 13px; margin-bottom: 2px; }
.action-desc { font-size: 12px; color: var(--text-2); line-height: 1.5; }
.action-tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: var(--bg); color: var(--text-2); margin-right: 4px; display: inline-block; margin-top: 4px; }

/* Category Tabs */
.cat-tabs { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
.cat-tab {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 18px; border: 2px solid var(--border);
  border-radius: var(--radius); background: white;
  cursor: pointer; transition: all 0.15s;
  flex: 1; min-width: 160px;
}
.cat-tab:hover { border-color: var(--text-3); }
.cat-tab.active { border-color: currentColor; box-shadow: var(--shadow-md); }
.cat-tab-icon { flex-shrink: 0; }
.cat-tab-content { flex: 1; min-width: 0; text-align: left; }
.cat-tab-name { font-weight: 600; font-size: 13px; color: var(--text); }
.cat-tab-stat { font-size: 11px; color: var(--text-3); margin-top: 2px; }
.cat-tab-value { font-size: 20px; font-weight: 700; }

/* Category Summary */
.cat-summary-card {
  background: white; border-radius: var(--radius);
  padding: 22px 24px; position: relative;
  overflow: hidden; color: white;
}
.cat-summary-card::before {
  content: ''; position: absolute; top: 0; right: 0;
  width: 200px; height: 200px;
  background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
}
.cat-summary-name { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
.cat-summary-desc { font-size: 13px; opacity: 0.9; line-height: 1.6; margin-bottom: 16px; }
.cat-summary-stats { display: flex; gap: 24px; }
.cat-summary-stat-label { font-size: 11px; opacity: 0.8; }
.cat-summary-stat-value { font-size: 22px; font-weight: 700; }

/* Category Customer Card */
.cat-customer-card {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; border: 1px solid var(--border);
  border-radius: 10px; margin-bottom: 8px;
  cursor: pointer; transition: all 0.15s;
}
.cat-customer-card:hover { border-color: var(--primary); background: var(--primary-light); }
.cat-customer-rank { width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; color: white; flex-shrink: 0; }
.cat-customer-info { flex: 1; min-width: 0; }
.cat-customer-name { font-weight: 600; font-size: 13px; }
.cat-customer-reason { font-size: 11px; color: var(--text-2); margin-top: 2px; line-height: 1.5; }
.cat-customer-score { font-size: 14px; font-weight: 700; }

/* Data Source */
.data-status-card {
  background: linear-gradient(135deg, #DBEAFE 0%, #EDE9FE 100%);
  border: 1px solid var(--primary-light); border-radius: var(--radius);
  padding: 20px; margin-bottom: 24px;
  display: flex; align-items: center; gap: 20px;
}
.data-status-icon { width: 56px; height: 56px; background: white; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.data-status-info { flex: 1; }
.data-status-title { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.data-status-meta { font-size: 13px; color: var(--text-2); }
.data-status-meta strong { color: var(--text); }
.data-source-tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 1px solid var(--border); }
.data-tab { padding: 10px 16px; font-size: 14px; color: var(--text-2); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; }
.data-tab.active { color: var(--primary); border-bottom-color: var(--primary); font-weight: 500; }
.data-tab:hover { color: var(--text); }
.connector-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; margin-bottom: 24px; }
.connector-item { padding: 14px; border: 1px solid var(--border); border-radius: 10px; background: white; }
.connector-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.connector-logo { width: 36px; height: 36px; background: var(--bg); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--text-2); flex-shrink: 0; }
.connector-info { flex: 1; }
.connector-name { font-weight: 500; font-size: 13px; }
.connector-status { font-size: 11px; color: var(--success); display: flex; align-items: center; gap: 4px; }
.dot { width: 6px; height: 6px; background: var(--success); border-radius: 50%; display: inline-block; }
.connector-meta { font-size: 11px; color: var(--text-3); margin-top: 6px; }
'''

# --- 2. src/components/AppLayout.tsx ---
app_layout_tsx = '''import React, { useState, useEffect } from "react";
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
  const location = useLocation();
  const currentPage = ROUTE_NAMES[location.pathname] || "";

  useEffect(() => {
    const check = () => { if (window.innerWidth < 768) setCollapsed(true); };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
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
            <span>\u5ba2\u6236\u6d41\u5931\u98a8\u96aa\u5206\u6790</span>
            <span className="sep">\u203a</span>
            <span className="current">{currentPage}</span>
          </div>
          <div className="topbar-spacer" />
          <div className="sync-badge">
            <div className="sync-dot" />
            \u5df2\u540c\u6b65
          </div>
        </div>
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}
'''

# --- 3. src/components/AppSidebar.tsx ---
app_sidebar_tsx = '''import React from "react";
import { routes, RouteItem } from "../routes";
import { useNavigate, useLocation } from "react-router-dom";

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
        <div className="nav-group-label">\u5ba2\u6236\u6d41\u5931\u98a8\u96aa\u5206\u6790</div>
        {routes.map((item, i) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <button key={i} className={`sidebar-item ${isActive ? "active" : ""}`} onClick={() => navigate(item.path)}>
              {Icon && <Icon size={16} />}
              <span>{item.title}</span>
            </button>
          );
        })}
      </nav>
      <div className="user-card">
        <div className="user-avatar">\u4e3b</div>
        <div className="user-info">
          <div className="user-name">\u696d\u52d9\u4e3b\u7ba1</div>
          <div className="user-role">manager@company.tw</div>
        </div>
      </div>
    </aside>
  );
}
'''

# --- 4. src/pages/DashboardPage.tsx ---
dashboard_tsx = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { FileText, AlertTriangle, Clock, Star, RefreshCw, Loader2, Brain } from "lucide-react";

function RiskBadge({ score }: { score: number }) {
  const cls = score >= 4 ? "risk-4" : score >= 3 ? "risk-3" : score >= 2 ? "risk-2" : "risk-1";
  const label = score >= 4 ? "\u6975\u9ad8" : score >= 3 ? "\u9ad8" : score >= 2 ? "\u4e2d" : "\u4f4e";
  return <span className={`badge ${cls}`}>{label} ({score})</span>;
}

function CatBadge({ cat }: { cat: string }) {
  const map: Record<string, string> = { "\u7af6\u722d\u6436\u55ae": "cat-competition", "\u54c1\u8cea\u5ba2\u8a34": "cat-quality", "\u71df\u904b\u4e0b\u6ed1": "cat-decline", "\u5e33\u6b3e\u554f\u984c": "cat-payment", "\u95dc\u4fc2\u60e1\u5316": "cat-relation" };
  return <span className={`badge ${map[cat] || ""}`}>{cat}</span>;
}

function BarChart({ data }: { data: { name: string; count: number }[] }) {
  const max = Math.max(...data.map(d => d.count), 1);
  const colors = ["#DC2626", "#EA580C", "#7C3AED", "#CA8A04", "#BE185D"];
  return (
    <div className="bar-chart">
      {data.map((d, i) => (
        <div key={d.name} className="bar-row">
          <div className="bar-label">{d.name}</div>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${(d.count / max) * 100}%`, background: colors[i % colors.length] }} /></div>
          <div className="bar-value">{d.count}</div>
        </div>
      ))}
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

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /><p style={{marginTop:12,color:"var(--text-3)"}}>\u8f09\u5165\u4e2d...</p></div>;
  if (error) return <div className="page"><div className="panel" style={{textAlign:"center"}}><p style={{color:"var(--danger)",marginBottom:12}}>\u8f09\u5165\u5931\u6557</p><p style={{fontSize:13,color:"var(--text-3)"}}>{error}</p><button className="btn btn-primary" onClick={load} style={{marginTop:16}}><RefreshCw size={14} /> \u91cd\u8a66</button></div></div>;
  if (!data) return <div className="page"><p>\u7121\u8cc7\u6599</p></div>;

  const kpi = data.kpi || {};
  const customers = (data.customer_ranking || []).filter((c: any) =>
    !search || c.company?.includes(search) || c.salesperson?.includes(search)
  );

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">\u98a8\u96aa\u7e3d\u89bd</h1>
          <p className="page-subtitle">\u696d\u52d9\u65e5\u8a8c AI \u98a8\u96aa\u5224\u8b80\u7d50\u679c\u5f59\u6574</p>
        </div>
        <div style={{display:"flex",gap:8}}>
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> \u66f4\u65b0\u8cc7\u6599</button>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card"><div className="kpi-icon blue"><FileText size={18} /></div><div className="kpi-label">\u5206\u6790\u65e5\u8a8c\u7e3d\u6578</div><div className="kpi-value">{kpi.total_logs || 0}</div><div className="kpi-meta">\u6db5\u84cb {(data.customer_ranking || []).length} \u500b\u5ba2\u6236</div></div>
        <div className="kpi-card danger"><div className="kpi-icon red"><AlertTriangle size={18} /></div><div className="kpi-label">\u9ad8\u98a8\u96aa\u5ba2\u6236</div><div className="kpi-value">{kpi.high_risk_customers || 0}</div><div className="kpi-meta">\u98a8\u96aa\u5206\u6578 3 \u4ee5\u4e0a</div></div>
        <div className="kpi-card"><div className="kpi-icon orange"><Clock size={18} /></div><div className="kpi-label">\u9ad8\u98a8\u96aa\u65e5\u8a8c</div><div className="kpi-value">{kpi.high_risk_logs || 0}</div><div className="kpi-meta">Risk 3 + Risk 4</div></div>
        <div className="kpi-card"><div className="kpi-icon purple"><Star size={18} /></div><div className="kpi-label">\u4e3b\u8981\u98a8\u96aa\u985e\u578b</div><div className="kpi-value" style={{fontSize:22}}>{kpi.top_category || "-"}</div><div className="kpi-meta">\u672c\u671f\u6700\u591a\u7b46\u6578\u985e\u578b</div></div>
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">\u5ba2\u6236\u98a8\u96aa\u6392\u540d</div><div className="panel-sub">\u4f9d\u6700\u9ad8\u98a8\u96aa\u5206\u6578\u6392\u5e8f</div></div></div>
          <div className="search-row"><input className="search-input" placeholder="\u641c\u5c0b\u516c\u53f8\u7c21\u7a31\u3001\u696d\u52d9\u4eba\u54e1..." value={search} onChange={e => setSearch(e.target.value)} /></div>
          <table>
            <thead><tr><th>\u516c\u53f8\u7c21\u7a31</th><th>\u696d\u52d9\u4eba\u54e1</th><th>\u7b49\u7d1a</th><th>\u63a5\u89f8\u6b21\u6578</th><th>\u6700\u9ad8\u98a8\u96aa</th><th>\u9ad8\u98a8\u96aa\u65e5\u8a8c</th><th>\u4e3b\u8981\u98a8\u96aa\u985e\u5225</th></tr></thead>
            <tbody>
              {customers.map((c: any) => (
                <tr key={c.company}>
                  <td><div className="company-cell">{c.company}</div></td>
                  <td>{c.salesperson}</td>
                  <td><span className="badge grade">{c.grade}</span></td>
                  <td>{c.contact_count}</td>
                  <td><RiskBadge score={c.max_risk} /></td>
                  <td className={`score-cell ${c.high_risk_count > 0 ? "high" : ""}`}>{c.high_risk_count}</td>
                  <td><CatBadge cat={c.main_category} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:16}}>
          <div className="panel">
            <div className="panel-head"><div><div className="panel-title">\u98a8\u96aa\u985e\u5225\u5206\u5e03</div><div className="panel-sub">{kpi.high_risk_logs || 0} \u7b46\u9ad8\u98a8\u96aa\u65e5\u8a8c</div></div></div>
            <BarChart data={data.category_distribution || []} />
          </div>
          <div className="panel">
            <div className="panel-head"><div><div className="panel-title">\u6700\u8a72\u95dc\u6ce8\u7684 5 \u500b\u5ba2\u6236</div><div className="panel-sub">\u4f9d\u98a8\u96aa\u5206\u6578\u6392\u5e8f</div></div></div>
            <div className="top-list">
              {(data.top5_customers || []).map((c: any, i: number) => (
                <div key={c.company} className="top-item">
                  <div className="top-rank">{i + 1}</div>
                  <div className="top-content"><div className="top-name">{c.company}</div><div className="top-reason">{c.salesperson} - {c.main_category}</div></div>
                  <div className="top-score">Risk {c.max_risk}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="panel">
            <div className="panel-head"><div><div className="panel-title">AI \u6d1e\u5bdf</div></div>
              <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>
                {aiLoading ? <><Loader2 size={14} className="spin" /> \u5206\u6790\u4e2d...</> : <><Brain size={14} /> \u7522\u751f\u6d1e\u5bdf</>}
              </button>
            </div>
            {aiInsight ? (
              <div className="ai-reason-box">
                <div className="ai-icon">AI</div>
                <div className="ai-reason-content"><div className="ai-reason-label">AI \u4e3b\u7ba1\u6d1e\u5bdf</div><div className="ai-reason-text">{aiInsight}</div></div>
              </div>
            ) : !aiLoading ? (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf</p>) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
'''

# --- 5. src/pages/SalesPage.tsx ---
sales_tsx = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Users, AlertTriangle, Flame, UserCheck, RefreshCw, Loader2, Brain } from "lucide-react";

function QuadrantChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) return <p style={{color:"var(--text-3)",textAlign:"center",padding:40}}>\u7121\u8cc7\u6599</p>;
  const W = 700, H = 360;
  const pad = { top: 30, right: 30, bottom: 40, left: 50 };
  const innerW = W - pad.left - pad.right;
  const innerH = H - pad.top - pad.bottom;
  const maxX = Math.max(...data.map(d => d.x), 15);
  const maxY = Math.max(...data.map(d => d.y), 4);
  const midX = maxX / 2, midY = maxY / 2;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{width:"100%",height:"auto"}}>
      <line x1={pad.left} y1={H-pad.bottom} x2={W-pad.right} y2={H-pad.bottom} stroke="#E2E8F0" strokeWidth={1} />
      <line x1={pad.left} y1={pad.top} x2={pad.left} y2={H-pad.bottom} stroke="#E2E8F0" strokeWidth={1} />
      <line x1={pad.left+innerW*(midX/maxX)} y1={pad.top} x2={pad.left+innerW*(midX/maxX)} y2={H-pad.bottom} stroke="#F1F5F9" strokeDasharray="4" />
      <line x1={pad.left} y1={pad.top+innerH*(1-midY/maxY)} x2={W-pad.right} y2={pad.top+innerH*(1-midY/maxY)} stroke="#F1F5F9" strokeDasharray="4" />
      <text x={W-pad.right-10} y={pad.top+15} textAnchor="end" fontSize={11} fill="#94A3B8" fontWeight={500}>\u6551\u706b\u578b</text>
      <text x={pad.left+10} y={pad.top+15} fontSize={11} fill="#94A3B8" fontWeight={500}>\u5931\u806f\u578b</text>
      <text x={W-pad.right-10} y={H-pad.bottom-8} textAnchor="end" fontSize={11} fill="#94A3B8" fontWeight={500}>\u7a69\u5b9a\u578b</text>
      {data.map((d, i) => {
        const cx = pad.left + (d.x / maxX) * innerW;
        const cy = pad.top + (1 - d.y / maxY) * innerH;
        const r = Math.max(10, Math.min(22, d.size * 5));
        const color = d.y > midY ? (d.x > midX ? "#DC2626" : "#CA8A04") : (d.x > midX ? "#16A34A" : "#94A3B8");
        return (<g key={i}><circle cx={cx} cy={cy} r={r} fill={color} opacity={0.6} stroke="white" strokeWidth={2} /><text x={cx} y={cy-r-4} textAnchor="middle" fontSize={11} fill="#0F172A" fontWeight={500}>{d.name}</text></g>);
      })}
    </svg>
  );
}

export default function SalesPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiInsight, setAiInsight] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { const r = await runAction("analyze_churn", { action: "sales_analysis", skip_ai: true }); setData(r.data || r); } catch (e: any) { setError(e.message || "\u8f09\u5165\u5931\u6557"); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  const loadAI = async () => {
    setAiLoading(true);
    try { const r = await runAction("analyze_churn", { action: "sales_analysis", skip_ai: false }); setAiInsight((r.data || r).ai_insight || ""); } catch { setAiInsight("AI \u5206\u6790\u5931\u6557"); }
    setAiLoading(false);
  };

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /></div>;
  if (error) return <div className="page"><div className="panel" style={{textAlign:"center"}}><p style={{color:"var(--danger)"}}>{error}</p><button className="btn btn-primary" onClick={load} style={{marginTop:16}}><RefreshCw size={14} /> \u91cd\u8a66</button></div></div>;
  if (!data) return <div className="page"><p>\u7121\u8cc7\u6599</p></div>;
  const kpi = data.kpi || {};
  const staff = data.staff_ranking || [];
  const warnStaff = staff.filter((s: any) => s.high_risk_count >= 2);
  const goodStaff = staff.filter((s: any) => s.high_risk_count <= 0);
  const gradeData = data.grade_distribution || [];
  const actions = data.action_items || [];

  return (
    <div className="page">
      <div className="page-head"><div><h1 className="page-title">\u696d\u52d9\u5206\u6790</h1><p className="page-subtitle">\u5f9e\u696d\u52d9\u89d2\u5ea6\u770b\uff1a\u8ab0\u7684\u5ba2\u6236\u6700\u8a72\u95dc\u6ce8\u3001\u8ab0\u53ef\u80fd\u4e0d\u64c5\u65bc\u7dad\u7e6b\u5ba2\u6236\u95dc\u4fc2</p></div><button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> \u66f4\u65b0</button></div>
      <div className="kpi-grid">
        <div className="kpi-card"><div className="kpi-icon teal"><Users size={18} /></div><div className="kpi-label">\u5206\u6790\u696d\u52d9\u4eba\u54e1</div><div className="kpi-value">{kpi.total_staff || 0}</div><div className="kpi-meta">\u672c\u671f\u81f3\u5c11 1 \u7b46\u65e5\u8a8c</div></div>
        <div className="kpi-card danger"><div className="kpi-icon red"><AlertTriangle size={18} /></div><div className="kpi-label">\u9ad8\u98a8\u96aa\u96c6\u4e2d\u696d\u52d9</div><div className="kpi-value">{kpi.concentrated_risk || 0} \u4eba</div><div className="kpi-meta">\u7ba1\u8f44 2 \u500b\u4ee5\u4e0a\u9ad8\u98a8\u96aa\u5ba2\u6236</div></div>
        <div className="kpi-card"><div className="kpi-icon orange"><Flame size={18} /></div><div className="kpi-label">\u6551\u706b\u578b\u696d\u52d9</div><div className="kpi-value">{kpi.firefighter || 0} \u4eba</div><div className="kpi-meta">\u9ad8\u983b\u62dc\u8a2a\u4f46\u5ba2\u6236\u4ecd\u9ad8\u98a8\u96aa</div></div>
        <div className="kpi-card"><div className="kpi-icon purple"><UserCheck size={18} /></div><div className="kpi-label">\u5ba2\u6236\u88ab\u591a\u4eba\u62dc\u8a2a</div><div className="kpi-value">{kpi.multi_visit || 0} \u500b</div><div className="kpi-meta">\u4ea4\u63a5\u6df7\u4e82\u98a8\u96aa</div></div>
      </div>

      <div className="panel" style={{marginBottom:16}}>
        <div className="panel-head"><div><div className="panel-title">\u696d\u52d9\u4eba\u54e1\u98a8\u96aa\u5730\u5716</div><div className="panel-sub">X: \u62dc\u8a2a\u983b\u7387 / Y: \u5e73\u5747\u98a8\u96aa\u5206 / \u5713\u5708\u5927\u5c0f: \u9ad8\u98a8\u96aa\u5ba2\u6236\u6578</div></div></div>
        <QuadrantChart data={data.quadrant_data || []} />
      </div>

      <div className="sales-grid">
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">\u696d\u52d9\u4eba\u54e1\u98a8\u96aa\u6392\u540d</div><div className="panel-sub">\u4f9d\u7ba1\u8f44\u9ad8\u98a8\u96aa\u5ba2\u6236\u6578\u6392\u5e8f</div></div></div>
          <table><thead><tr><th>\u696d\u52d9\u4eba\u54e1</th><th>\u7ba1\u8f44\u5ba2\u6236</th><th>\u9ad8\u98a8\u96aa\u5ba2\u6236</th><th>\u62dc\u8a2a\u7e3d\u6b21\u6578</th><th>\u5e73\u5747\u98a8\u96aa</th></tr></thead>
          <tbody>{staff.map((s: any) => (<tr key={s.name}><td style={{fontWeight:500}}>{s.name}</td><td>{s.customer_count}</td><td className={`score-cell ${s.high_risk_count >= 2 ? "high" : ""}`}>{s.high_risk_count}</td><td>{s.visits}</td><td>{s.avg_risk}</td></tr>))}</tbody></table>
        </div>
        <div>
          {warnStaff.length > 0 && (
            <div className="warn-card">
              <div className="warn-card-title"><AlertTriangle size={14} /> \u4e0d\u64c5\u7dad\u7e6b\u5ba2\u6236 Top {Math.min(3, warnStaff.length)}</div>
              <div className="warn-card-desc">\u9ad8\u98a8\u96aa\u5ba2\u6236\u6bd4\u4f8b\u6700\u9ad8\u7684\u696d\u52d9\uff0c\u5efa\u8b70\u4e3b\u7ba1 1-on-1 \u4e86\u89e3\u72c0\u6cc1</div>
              <div className="warn-card-list">
                {warnStaff.slice(0, 3).map((s: any) => (
                  <div key={s.name} className="warn-staff-item">
                    <div className="warn-staff-avatar">{s.name[0]}</div>
                    <div className="warn-staff-info"><div className="warn-staff-name">{s.name}</div><div className="warn-staff-meta">\u7ba1\u8f44 {s.customer_count} \u500b\u5ba2\u6236 / {s.high_risk_count} \u500b\u9ad8\u98a8\u96aa</div></div>
                    <div className="warn-staff-stat">{s.customer_count > 0 ? Math.round(s.high_risk_count / s.customer_count * 100) : 0}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {goodStaff.length > 0 && (
            <div className="warn-card green">
              <div className="warn-card-title"><UserCheck size={14} /> \u5ba2\u6236\u7dad\u8b77\u512a\u7b49\u751f</div>
              <div className="warn-card-desc">\u5ba2\u6236\u7a69\u5b9a\u7684\u696d\u52d9\uff0c\u503c\u5f97\u80af\u5b9a\u8207\u7d93\u9a57\u5206\u4eab</div>
              <div className="warn-card-list">
                {goodStaff.slice(0, 3).map((s: any) => (
                  <div key={s.name} className="warn-staff-item">
                    <div className="warn-staff-avatar">{s.name[0]}</div>
                    <div className="warn-staff-info"><div className="warn-staff-name">{s.name}</div><div className="warn-staff-meta">\u7ba1\u8f44 {s.customer_count} \u500b\u5ba2\u6236 / {s.high_risk_count} \u500b\u9ad8\u98a8\u96aa</div></div>
                    <div className="warn-staff-stat">{s.customer_count > 0 ? Math.round(s.high_risk_count / s.customer_count * 100) : 0}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {gradeData.length > 0 && (
        <div className="panel" style={{marginTop:16}}>
          <div className="panel-head"><div><div className="panel-title">\u5ba2\u6236\u7b49\u7d1a\u98a8\u96aa\u5206\u5e03</div><div className="panel-sub">A \u7d1a\u5ba2\u6236\u6d41\u5931\u640d\u5931\u6700\u5927\uff0c\u9700\u512a\u5148\u8655\u7406</div></div></div>
          <div className="grade-matrix">
            {gradeData.map((g: any) => (
              <div key={g.grade} className="grade-cell">
                <div className="grade-cell-label">{g.grade} \u7d1a\u5ba2\u6236</div>
                <div className={`grade-cell-letter ${g.grade}`}>{g.grade}</div>
                <div className="grade-cell-stat"><strong>{g.high_risk}</strong> / \u9ad8\u98a8\u96aa</div>
                <div className="grade-cell-stat" style={{fontSize:11,color:"var(--text-3)"}}>\u5171 {g.total} \u500b\u5ba2\u6236</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="panel" style={{marginTop:16}}>
        <div className="panel-head"><div><div className="panel-title">AI \u6d1e\u5bdf</div></div>
          <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>{aiLoading ? <><Loader2 size={14} className="spin" /> \u5206\u6790\u4e2d...</> : <><Brain size={14} /> \u7522\u751f\u6d1e\u5bdf</>}</button>
        </div>
        {aiInsight ? (<div className="ai-reason-box"><div className="ai-icon">AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI \u696d\u52d9\u5206\u6790</div><div className="ai-reason-text">{aiInsight}</div></div></div>
        ) : !aiLoading ? (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf</p>) : null}
      </div>
    </div>
  );
}
'''

# --- 6. src/pages/CategoriesPage.tsx ---
categories_tsx = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Loader2, Brain, Swords, Wrench, TrendingDown, Wallet, HeartCrack } from "lucide-react";

const CATEGORIES = [
  { id: "\u7af6\u722d\u6436\u55ae", label: "\u7af6\u722d\u6436\u55ae", color: "#DC2626", icon: Swords },
  { id: "\u54c1\u8cea\u5ba2\u8a34", label: "\u54c1\u8cea\u5ba2\u8a34", color: "#EA580C", icon: Wrench },
  { id: "\u71df\u904b\u4e0b\u6ed1", label: "\u71df\u904b\u4e0b\u6ed1", color: "#7C3AED", icon: TrendingDown },
  { id: "\u5e33\u6b3e\u554f\u984c", label: "\u5e33\u6b3e\u554f\u984c", color: "#CA8A04", icon: Wallet },
  { id: "\u95dc\u4fc2\u60e1\u5316", label: "\u95dc\u4fc2\u60e1\u5316", color: "#BE185D", icon: HeartCrack },
];

export default function CategoriesPage() {
  const [active, setActive] = useState(CATEGORIES[0].id);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiInsight, setAiInsight] = useState("");
  const [counts, setCounts] = useState<Record<string, number>>({});

  const loadCounts = useCallback(async () => {
    try { const r = await runAction("analyze_churn", { action: "dashboard", skip_ai: true }); const d = r.data || r; const dist = d.category_distribution || []; const map: Record<string, number> = {}; dist.forEach((item: any) => { map[item.name] = item.count; }); setCounts(map); } catch (e) { console.error(e); }
  }, []);
  useEffect(() => { loadCounts(); }, [loadCounts]);

  const loadDetail = useCallback(async (cat: string) => {
    setLoading(true); setAiInsight("");
    try { const r = await runAction("analyze_churn", { action: "category_detail", category: cat, skip_ai: true }); setDetail(r.data || r); } catch (e) { console.error(e); setDetail(null); }
    setLoading(false);
  }, []);
  useEffect(() => { loadDetail(active); }, [active, loadDetail]);

  const loadAI = async () => {
    setAiLoading(true);
    try { const r = await runAction("analyze_churn", { action: "category_detail", category: active, skip_ai: false }); setAiInsight((r.data || r).ai_insight || ""); } catch { setAiInsight("AI \u5206\u6790\u5931\u6557"); }
    setAiLoading(false);
  };

  const activeCat = CATEGORIES.find(c => c.id === active)!;

  return (
    <div className="page">
      <div className="page-head"><div><h1 className="page-title">\u98a8\u96aa\u985e\u5225\u5206\u6790</h1><p className="page-subtitle">\u6df1\u5165\u5256\u6790\u5404\u985e\u98a8\u96aa\u7684\u771f\u5be6\u6210\u56e0</p></div></div>
      <div className="cat-tabs">
        {CATEGORIES.map(cat => {
          const Icon = cat.icon;
          return (
            <div key={cat.id} className={`cat-tab ${active === cat.id ? "active" : ""}`} style={active === cat.id ? {borderColor: cat.color, color: cat.color} : {}} onClick={() => setActive(cat.id)}>
              <div className="cat-tab-icon"><Icon size={22} color={cat.color} /></div>
              <div className="cat-tab-content"><div className="cat-tab-name">{cat.label}</div><div className="cat-tab-stat">{counts[cat.id] || 0} \u7b46\u65e5\u8a8c</div></div>
              <div className="cat-tab-value" style={{color: cat.color}}>{counts[cat.id] || 0}</div>
            </div>
          );
        })}
      </div>
      {loading ? (<div style={{textAlign:"center",padding:60}}><Loader2 className="spin" size={32} /></div>) : detail ? (
        <>
          <div className="cat-summary-card" style={{background:`linear-gradient(135deg, ${activeCat.color}, ${activeCat.color}dd)`,marginBottom:16}}>
            <div className="cat-summary-name">{activeCat.label}</div>
            <div className="cat-summary-desc">\u5171 {detail.total_logs} \u7b46\u65e5\u8a8c\uff0c\u5f71\u97ff {detail.total_customers} \u500b\u5ba2\u6236</div>
            <div className="cat-summary-stats"><div><div className="cat-summary-stat-label">\u65e5\u8a8c\u6578</div><div className="cat-summary-stat-value">{detail.total_logs}</div></div><div><div className="cat-summary-stat-label">\u5ba2\u6236\u6578</div><div className="cat-summary-stat-value">{detail.total_customers}</div></div></div>
          </div>
          <div className="cat-detail-grid">
            <div className="panel"><div className="panel-head"><div><div className="panel-title">\u6b64\u985e\u5225 Top \u5ba2\u6236</div></div></div>
              {(detail.top_customers || []).map((c: any, i: number) => (<div key={c.company} className="cat-customer-card"><div className="cat-customer-rank" style={{background: activeCat.color}}>{i+1}</div><div className="cat-customer-info"><div className="cat-customer-name">{c.company}</div><div className="cat-customer-reason">{c.count} \u7b46\u76f8\u95dc\u65e5\u8a8c</div></div></div>))}
            </div>
            <div className="panel"><div className="panel-head"><div><div className="panel-title">\u6b64\u985e\u5225\u5f71\u97ff\u696d\u52d9</div></div></div>
              {(detail.top_staff || []).map((s: any, i: number) => (<div key={s.name} className="cat-customer-card"><div className="cat-customer-rank" style={{background: "#475569"}}>{i+1}</div><div className="cat-customer-info"><div className="cat-customer-name">{s.name}</div><div className="cat-customer-reason">{s.count} \u7b46\u76f8\u95dc\u65e5\u8a8c</div></div></div>))}
            </div>
          </div>
          <div className="panel">
            <div className="panel-head"><div><div className="panel-title">AI \u6d1e\u5bdf - {activeCat.label}</div></div>
              <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>{aiLoading ? <><Loader2 size={14} className="spin" /> \u5206\u6790\u4e2d...</> : <><Brain size={14} /> \u7522\u751f\u6d1e\u5bdf</>}</button>
            </div>
            {aiInsight ? (<div className="ai-reason-box"><div className="ai-icon">AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI \u985e\u5225\u6df1\u5ea6\u5206\u6790</div><div className="ai-reason-text">{aiInsight}</div></div></div>
            ) : !aiLoading ? (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf</p>) : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
'''

# --- 7. src/pages/DataSourcePage.tsx ---
datasource_tsx = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Loader2, RefreshCw, Link2, FileText, BarChart3, Database, XCircle } from "lucide-react";

export default function DataSourcePage() {
  const [sources, setSources] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"status" | "logs">("status");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await runAction("fetch_crm_data", { action: "refs_status" });
      setSources((r.data || r).sources || []);
      const r2 = await runAction("fetch_crm_data", { action: "raw_logs" });
      setLogs((r2.data || r2).logs || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /></div>;

  const connected = sources.filter(s => s.status === "connected").length;
  const totalRecords = sources.reduce((sum, s) => sum + (s.count || 0), 0);
  const icons = [Link2, FileText, BarChart3];

  return (
    <div className="page">
      <div className="page-head"><div><h1 className="page-title">\u8cc7\u6599\u4f86\u6e90</h1><p className="page-subtitle">CRM \u696d\u52d9\u65e5\u8a8c\u8cc7\u6599\u5373\u6642\u540c\u6b65\uff0cAI \u5206\u6790\u81ea\u52d5\u66f4\u65b0</p></div><div style={{display:"flex",gap:8}}><button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> \u66f4\u65b0</button></div></div>
      <div className="data-status-card">
        <div className="data-status-icon"><Database size={24} color="#2563EB" /></div>
        <div className="data-status-info">
          <div className="data-status-title">\u8cc7\u6599\u4f86\u6e90\u9023\u7dda\u72c0\u614b</div>
          <div className="data-status-meta">\u5df2\u9023\u7dda <strong>{connected}</strong> \u500b / \u5171 <strong>{sources.length}</strong> \u500b\u8cc7\u6599\u8868\uff0c\u7e3d\u8a08 <strong>{totalRecords}</strong> \u7b46\u8cc7\u6599</div>
        </div>
      </div>
      <div className="data-source-tabs">
        <div className={`data-tab ${tab === "status" ? "active" : ""}`} onClick={() => setTab("status")}>\u9023\u7dda\u72c0\u614b</div>
        <div className={`data-tab ${tab === "logs" ? "active" : ""}`} onClick={() => setTab("logs")}>\u539f\u59cb\u65e5\u8a8c\u9810\u89bd</div>
      </div>
      {tab === "status" ? (
        <div className="connector-list">
          {sources.map((s, i) => {
            const Icon = icons[i % icons.length];
            return (<div key={s.name} className="connector-item"><div className="connector-head"><div className="connector-logo"><Icon size={18} /></div><div className="connector-info"><div className="connector-name">{s.name}</div><div className="connector-status">{s.status === "connected" ? <><span className="dot" /> \u5df2\u9023\u7dda</> : <><XCircle size={12} color="#DC2626" /> \u932f\u8aa4</>}</div></div></div><div className="connector-meta">{s.type === "custom" ? "\u81ea\u8a02\u8cc7\u6599\u8868" : "Proxy Table"} {s.count !== undefined ? `/ ${s.count} \u7b46` : ""}</div></div>);
          })}
        </div>
      ) : (
        <div className="panel"><div className="panel-head"><div><div className="panel-title">\u539f\u59cb\u65e5\u8a8c\u9810\u89bd</div><div className="panel-sub">\u6700\u8fd1 {logs.length} \u7b46</div></div></div>
          <table><thead><tr><th>\u65e5\u671f</th><th>\u696d\u52d9\u4eba\u54e1</th><th>\u516c\u53f8\u7c21\u7a31</th><th>\u5de5\u4f5c\u6027\u8cea</th><th>\u5de5\u4f5c\u63cf\u8ff0</th><th>\u72c0\u614b</th></tr></thead>
          <tbody>{logs.slice(0, 20).map((l: any) => { const d = l.data || {}; return (<tr key={l.id}><td>{d.date}</td><td>{d.salesperson}</td><td>{d.company}</td><td>{d.work_nature}</td><td style={{maxWidth:300,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{d.description}</td><td><span className="badge" style={{background:d.status==="analyzed"?"#DCFCE7":"#FEF3C7",color:d.status==="analyzed"?"#16A34A":"#CA8A04"}}>{d.status === "analyzed" ? "\u5df2\u5206\u6790" : "\u5f85\u5206\u6790"}</span></td></tr>); })}</tbody></table>
        </div>
      )}
    </div>
  );
}
'''

# ===========================================================
# 上傳所有檔案
# ===========================================================
all_files = {
    "src/App.css": app_css,
    "src/components/AppLayout.tsx": app_layout_tsx,
    "src/components/AppSidebar.tsx": app_sidebar_tsx,
    "src/pages/DashboardPage.tsx": dashboard_tsx,
    "src/pages/SalesPage.tsx": sales_tsx,
    "src/pages/CategoriesPage.tsx": categories_tsx,
    "src/pages/DataSourcePage.tsx": datasource_tsx,
}

print(f"\n=== 2. 上傳 {len(all_files)} 個 VFS 檔案 ===")
for path in sorted(all_files):
    print(f"  - {path} ({len(all_files[path])} chars)")

r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": all_files}, token)
if r and "_error" not in r:
    print("  上傳成功!")
else:
    print(f"  上傳失敗: {json.dumps(r, ensure_ascii=False)[:300]}")
    exit(1)

# ===========================================================
# 編譯
# ===========================================================
print("\n=== 3. 編譯 ===")
time.sleep(2)
compile_r = api("POST", f"/compile/compile/{SLUG}", None, token)
if compile_r and "_error" not in compile_r:
    success = compile_r.get("success", False)
    errors = compile_r.get("compile_errors", [])
    html = compile_r.get("html", "")
    print(f"  編譯結果: success={success}, errors={len(errors)}, html_len={len(html)}")
    if errors:
        for e in errors[:10]:
            print(f"    [ERROR] {e}")
    if not html and not success:
        print("  警告: 沒有產出 HTML，嘗試重新編譯...")
        time.sleep(3)
        compile_r = api("POST", f"/compile/compile/{SLUG}", None, token)
        success = compile_r.get("success", False)
        errors = compile_r.get("compile_errors", [])
        html = compile_r.get("html", "")
        print(f"  重試結果: success={success}, errors={len(errors)}, html_len={len(html)}")
        if errors:
            for e in errors[:10]:
                print(f"    [ERROR] {e}")
else:
    print(f"  編譯失敗: {json.dumps(compile_r, ensure_ascii=False)[:500]}")
    html = ""

# ===========================================================
# 發佈
# ===========================================================
print("\n=== 4. 發佈 ===")
if html:
    time.sleep(1)
    pub_r = api("POST", f"/builder/apps/{APP}/publish", {"published_assets": {"html": html}}, token)
    if pub_r and "_error" not in pub_r:
        print("  發佈成功!")
    else:
        print(f"  發佈結果: {json.dumps(pub_r, ensure_ascii=False)[:300]}")
else:
    print("  跳過發佈（沒有 HTML 產出）")

# ===========================================================
# 驗證
# ===========================================================
print("\n=== 5. 驗證 VFS ===")
app_final = api("GET", f"/builder/apps/{APP}", None, token)
vfs_final = app_final.get("vfs_state", {})
print(f"  VFS 總檔案數: {len(vfs_final)}")
for path in sorted(vfs_final):
    content = vfs_final[path] or ""
    print(f"    {path}: {len(content)} chars")

# ===========================================================
# E2E 測試
# ===========================================================
print("\n=== 6. E2E 測試 ===")
r = api("POST", f"/actions/apps/{APP}/run/analyze_churn", {"params": {"action": "dashboard", "skip_ai": True}}, token)
if r and "_error" not in r:
    result = r.get("result") or {}
    kpi = result.get("kpi", {})
    print(f"  Dashboard: total_logs={kpi.get('total_logs')}, high_risk={kpi.get('high_risk_customers')}, top_cat={kpi.get('top_category')}")
    print(f"    customers: {len(result.get('customer_ranking', []))}")
else:
    print(f"  Dashboard FAIL: {json.dumps(r, ensure_ascii=False)[:200]}")

r = api("POST", f"/actions/apps/{APP}/run/analyze_churn", {"params": {"action": "sales_analysis", "skip_ai": True}}, token)
if r and "_error" not in r:
    result = r.get("result") or {}
    print(f"  Sales: staff={len(result.get('staff_ranking', []))}")
else:
    print(f"  Sales FAIL: {json.dumps(r, ensure_ascii=False)[:200]}")

r = api("POST", f"/actions/apps/{APP}/run/fetch_crm_data", {"params": {"action": "refs_status"}}, token)
if r and "_error" not in r:
    result = r.get("result") or {}
    sources = result.get("sources", [])
    print(f"  DataSource: {len(sources)} tables")
    for s in sources[:3]:
        print(f"    {s.get('name')}: {s.get('status')} ({s.get('count', '?')})")
else:
    print(f"  DataSource FAIL: {json.dumps(r, ensure_ascii=False)[:200]}")

print("\n===== 部署完成！=====")
print("App URL: https://tslg-churn-analysis-manager.ai-go.app")
