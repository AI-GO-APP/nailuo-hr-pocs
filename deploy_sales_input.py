# -*- coding: utf-8 -*-
"""
業務日誌輸入系統 — 完整部署腳本
App: 45cc5b0c-e669-4876-b3da-b7f96da02404
Slug: da1900f990b0-copy
"""
import json, urllib.request, ssl, time
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "45cc5b0c-e669-4876-b3da-b7f96da02404"
SLUG = "da1900f990b0-copy"

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
print("Login OK")

# ===========================
# VFS 檔案定義
# ===========================

routes_ts = r'''import { PenLine, ClipboardList, Users } from "lucide-react";
export interface RouteItem { title: string; path: string; icon?: any; }
export const routes: RouteItem[] = [
  { title: "填寫業務日誌", path: "/", icon: PenLine },
  { title: "我的歷史日誌", path: "/history", icon: ClipboardList },
  { title: "我的客戶", path: "/customers", icon: Users },
];
'''

app_tsx = r'''import React from "react";
import { HashRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import LogInputPage from "./pages/LogInputPage";
import HistoryPage from "./pages/HistoryPage";
import CustomersPage from "./pages/CustomersPage";

export default function App() {
  return (
    <HashRouter>
      <AppLayout appName="業務工作平台">
        <Routes>
          <Route path="/" element={<LogInputPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/customers" element={<CustomersPage />} />
        </Routes>
      </AppLayout>
    </HashRouter>
  );
}
'''

layout_tsx = r'''import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import AppSidebar from "./AppSidebar";

interface Props { children: React.ReactNode; appName: string; }

const ROUTE_NAMES: Record<string, string> = {
  "/": "填寫業務日誌",
  "/history": "我的歷史日誌",
  "/customers": "我的客戶",
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
            <span>業務工作平台</span>
            <span className="sep">{"\u203a"}</span>
            <span className="current">{currentPage}</span>
          </div>
          <div className="topbar-spacer" />
        </div>
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}
'''

sidebar_tsx = r'''import React, { useState, useEffect } from "react";
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
        <div className="brand-logo green">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </div>
        <div>
          <div className="brand-name">{appName}</div>
          <div className="brand-sub">業務工作平台</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-group-label">日常工作</div>
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
        <div className="user-avatar">{avatar}</div>
        <div className="user-info">
          <div className="user-name">{userName || "使用者"}</div>
          <div className="user-role">{userEmail}</div>
        </div>
      </div>
    </aside>
  );
}
'''

markdown_tsx = r'''import React from "react";
export default function MarkdownText({ text }: { text: string }) {
  if (!text) return null;
  const html = text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
'''

log_input_page = r'''import React, { useState, useEffect, useRef } from "react";
import { runAction } from "../action";

const WORK_NATURES = [
  "訂單追蹤","人脈建立維護","導入進度追蹤","探詢客戶產品資訊",
  "技術規範研討","電話案例追蹤","客戶約訪","異常服務處理",
  "客戶品質會議","Nycron 檢測","報價作業","客戶來廠參觀","舉辦說明會",
];

const EXAMPLES: Record<string, any> = {
  competition: {
    company: "雷堤", nature: "人脈建立維護",
    desc: "和昇源共同拜訪採購簡先生、盧小姐，溝通近期訂單狀況。\n\n關於原本交 GB200 富士康料號，盧小姐表示確定被越南當地廠商切走，因為少了這些數量，預計雷堤每月加工量約在 250 萬上下。\n\n後續動作：持續跟進雷堤訂單情況、配合雷堤交期爭取富士康新料件承認。",
  },
  quality: {
    company: "昆山-仁寶二廠", nature: "異常服務處理",
    desc: "料號 MA00002HIGO M2*0.4*2.5 頭部相連，到現場確認不良率 10%，今日返工庫存 188K，產線庫存 140K。\n\n由於近半年連續發生頭部相連異常，請我方重視並需盡快提供改善報告，後續再發生，將按流程開立罰款單。",
  },
  payment: {
    company: "太倉-文順(更名為金億嘉)", nature: "客戶來廠參觀",
    desc: "實際拜訪太倉-文順\n\n拜訪目的：賬款催收、客戶狀況瞭解\n\n拜訪重點：\n1. 催收貨款，聶總表示，賓科的貨款上個月又沒付，還在跟催。我司貨款盡量本週先用其他客戶付的款支付。",
  },
  normal: {
    company: "泰都分廠", nature: "人脈建立維護",
    desc: "拜訪泰都採購陳小姐、PMC 劉主管，主要是探詢後續化學膠訂單情況與人脈關係維護。\n\n客戶對我司品質、配合滿意，有防鬆需求的點膠螺絲，全部指定發往我司加工。",
  },
};

function categoryClass(cat: string): string {
  const m: Record<string, string> = {"競爭搶單":"competition","品質客訴":"quality","營運下滑":"decline","帳款問題":"payment","關係惡化":"relation","無風險":"normal"};
  return m[cat] || "normal";
}

function riskLabel(r: number): string {
  if (r >= 4) return "極高風險";
  if (r >= 3) return "高風險";
  if (r >= 2) return "中度風險";
  if (r >= 1) return "輕微注意";
  return "無風險";
}

export default function LogInputPage() {
  const [companies, setCompanies] = useState<string[]>([]);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [nature, setNature] = useState("");
  const [company, setCompany] = useState("");
  const [hours, setHours] = useState(2);
  const [desc, setDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [modal, setModal] = useState<any>(null);
  const [formError, setFormError] = useState("");
  const timerRef = useRef<any>(null);

  useEffect(() => {
    runAction("sales_log", { action: "get_options" })
      .then((r: any) => { if (r?.companies) setCompanies(r.companies); })
      .catch(() => {});
  }, []);

  const handleDescChange = (text: string) => {
    setDesc(text);
    clearTimeout(timerRef.current);
    if (text.length < 20) { setPreview(null); return; }
    setPreviewLoading(true);
    timerRef.current = setTimeout(() => {
      runAction("sales_log", { action: "ai_preview", description: text })
        .then((r: any) => { setPreview(r); setPreviewLoading(false); })
        .catch(() => setPreviewLoading(false));
    }, 800);
  };

  const loadExample = (key: string) => {
    const ex = EXAMPLES[key];
    setCompany(ex.company);
    setNature(ex.nature);
    setDesc(ex.desc);
    setPreviewLoading(true);
    runAction("sales_log", { action: "ai_preview", description: ex.desc })
      .then((r: any) => { setPreview(r); setPreviewLoading(false); })
      .catch(() => setPreviewLoading(false));
  };

  const clearForm = () => {
    setCompany(""); setNature(""); setDesc(""); setHours(2);
    setPreview(null); setFormError("");
  };

  const submitLog = () => {
    if (!company || !nature || !desc) {
      setFormError("請填寫完整：客戶、工作性質、工作描述");
      return;
    }
    setFormError("");
    setSubmitting(true);
    runAction("sales_log", { action: "submit_log", company, date, work_nature: nature, hours, description: desc })
      .then((r: any) => {
        setSubmitting(false);
        setModal(r);
      })
      .catch(() => setSubmitting(false));
  };

  const closeModal = (reset?: boolean) => {
    setModal(null);
    if (reset) clearForm();
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">填寫業務日誌</h1>
          <p className="page-subtitle">記錄本次與客戶的互動，AI 將即時判讀風險訊號並提醒主管。</p>
        </div>
      </div>

      <div className="quick-tip">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
        小提醒：請盡量寫清楚客戶的「弦外之音」，例如「客戶提到要評估其他供應商」、「貨款延遲到 X 月底」等具體資訊，AI 才能準確判讀。
      </div>

      <div className="form-card">
        <div className="form-card-head">
          <div className="form-card-title">新增日誌</div>
          <div className="form-card-desc">填寫完成後，AI 會即時分析這筆日誌的風險程度</div>
        </div>
        <div className="form-body">
          <div className="form-row">
            <div className="form-field">
              <label>拜訪日期 <span className="required">*</span></label>
              <input type="date" className="form-input" value={date} onChange={e => setDate(e.target.value)} />
            </div>
            <div className="form-field">
              <label>工作性質 <span className="required">*</span></label>
              <select className="form-select" value={nature} onChange={e => setNature(e.target.value)}>
                <option value="">請選擇</option>
                {WORK_NATURES.map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-field">
              <label>公司簡稱 <span className="required">*</span></label>
              <input type="text" className="form-input" list="company-list" placeholder="輸入或選擇客戶" value={company} onChange={e => setCompany(e.target.value)} />
              <datalist id="company-list">
                {companies.map(c => <option key={c} value={c} />)}
              </datalist>
            </div>
            <div className="form-field">
              <label>使用時間（小時）</label>
              <input type="number" className="form-input" value={hours} min={0} max={24} step={0.5} onChange={e => setHours(Number(e.target.value))} />
            </div>
          </div>
          <div className="form-row full">
            <div className="form-field">
              <label>工作描述 <span className="required">*</span></label>
              <textarea className="form-textarea large" placeholder="詳細描述本次與客戶的互動內容、客戶反饋、議題進展..." value={desc} onChange={e => handleDescChange(e.target.value)} />
              <div className="form-help">提示：可從以下情境快速套用範例（測試 AI 風險判讀效果）</div>
              <div className="examples-row">
                <button className="example-chip" onClick={() => loadExample("competition")}>客戶提到轉單</button>
                <button className="example-chip" onClick={() => loadExample("quality")}>品質客訴</button>
                <button className="example-chip" onClick={() => loadExample("payment")}>帳款延遲</button>
                <button className="example-chip" onClick={() => loadExample("normal")}>正常拜訪</button>
              </div>
            </div>
          </div>

          {(previewLoading || preview) && (
            <div className="ai-preview">
              <div className="ai-preview-icon">AI</div>
              <div className="ai-preview-content">
                <div className="ai-preview-label">AI 即時判讀（初步）</div>
                {previewLoading ? (
                  <div className="ai-preview-text"><span className="spinner"></span><span className="ai-preview-loading">AI 正在閱讀你的日誌...</span></div>
                ) : preview && (
                  <div className="ai-preview-text">
                    <span className={`risk-tag r-${preview.risk_score}`}>Risk {preview.risk_score} · {riskLabel(preview.risk_score)}</span>
                    <span className={`badge cat-${categoryClass(preview.risk_category)}`} style={{marginLeft: 6}}>{preview.risk_category}</span>
                    <div style={{marginTop: 6}}>{preview.reason}</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        <div className="form-actions">
          <div className="form-status">
            {formError ? <span style={{color: "var(--danger)"}}>{formError}</span> : "尚未送出"}
          </div>
          <div style={{display: "flex", gap: 8}}>
            <button className="btn btn-ghost" onClick={clearForm}>清除</button>
            <button className="btn btn-primary btn-lg" onClick={submitLog} disabled={submitting}>
              {submitting ? "送出中..." : "送出日誌"}
            </button>
          </div>
        </div>
      </div>

      {modal && (
        <div className="success-modal-backdrop show" onClick={e => { if (e.target === e.currentTarget) closeModal(); }}>
          <div className="success-modal">
            <div className="success-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <div className="success-title">日誌已送出！</div>
            <div className="success-desc">日誌已即時同步至主管儀表板。AI 已完成判讀：</div>
            <div className="success-ai-card">
              <div className="success-ai-label">AI 判讀結果</div>
              <div style={{display: "flex", gap: 8, margin: "6px 0"}}>
                <span className={`risk-tag r-${modal.risk_score}`}>Risk {modal.risk_score} · {riskLabel(modal.risk_score)}</span>
                <span className={`badge cat-${categoryClass(modal.risk_category)}`}>{modal.risk_category}</span>
              </div>
              <div className="success-ai-text">{modal.ai_reason}</div>
              {modal.risk_score >= 3 && (
                <div style={{marginTop: 10, padding: "8px 10px", background: "rgba(220,38,38,0.1)", borderRadius: 6, fontSize: 12, color: "var(--danger)"}}>
                  主管已收到此風險提醒，並更新「<strong>{company}</strong>」的客戶風險評分。
                </div>
              )}
            </div>
            <div className="success-actions">
              <button className="btn btn-ghost" onClick={() => closeModal()}>關閉</button>
              <button className="btn btn-primary" onClick={() => closeModal(true)}>繼續填寫下一筆</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
'''

history_page = r'''import React, { useState, useEffect } from "react";
import { runAction } from "../action";

function categoryClass(cat: string): string {
  const m: Record<string, string> = {"競爭搶單":"competition","品質客訴":"quality","營運下滑":"decline","帳款問題":"payment","關係惡化":"relation","無風險":"normal"};
  return m[cat] || "normal";
}

export default function HistoryPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [kpi, setKpi] = useState<any>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    runAction("sales_log", { action: "list_logs" })
      .then((r: any) => {
        if (r?.logs) setLogs(r.logs);
        if (r?.kpi) setKpi(r.kpi);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">我的歷史日誌</h1>
          <p className="page-subtitle">你近期送出的業務日誌與 AI 判讀結果</p>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon blue"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
          <div className="kpi-label">日誌總數</div>
          <div className="kpi-value">{kpi.total || 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon red"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg></div>
          <div className="kpi-label">高風險日誌</div>
          <div className="kpi-value">{kpi.high_risk || 0}</div>
          <div className="kpi-meta">主管已關注</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon green"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg></div>
          <div className="kpi-label">正面互動</div>
          <div className="kpi-value">{kpi.positive || 0}</div>
          <div className="kpi-meta">訂單成長/穩定</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon purple"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
          <div className="kpi-label">平均填寫時間</div>
          <div className="kpi-value">1.8<span style={{fontSize: 14, color: "var(--text-2)"}}> 分</span></div>
          <div className="kpi-meta">每筆日誌</div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <div className="panel-title">最近送出</div>
            <div className="panel-sub">{logs.length} 筆</div>
          </div>
        </div>
        {loading ? <div style={{padding: 40, textAlign: "center", color: "var(--text-3)"}}>載入中...</div> : (
          <table>
            <thead>
              <tr><th>日期</th><th>客戶</th><th>工作性質</th><th>摘要</th><th>AI 判讀</th></tr>
            </thead>
            <tbody>
              {logs.map((l, i) => (
                <tr key={i}>
                  <td style={{whiteSpace: "nowrap"}}>{l.date}</td>
                  <td><strong>{l.company}</strong></td>
                  <td style={{color: "var(--text-2)", fontSize: 12}}>{l.work_nature}</td>
                  <td style={{maxWidth: 300, color: "var(--text-2)", fontSize: 12, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"}} title={l.description}>{l.description}</td>
                  <td>
                    <span className={`badge r${l.risk_score}`}>Risk {l.risk_score}</span>
                    <span className={`badge cat-${categoryClass(l.risk_category)}`} style={{marginLeft: 4}}>{l.risk_category}</span>
                  </td>
                </tr>
              ))}
              {logs.length === 0 && <tr><td colSpan={5} style={{textAlign: "center", color: "var(--text-3)", padding: 40}}>尚無日誌紀錄</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
'''

customers_page = r'''import React, { useState, useEffect } from "react";
import { runAction } from "../action";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [highRiskCount, setHighRiskCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    runAction("sales_log", { action: "my_customers" })
      .then((r: any) => {
        if (r?.customers) setCustomers(r.customers);
        if (r?.high_risk_count != null) setHighRiskCount(r.high_risk_count);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">我的客戶</h1>
          <p className="page-subtitle">你負責的客戶與 AI 風險提醒</p>
        </div>
      </div>

      {highRiskCount > 0 && (
        <div className="alert-card">
          <div className="alert-icon">!</div>
          <div className="alert-content">
            <div className="alert-title">AI 為你標記了 {highRiskCount} 個需立即關注的客戶</div>
            <div className="alert-desc">這些客戶的近期日誌出現了流失或品質風險訊號，建議優先安排拜訪或主動聯繫。</div>
          </div>
        </div>
      )}

      <div className="panel">
        <div className="panel-head">
          <div>
            <div className="panel-title">我管轄的客戶</div>
            <div className="panel-sub">共 {customers.length} 個</div>
          </div>
        </div>
        {loading ? <div style={{padding: 40, textAlign: "center", color: "var(--text-3)"}}>載入中...</div> : (
          <table>
            <thead>
              <tr><th>公司簡稱</th><th>本月接觸次數</th><th>最近接觸</th><th>AI 風險</th></tr>
            </thead>
            <tbody>
              {customers.map((c, i) => (
                <tr key={i}>
                  <td><strong>{c.company}</strong></td>
                  <td>{c.visits}</td>
                  <td style={{color: "var(--text-2)", fontSize: 12}}>{c.last_date}</td>
                  <td><span className={`badge r${c.max_risk}`}>Risk {c.max_risk}</span></td>
                </tr>
              ))}
              {customers.length === 0 && <tr><td colSpan={4} style={{textAlign: "center", color: "var(--text-3)", padding: 40}}>尚無客戶資料</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
'''

action_py = r'''import json, re, httpx
from collections import defaultdict

def execute(ctx):
    action = ctx.params.get("action", "get_options")

    if action == "get_options":
        leads = ctx.db.query("crm_leads", limit=500)
        if not isinstance(leads, list): leads = []
        companies = sorted(set(
            l.get("partner_name", "") for l in leads
            if l.get("partner_name")
        ))
        ctx.response.json({"companies": companies})

    elif action == "submit_log":
        desc = ctx.params.get("description", "")
        company = ctx.params.get("company", "")
        date = ctx.params.get("date", "")
        work_nature = ctx.params.get("work_nature", "")
        hours = ctx.params.get("hours", 2)

        ai = _call_ai(ctx, desc)

        teams = ctx.db.query("crm_teams", limit=1)
        stages = ctx.db.query("crm_stages", limit=1)
        team_id = teams[0]["id"] if isinstance(teams, list) and teams else None
        stage_id = stages[0]["id"] if isinstance(stages, list) and stages else None

        record = {
            "name": f"日誌: {company} {date}",
            "partner_name": company,
            "description": desc,
            "date_open": date,
            "type": "opportunity",
            "custom_data": {
                "log_type": "sales_log",
                "work_nature": work_nature,
                "hours": hours,
                "risk_score": ai.get("risk_score", 0),
                "risk_category": ai.get("risk_category", "無風險"),
                "ai_reason": ai.get("reason", ""),
                "status": "analyzed",
            }
        }
        if team_id: record["team_id"] = team_id
        if stage_id: record["stage_id"] = stage_id

        inserted = ctx.db.insert("crm_leads", record)

        ctx.response.json({
            "success": True,
            "risk_score": ai.get("risk_score", 0),
            "risk_category": ai.get("risk_category", "無風險"),
            "ai_reason": ai.get("reason", ""),
        })

    elif action == "list_logs":
        leads = ctx.db.query("crm_leads", limit=500)
        if not isinstance(leads, list): leads = []
        logs = []
        for l in leads:
            cd = l.get("custom_data") or {}
            if cd.get("log_type") != "sales_log": continue
            logs.append({
                "id": l.get("id", ""),
                "date": l.get("date_open", ""),
                "company": l.get("partner_name", ""),
                "work_nature": cd.get("work_nature", ""),
                "description": l.get("description", ""),
                "risk_score": cd.get("risk_score", 0),
                "risk_category": cd.get("risk_category", ""),
                "ai_reason": cd.get("ai_reason", ""),
            })
        logs.sort(key=lambda x: x.get("date", ""), reverse=True)
        total = len(logs)
        high_risk = len([l for l in logs if l.get("risk_score", 0) >= 3])
        positive = len([l for l in logs if l.get("risk_score", 0) <= 1])
        ctx.response.json({"logs": logs, "kpi": {"total": total, "high_risk": high_risk, "positive": positive}})

    elif action == "my_customers":
        leads = ctx.db.query("crm_leads", limit=500)
        if not isinstance(leads, list): leads = []
        cust = defaultdict(lambda: {"visits": 0, "max_risk": 0, "last_date": ""})
        for l in leads:
            cd = l.get("custom_data") or {}
            if cd.get("log_type") != "sales_log": continue
            company = l.get("partner_name", "")
            if not company: continue
            c = cust[company]
            c["visits"] += 1
            rs = cd.get("risk_score", 0)
            if rs > c["max_risk"]: c["max_risk"] = rs
            d = l.get("date_open", "")
            if d > c["last_date"]: c["last_date"] = d
        result = [{"company": n, **c} for n, c in cust.items()]
        result.sort(key=lambda x: -x["max_risk"])
        high_risk_count = len([c for c in result if c["max_risk"] >= 3])
        ctx.response.json({"customers": result, "high_risk_count": high_risk_count})

    elif action == "ai_preview":
        desc = ctx.params.get("description", "")
        ai = _call_ai(ctx, desc)
        ctx.response.json(ai)

    else:
        ctx.response.json({"error": "Unknown action"})

def _call_ai(ctx, description):
    api_key = ctx.secrets.get("OPENAI_API_KEY")
    if not api_key:
        return _fallback_detect(description)
    try:
        prompt = (
            "你是客戶流失風險分析專家。請判讀以下業務日誌的風險。\n\n"
            f"日誌內容：{description}\n\n"
            "請回傳 JSON：{\"risk_score\": 0-4, \"risk_category\": \"分類\", \"reason\": \"說明\"}\n"
            "risk_category 必須是：競爭搶單/品質客訴/營運下滑/帳款問題/關係惡化/無風險\n"
            "只回傳 JSON，不要其他文字。"
        )
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3},
            timeout=30,
        )
        content = resp.json()["choices"][0]["message"]["content"].strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        return json.loads(content)
    except Exception:
        return _fallback_detect(description)

def _fallback_detect(text):
    if not text or len(text) < 20:
        return {"risk_score": 0, "risk_category": "無風險", "reason": "內容過短，無法判讀"}
    if re.search(r'切走|搶單|轉給.{0,5}(別|其他|對手)|流失|被.{0,5}(切|搶)', text):
        return {"risk_score": 4, "risk_category": "競爭搶單", "reason": "偵測到「訂單流失/被切走」訊號"}
    if re.search(r'罰款|不良率|連續.{0,5}異常|退貨|客訴|索賠', text):
        return {"risk_score": 4, "risk_category": "品質客訴", "reason": "偵測到「品質爭議/罰款」訊號"}
    if re.search(r'(貨款|帳款|賬款).{0,5}(未付|沒付|逾期|催)|呆帳', text):
        return {"risk_score": 4, "risk_category": "帳款問題", "reason": "偵測到「貨款延遲」訊號"}
    if re.search(r'(下滑|下降|減量).{0,10}(\d+%|%)', text):
        return {"risk_score": 3, "risk_category": "營運下滑", "reason": "偵測到客戶訂單下滑訊號"}
    if re.search(r'抱怨|不滿|拒絕.{0,5}(降價|配合)|施壓', text):
        return {"risk_score": 3, "risk_category": "關係惡化", "reason": "偵測到客戶關係緊張訊號"}
    return {"risk_score": 1, "risk_category": "無風險", "reason": "未偵測到明顯風險訊號，屬於常規互動"}
'''

manifest_json = '{"actions":[{"name":"sales_log","file":"actions/sales_log.py","description":"業務日誌管理與 AI 風險判讀"}]}'

pages_manifest = '{"/":{\"title\":\"填寫業務日誌\",\"order\":0},\"/history\":{\"title\":\"我的歷史日誌\",\"order\":1},\"/customers\":{\"title\":\"我的客戶\",\"order\":2}}'

# CSS 完整內容（合併舊 App 佈局 + sales-input.html 新元件）
app_css = r''':host, :root {
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
  --text: #0F172A;
  --text-2: #475569;
  --text-3: #94A3B8;
  --border: #E2E8F0;
  --bg: #F8FAFC;
  --bg-card: #FFFFFF;
  --radius: 12px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #root { height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", sans-serif;
  color: var(--text); background: var(--bg); font-size: 14px; line-height: 1.5;
}
button, input, select, textarea { font-family: inherit; }
button { cursor: pointer; border: none; background: none; color: inherit; }

/* ===== App Layout ===== */
.app-layout { display: grid; grid-template-columns: 232px 1fr; min-height: 100vh; }
.app-main { display: flex; flex-direction: column; min-height: 100vh; }
.app-topbar { display: flex; align-items: center; gap: 10px; padding: 14px 32px; border-bottom: 1px solid var(--border); background: white; position: sticky; top: 0; z-index: 5; }
.app-content { flex: 1; overflow-y: auto; }
.collapse-btn { padding: 6px; border-radius: 6px; color: var(--text-2); }
.collapse-btn:hover { background: #F1F5F9; }
.breadcrumb { font-size: 14px; color: var(--text-2); display: flex; align-items: center; gap: 6px; }
.breadcrumb .sep { color: var(--text-3); }
.breadcrumb .current { color: var(--text); font-weight: 500; }
.topbar-spacer { flex: 1; }

/* ===== Sidebar ===== */
.app-sidebar { background: #FFFFFF; border-right: 1px solid var(--border); display: flex; flex-direction: column; position: sticky; top: 0; height: 100vh; overflow-y: auto; transition: width 0.2s; }
.app-sidebar.collapsed { width: 0; overflow: hidden; border: none; }
.sidebar-brand { display: flex; align-items: center; gap: 10px; padding: 16px 18px; border-bottom: 1px solid var(--border); }
.brand-logo { width: 32px; height: 32px; background: linear-gradient(135deg, #2563EB, #7C3AED); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
.brand-logo.green { background: linear-gradient(135deg, #16A34A, #2563EB); }
.brand-name { font-weight: 600; font-size: 15px; }
.brand-sub { font-size: 11px; color: var(--text-3); margin-top: 1px; }
.sidebar-nav { flex: 1; overflow-y: auto; padding: 12px 8px; }
.nav-group-label { font-size: 11px; color: var(--text-3); padding: 14px 12px 6px; font-weight: 500; letter-spacing: 0.5px; }
.sidebar-item { display: flex; align-items: center; gap: 10px; padding: 8px 12px; border-radius: 8px; color: var(--text-2); cursor: pointer; font-size: 14px; margin: 1px 0; width: 100%; text-align: left; background: none; border: none; }
.sidebar-item:hover { background: #F1F5F9; color: var(--text); }
.sidebar-item.active { background: var(--primary-light); color: var(--primary); font-weight: 500; }
.user-card { padding: 12px; margin: 8px; border: 1px solid var(--border); border-radius: 10px; display: flex; align-items: center; gap: 10px; }
.user-avatar { width: 32px; height: 32px; background: linear-gradient(135deg, #16A34A, #2563EB); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px; flex-shrink: 0; }
.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 13px; font-weight: 500; }
.user-role { font-size: 11px; color: var(--text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ===== Page ===== */
.page { padding: 28px 32px; }
.page-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 600; margin-bottom: 4px; }
.page-subtitle { color: var(--text-2); font-size: 14px; }

/* ===== Button ===== */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 10px 16px; border-radius: 8px; font-size: 14px; font-weight: 500; transition: all .15s; }
.btn-primary { background: var(--primary); color: white; }
.btn-primary:hover:not(:disabled) { background: var(--primary-dark); }
.btn-primary:disabled { background: #CBD5E1; cursor: not-allowed; }
.btn-ghost { color: var(--text-2); border: 1px solid var(--border); background: white; }
.btn-ghost:hover { background: var(--bg); color: var(--text); }
.btn-lg { padding: 12px 24px; font-size: 15px; }

/* ===== Form ===== */
.form-card { background: white; border: 1px solid var(--border); border-radius: 12px; max-width: 820px; }
.form-card-head { padding: 20px 24px; border-bottom: 1px solid var(--border); }
.form-card-title { font-size: 16px; font-weight: 600; }
.form-card-desc { font-size: 13px; color: var(--text-2); margin-top: 2px; }
.form-body { padding: 24px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.form-row.full { grid-template-columns: 1fr; }
.form-field label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: var(--text); }
.form-field .required { color: var(--danger); margin-left: 2px; }
.form-input, .form-select, .form-textarea { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; background: white; color: var(--text); transition: border-color 0.15s; }
.form-input:focus, .form-select:focus, .form-textarea:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-light); }
.form-textarea { min-height: 160px; resize: vertical; font-family: inherit; line-height: 1.6; }
.form-textarea.large { min-height: 240px; }
.form-help { font-size: 12px; color: var(--text-3); margin-top: 4px; }
.form-actions { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; border-top: 1px solid var(--border); background: var(--bg); border-radius: 0 0 12px 12px; }
.form-status { font-size: 13px; color: var(--text-2); }

/* ===== AI Preview ===== */
.ai-preview { background: linear-gradient(135deg, #DBEAFE 0%, #EDE9FE 100%); border: 1px solid #93C5FD; border-radius: 10px; padding: 14px 16px; margin-top: 8px; display: flex; gap: 12px; align-items: flex-start; }
.ai-preview-icon { width: 32px; height: 32px; background: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; flex-shrink: 0; color: var(--primary); }
.ai-preview-content { flex: 1; }
.ai-preview-label { font-size: 11px; font-weight: 600; color: var(--primary); margin-bottom: 2px; }
.ai-preview-text { font-size: 13px; color: var(--text); line-height: 1.5; }
.ai-preview-loading { font-size: 13px; color: var(--text-2); font-style: italic; }
.spinner { display: inline-block; width: 12px; height: 12px; border: 2px solid var(--primary-light); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.6s linear infinite; vertical-align: middle; margin-right: 6px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ===== Risk & Badge ===== */
.risk-tag { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 500; }
.risk-tag.r-4 { background: var(--danger); color: white; }
.risk-tag.r-3 { background: var(--warning); color: white; }
.risk-tag.r-2 { background: var(--yellow-light); color: var(--yellow); }
.risk-tag.r-1 { background: #F1F5F9; color: var(--text-2); }
.risk-tag.r-0 { background: var(--success-light); color: var(--success); }
.badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 500; white-space: nowrap; }
.badge.cat-competition { background: var(--danger-light); color: var(--danger); }
.badge.cat-quality { background: var(--warning-light); color: var(--warning); }
.badge.cat-decline { background: var(--purple-light); color: var(--purple); }
.badge.cat-payment { background: var(--yellow-light); color: var(--yellow); }
.badge.cat-relation { background: #FCE7F3; color: #BE185D; }
.badge.cat-normal { background: var(--success-light); color: var(--success); }
.badge.r4 { background: var(--danger); color: white; }
.badge.r3 { background: var(--warning); color: white; }
.badge.r2 { background: var(--yellow-light); color: var(--yellow); }
.badge.r1 { background: #F1F5F9; color: var(--text-2); }
.badge.r0 { background: var(--success-light); color: var(--success); }

/* ===== Success Modal ===== */
.success-modal-backdrop { display: none; position: fixed; inset: 0; background: rgba(15,23,42,0.5); z-index: 50; align-items: center; justify-content: center; animation: fadeIn .2s; }
.success-modal-backdrop.show { display: flex; }
.success-modal { background: white; border-radius: 16px; max-width: 520px; width: 90%; padding: 32px; text-align: center; box-shadow: 0 20px 60px rgba(15,23,42,0.2); }
.success-icon { width: 64px; height: 64px; background: var(--success-light); color: var(--success); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; }
.success-title { font-size: 20px; font-weight: 600; margin-bottom: 8px; }
.success-desc { font-size: 14px; color: var(--text-2); margin-bottom: 20px; line-height: 1.6; }
.success-ai-card { background: linear-gradient(135deg, #DBEAFE 0%, #EDE9FE 100%); border-radius: 12px; padding: 16px; margin-bottom: 20px; text-align: left; }
.success-ai-label { font-size: 11px; font-weight: 600; color: var(--primary); margin-bottom: 4px; }
.success-ai-text { font-size: 14px; line-height: 1.6; }
.success-actions { display: flex; gap: 10px; justify-content: center; }

/* ===== KPI Grid ===== */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.kpi-card { background: white; border: 1px solid var(--border); border-radius: 12px; padding: 18px; }
.kpi-icon { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
.kpi-icon.blue { background: var(--primary-light); color: var(--primary); }
.kpi-icon.green { background: var(--success-light); color: var(--success); }
.kpi-icon.red { background: var(--danger-light); color: var(--danger); }
.kpi-icon.purple { background: var(--purple-light); color: var(--purple); }
.kpi-label { font-size: 12px; color: var(--text-2); margin-bottom: 4px; }
.kpi-value { font-size: 24px; font-weight: 700; line-height: 1.1; }
.kpi-meta { font-size: 11px; color: var(--text-3); margin-top: 4px; }

/* ===== Panel & Table ===== */
.panel { background: white; border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-title { font-size: 16px; font-weight: 600; }
.panel-sub { font-size: 12px; color: var(--text-3); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead th { text-align: left; padding: 12px 14px; font-weight: 500; color: var(--text-2); font-size: 12px; border-bottom: 1px solid var(--border); background: var(--bg); white-space: nowrap; }
tbody td { padding: 14px; border-bottom: 1px solid #F1F5F9; }
tbody tr:hover { background: #FAFBFC; }

/* ===== Alert Card ===== */
.alert-card { background: linear-gradient(135deg, #FEF3C7 0%, #FEE2E2 100%); border: 1px solid #FDE68A; border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; display: flex; gap: 14px; }
.alert-icon { font-size: 20px; font-weight: 700; color: #dc2626; }
.alert-content { flex: 1; }
.alert-title { font-weight: 600; font-size: 14px; color: #92400E; margin-bottom: 4px; }
.alert-desc { font-size: 13px; color: #78350F; line-height: 1.6; }

/* ===== Quick Tip ===== */
.quick-tip { background: var(--primary-light); border-radius: 8px; padding: 10px 14px; margin-bottom: 16px; font-size: 13px; color: var(--primary-dark); display: flex; align-items: center; gap: 8px; }

/* ===== Example Chips ===== */
.examples-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
.example-chip { padding: 4px 10px; background: var(--bg); border: 1px solid var(--border); border-radius: 999px; font-size: 12px; color: var(--text-2); cursor: pointer; transition: all 0.15s; }
.example-chip:hover { background: var(--primary-light); border-color: var(--primary); color: var(--primary); }

/* ===== Animation ===== */
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
'''

# ===========================
# 上傳與部署
# ===========================
print("\n=== Upload files ===")
files = {
    "src/routes.ts": routes_ts,
    "src/App.tsx": app_tsx,
    "src/App.css": app_css,
    "src/components/AppLayout.tsx": layout_tsx,
    "src/components/AppSidebar.tsx": sidebar_tsx,
    "src/components/MarkdownText.tsx": markdown_tsx,
    "src/pages/LogInputPage.tsx": log_input_page,
    "src/pages/HistoryPage.tsx": history_page,
    "src/pages/CustomersPage.tsx": customers_page,
    "src/pages/_manifest.json": pages_manifest,
    "actions/sales_log.py": action_py,
    "actions/manifest.json": manifest_json,
    # 刪除舊頁面（設為空）
    "src/pages/DashboardPage.tsx": "",
    "src/pages/SalesPage.tsx": "",
    "src/pages/CategoriesPage.tsx": "",
    "src/pages/DataSourcePage.tsx": "",
    "src/pages/NotFoundPage.tsx": "",
    "src/components/AILoadingSkeleton.tsx": "",
}

r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": files}, token)
print("Upload:", "OK" if r and "_error" not in r else "FAIL: " + str(r)[:300])

# Publish
print("\n=== Publish ===")
r = api("POST", f"/builder/apps/{APP}/publish",
    {"published_assets": {"html": "", "bundle_js": "", "css": ""}}, token)
print("Publish:", "OK" if r and "_error" not in r else "FAIL")

# Verify
time.sleep(1)
print("\n=== Verify ===")
app = api("GET", f"/builder/apps/{APP}", None, token)
pvfs = app.get("published_vfs") or {}
print("published_vfs files:", len(pvfs))
for f in sorted(pvfs.keys()):
    c = pvfs.get(f, "") or ""
    print("  %s: %d chars" % (f, len(c)))

# Check key content
print("\nKey checks:")
css = pvfs.get("src/App.css", "")
print("  CSS has ':host, :root':", ":host, :root" in css)
print("  CSS has 'form-card':", "form-card" in css)
apptsx = pvfs.get("src/App.tsx", "")
print("  App.tsx has 'HashRouter':", "HashRouter" in apptsx)
print("  App.tsx has 'LogInputPage':", "LogInputPage" in apptsx)
layout = pvfs.get("src/components/AppLayout.tsx", "")
print("  Layout has 'children':", "children" in layout)
print("  Layout has 'Outlet':", "Outlet" in layout, "(should be False)")
action = pvfs.get("actions/sales_log.py", "")
print("  Action has 'httpx':", "httpx" in action)
print("  Action has 'ssl':", "import ssl" in action, "(should be False)")

# Compile
time.sleep(1)
print("\n=== Compile ===")
c = api("POST", f"/compile/compile/{SLUG}", None, token)
print("Success:", c.get("success"))
for e in c.get("compile_errors", []):
    print("  ERROR:", json.dumps(e, ensure_ascii=False)[:200])

print("\n===== DONE =====")
