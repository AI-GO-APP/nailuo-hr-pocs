# -*- coding: utf-8 -*-
"""
Phase 2 & 3: 前端全部檔案建置 + 編譯 + 發佈
建立所有 VFS 檔案並上傳到 AI GO
"""
import json, urllib.request, ssl, time
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
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# ==========================================
# 取得現有 VFS
# ==========================================
app_data = api("GET", f"/builder/apps/{APP}", None, token)
slug = app_data.get("slug", "")
vfs = app_data.get("vfs_state", {})
print(f"App slug: {slug}")
print(f"Current files: {len(vfs)}")

# ==========================================
# 定義所有新檔案
# ==========================================
files = {}

# --- routes.ts ---
files["src/routes.ts"] = '''import { LayoutDashboard, Users, Layers, Database } from "lucide-react";

export interface RouteItem {
  title: string;
  path: string;
  icon?: any;
  children?: RouteItem[];
}

export const routes: RouteItem[] = [
  { title: "\\u98a8\\u96aa\\u7e3d\\u89bd", path: "/", icon: LayoutDashboard },
  { title: "\\u696d\\u52d9\\u5206\\u6790", path: "/sales", icon: Users },
  { title: "\\u98a8\\u96aa\\u985e\\u5225", path: "/categories", icon: Layers },
  { title: "\\u8cc7\\u6599\\u4f86\\u6e90", path: "/datasource", icon: Database },
];
'''

# --- App.tsx ---
files["src/App.tsx"] = '''import { HashRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import AppLayout from "./components/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import SalesPage from "./pages/SalesPage";
import CategoriesPage from "./pages/CategoriesPage";
import DataSourcePage from "./pages/DataSourcePage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <>
      <Toaster position="top-right" />
      <HashRouter>
        <AppLayout appName="\\u5ba2\\u6236\\u6d41\\u5931\\u98a8\\u96aa\\u5206\\u6790">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/sales" element={<SalesPage />} />
            <Route path="/categories" element={<CategoriesPage />} />
            <Route path="/datasource" element={<DataSourcePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AppLayout>
      </HashRouter>
    </>
  );
}
'''

# --- DashboardPage.tsx ---
files["src/pages/DashboardPage.tsx"] = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { FileText, AlertTriangle, Clock, Star, RefreshCw, Loader2, Brain } from "lucide-react";

/* 風險 badge */
function RiskBadge({ score }: { score: number }) {
  const cls = score >= 4 ? "risk-4" : score >= 3 ? "risk-3" : score >= 2 ? "risk-2" : "risk-1";
  const label = score >= 4 ? "極高" : score >= 3 ? "高" : score >= 2 ? "中" : "低";
  return <span className={`badge ${cls}`}>{label} ({score})</span>;
}

function CatBadge({ cat }: { cat: string }) {
  const map: Record<string, string> = {
    "競爭搶單": "cat-competition", "品質客訴": "cat-quality",
    "營運下滑": "cat-decline", "帳款問題": "cat-payment", "關係惡化": "cat-relation",
  };
  return <span className={`badge ${map[cat] || ""}`}>{cat}</span>;
}

/* 橫條圖 */
function BarChart({ data }: { data: { name: string; count: number }[] }) {
  const max = Math.max(...data.map(d => d.count), 1);
  const colors = ["#DC2626", "#EA580C", "#7C3AED", "#CA8A04", "#BE185D"];
  return (
    <div className="bar-chart">
      {data.map((d, i) => (
        <div key={d.name} className="bar-row">
          <div className="bar-label">{d.name}</div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(d.count / max) * 100}%`, background: colors[i % colors.length] }} />
          </div>
          <div className="bar-value">{d.count}</div>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiInsight, setAiInsight] = useState("");
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "dashboard", skip_ai: true });
      setData(r);
    } catch (e: any) {
      console.error(e);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const loadAI = async () => {
    setAiLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "dashboard", skip_ai: false });
      setAiInsight(r.ai_insight || "");
    } catch (e: any) {
      setAiInsight("AI 分析失敗: " + (e.message || ""));
    }
    setAiLoading(false);
  };

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /><p style={{marginTop:12,color:"#64748B"}}>載入中...</p></div>;
  if (!data) return <div className="page"><p>無資料</p></div>;

  const kpi = data.kpi || {};
  const customers = (data.customer_ranking || []).filter((c: any) =>
    !search || c.company?.includes(search) || c.salesperson?.includes(search)
  );

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">風險總覽</h1>
          <p className="page-subtitle">業務日誌 AI 風險判讀結果彙整</p>
        </div>
        <div style={{display:"flex",gap:8}}>
          <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> 更新</button>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon blue"><FileText size={18} /></div>
          <div className="kpi-label">分析日誌總數</div>
          <div className="kpi-value">{kpi.total_logs || 0}</div>
        </div>
        <div className="kpi-card danger">
          <div className="kpi-icon red"><AlertTriangle size={18} /></div>
          <div className="kpi-label">高風險客戶</div>
          <div className="kpi-value">{kpi.high_risk_customers || 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon orange"><Clock size={18} /></div>
          <div className="kpi-label">高風險日誌</div>
          <div className="kpi-value">{kpi.high_risk_logs || 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon purple"><Star size={18} /></div>
          <div className="kpi-label">主要風險類型</div>
          <div className="kpi-value" style={{fontSize:20}}>{kpi.top_category || "-"}</div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-title">客戶風險排名</div>
              <div className="panel-sub">依最高風險分數排序</div>
            </div>
          </div>
          <div className="search-row">
            <input className="search-input" placeholder="搜尋公司、業務..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <table>
            <thead><tr>
              <th>公司簡稱</th><th>業務人員</th><th>等級</th>
              <th>接觸次數</th><th>最高風險</th><th>高風險日誌</th><th>主要風險類別</th>
            </tr></thead>
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
            <div className="panel-head">
              <div><div className="panel-title">風險類別分布</div></div>
            </div>
            <BarChart data={data.category_distribution || []} />
          </div>

          <div className="panel">
            <div className="panel-head">
              <div>
                <div className="panel-title">最該關注的 5 個客戶</div>
                <div className="panel-sub">依風險分數排序</div>
              </div>
            </div>
            <div className="top-list">
              {(data.top5_customers || []).map((c: any, i: number) => (
                <div key={c.company} className="top-item">
                  <div className="top-rank">{i + 1}</div>
                  <div className="top-content">
                    <div className="top-name">{c.company}</div>
                    <div className="top-reason">{c.salesperson} - {c.main_category}</div>
                  </div>
                  <div className="top-score">Risk {c.max_risk}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-head">
              <div><div className="panel-title">AI 洞察</div></div>
              <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>
                {aiLoading ? <><Loader2 size={14} className="spin" /> 分析中...</> : <><Brain size={14} /> 產生洞察</>}
              </button>
            </div>
            {aiInsight ? (
              <div className="ai-reason-box">
                <div className="ai-icon" style={{fontSize:14,fontWeight:700,color:"var(--primary)"}}>AI</div>
                <div className="ai-reason-content">
                  <div className="ai-reason-label">AI 主管洞察</div>
                  <div className="ai-reason-text" style={{whiteSpace:"pre-line"}}>{aiInsight}</div>
                </div>
              </div>
            ) : !aiLoading ? (
              <p style={{color:"#94A3B8",fontSize:13,textAlign:"center",padding:16}}>點擊上方按鈕產生 AI 洞察</p>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
'''

# --- SalesPage.tsx ---
files["src/pages/SalesPage.tsx"] = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Users, AlertTriangle, Flame, UserCheck, RefreshCw, Loader2, Brain } from "lucide-react";

/* SVG 象限圖 */
function QuadrantChart({ data }: { data: any[] }) {
  const W = 500, H = 340;
  const pad = { top: 30, right: 30, bottom: 40, left: 50 };
  const innerW = W - pad.left - pad.right;
  const innerH = H - pad.top - pad.bottom;
  const maxX = Math.max(...data.map(d => d.x), 15);
  const maxY = Math.max(...data.map(d => d.y), 4);
  const midX = maxX / 2, midY = maxY / 2;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{width:"100%",height:"auto"}}>
      {/* 軸 */}
      <line x1={pad.left} y1={H - pad.bottom} x2={W - pad.right} y2={H - pad.bottom} stroke="#E2E8F0" strokeWidth={1} />
      <line x1={pad.left} y1={pad.top} x2={pad.left} y2={H - pad.bottom} stroke="#E2E8F0" strokeWidth={1} />
      {/* 中線 */}
      <line x1={pad.left + innerW * (midX / maxX)} y1={pad.top} x2={pad.left + innerW * (midX / maxX)} y2={H - pad.bottom} stroke="#E2E8F0" strokeDasharray="4" />
      <line x1={pad.left} y1={pad.top + innerH * (1 - midY / maxY)} x2={W - pad.right} y2={pad.top + innerH * (1 - midY / maxY)} stroke="#E2E8F0" strokeDasharray="4" />
      {/* 標籤 */}
      <text x={W - pad.right - 10} y={pad.top + 15} textAnchor="end" fontSize={11} fill="#94A3B8">救火型</text>
      <text x={pad.left + 10} y={pad.top + 15} textAnchor="start" fontSize={11} fill="#94A3B8">失聯型</text>
      <text x={W - pad.right - 10} y={H - pad.bottom - 8} textAnchor="end" fontSize={11} fill="#94A3B8">穩定型</text>
      <text x={pad.left + 5} y={H - pad.bottom + 30} fontSize={11} fill="#94A3B8">拜訪次數</text>
      <text x={pad.left - 35} y={pad.top + innerH / 2} fontSize={11} fill="#94A3B8" transform={`rotate(-90,${pad.left - 35},${pad.top + innerH / 2})`}>平均風險</text>
      {/* 點 */}
      {data.map((d, i) => {
        const cx = pad.left + (d.x / maxX) * innerW;
        const cy = pad.top + (1 - d.y / maxY) * innerH;
        const r = Math.max(8, Math.min(20, d.size * 4));
        const color = d.y > midY ? (d.x > midX ? "#DC2626" : "#CA8A04") : (d.x > midX ? "#16A34A" : "#94A3B8");
        return (
          <g key={i}>
            <circle cx={cx} cy={cy} r={r} fill={color} opacity={0.7} stroke="white" strokeWidth={2} />
            <text x={cx} y={cy - r - 4} textAnchor="middle" fontSize={10} fill="#0F172A">{d.name}</text>
          </g>
        );
      })}
    </svg>
  );
}

export default function SalesPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiInsight, setAiInsight] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "sales_analysis", skip_ai: true });
      setData(r);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const loadAI = async () => {
    setAiLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "sales_analysis", skip_ai: false });
      setAiInsight(r.ai_insight || "");
    } catch (e: any) { setAiInsight("AI 分析失敗: " + (e.message || "")); }
    setAiLoading(false);
  };

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /></div>;
  if (!data) return <div className="page"><p>無資料</p></div>;

  const kpi = data.kpi || {};

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">業務分析</h1>
          <p className="page-subtitle">從業務角度看：誰的客戶最該關注、誰可能不擅於維繫客戶關係</p>
        </div>
        <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> 更新</button>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon teal"><Users size={18} /></div>
          <div className="kpi-label">分析業務人員</div>
          <div className="kpi-value">{kpi.total_staff || 0}</div>
        </div>
        <div className="kpi-card danger">
          <div className="kpi-icon red"><AlertTriangle size={18} /></div>
          <div className="kpi-label">高風險客戶集中業務</div>
          <div className="kpi-value">{kpi.concentrated_risk || 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon orange"><Flame size={18} /></div>
          <div className="kpi-label">救火型業務</div>
          <div className="kpi-value">{kpi.firefighter || 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-icon blue"><UserCheck size={18} /></div>
          <div className="kpi-label">客戶被多人拜訪</div>
          <div className="kpi-value">{kpi.multi_visit || 0}</div>
        </div>
      </div>

      <div className="sales-grid">
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">業務人員風險地圖</div><div className="panel-sub">X: 拜訪次數 / Y: 平均風險 / 大小: 客戶數</div></div></div>
          <QuadrantChart data={data.quadrant_data || []} />
        </div>
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">業務人員風險排名</div></div></div>
          <table>
            <thead><tr><th>業務人員</th><th>管轄客戶</th><th>高風險</th><th>拜訪次數</th><th>平均風險</th></tr></thead>
            <tbody>
              {(data.staff_ranking || []).map((s: any) => (
                <tr key={s.name}>
                  <td style={{fontWeight:500}}>{s.name}</td>
                  <td>{s.customer_count}</td>
                  <td className={`score-cell ${s.high_risk_count > 0 ? "high" : ""}`}>{s.high_risk_count}</td>
                  <td>{s.visits}</td>
                  <td>{s.avg_risk}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel" style={{marginTop:16}}>
        <div className="panel-head">
          <div><div className="panel-title">AI 洞察</div></div>
          <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>
            {aiLoading ? <><Loader2 size={14} className="spin" /> 分析中...</> : <><Brain size={14} /> 產生洞察</>}
          </button>
        </div>
        {aiInsight ? (
          <div className="ai-reason-box">
            <div className="ai-icon" style={{fontSize:14,fontWeight:700,color:"var(--primary)"}}>AI</div>
            <div className="ai-reason-content">
              <div className="ai-reason-label">AI 業務分析</div>
              <div className="ai-reason-text" style={{whiteSpace:"pre-line"}}>{aiInsight}</div>
            </div>
          </div>
        ) : !aiLoading ? (
          <p style={{color:"#94A3B8",fontSize:13,textAlign:"center",padding:16}}>點擊上方按鈕產生 AI 洞察</p>
        ) : null}
      </div>
    </div>
  );
}
'''

# --- CategoriesPage.tsx ---
files["src/pages/CategoriesPage.tsx"] = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Loader2, Brain, Swords, Wrench, TrendingDown, Wallet, HeartCrack } from "lucide-react";

const CATEGORIES = [
  { id: "競爭搶單", label: "競爭搶單", color: "#DC2626", bg: "#FEE2E2", icon: Swords },
  { id: "品質客訴", label: "品質客訴", color: "#EA580C", bg: "#FFEDD5", icon: Wrench },
  { id: "營運下滑", label: "營運下滑", color: "#7C3AED", bg: "#EDE9FE", icon: TrendingDown },
  { id: "帳款問題", label: "帳款問題", color: "#CA8A04", bg: "#FEF3C7", icon: Wallet },
  { id: "關係惡化", label: "關係惡化", color: "#BE185D", bg: "#FCE7F3", icon: HeartCrack },
];

export default function CategoriesPage() {
  const [active, setActive] = useState(CATEGORIES[0].id);
  const [detail, setDetail] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiInsight, setAiInsight] = useState("");
  const [counts, setCounts] = useState<Record<string, number>>({});

  const loadCounts = useCallback(async () => {
    try {
      const r = await runAction("analyze_churn", { action: "dashboard", skip_ai: true });
      const dist = r.category_distribution || [];
      const map: Record<string, number> = {};
      dist.forEach((d: any) => { map[d.name] = d.count; });
      setCounts(map);
    } catch {}
  }, []);

  useEffect(() => { loadCounts(); }, [loadCounts]);

  const loadDetail = useCallback(async (cat: string) => {
    setLoading(true);
    setAiInsight("");
    try {
      const r = await runAction("analyze_churn", { action: "category_detail", category: cat, skip_ai: true });
      setDetail(r);
    } catch { setDetail(null); }
    setLoading(false);
  }, []);

  useEffect(() => { loadDetail(active); }, [active, loadDetail]);

  const loadAI = async () => {
    setAiLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "category_detail", category: active, skip_ai: false });
      setAiInsight(r.ai_insight || "");
    } catch (e: any) { setAiInsight("AI 分析失敗"); }
    setAiLoading(false);
  };

  const activeCat = CATEGORIES.find(c => c.id === active)!;

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">風險類別分析</h1>
          <p className="page-subtitle">五大流失風險類別深度解析</p>
        </div>
      </div>

      <div className="cat-tabs">
        {CATEGORIES.map(cat => {
          const Icon = cat.icon;
          return (
            <div key={cat.id} className={`cat-tab ${active === cat.id ? "active" : ""}`}
              style={active === cat.id ? {borderColor: cat.color, color: cat.color} : {}}
              onClick={() => setActive(cat.id)}>
              <div className="cat-tab-icon"><Icon size={22} color={cat.color} /></div>
              <div className="cat-tab-content">
                <div className="cat-tab-name">{cat.label}</div>
                <div className="cat-tab-stat">{counts[cat.id] || 0} 筆日誌</div>
              </div>
              <div className="cat-tab-value" style={{color: cat.color}}>{counts[cat.id] || 0}</div>
            </div>
          );
        })}
      </div>

      {loading ? (
        <div style={{textAlign:"center",padding:60}}><Loader2 className="spin" size={32} /></div>
      ) : detail ? (
        <>
          <div className="cat-summary-card" style={{background:`linear-gradient(135deg, ${activeCat.color}, ${activeCat.color}dd)`,marginBottom:16}}>
            <div className="cat-summary-name">{activeCat.label}</div>
            <div className="cat-summary-desc">共 {detail.total_logs} 筆日誌，影響 {detail.total_customers} 個客戶</div>
            <div className="cat-summary-stats">
              <div><div className="cat-summary-stat-label">日誌數</div><div className="cat-summary-stat-value">{detail.total_logs}</div></div>
              <div><div className="cat-summary-stat-label">客戶數</div><div className="cat-summary-stat-value">{detail.total_customers}</div></div>
            </div>
          </div>

          <div className="cat-detail-grid">
            <div className="panel">
              <div className="panel-head"><div><div className="panel-title">此類別 Top 客戶</div></div></div>
              {(detail.top_customers || []).map((c: any, i: number) => (
                <div key={c.company} className="cat-customer-card">
                  <div className="cat-customer-rank" style={{background: activeCat.color}}>{i + 1}</div>
                  <div className="cat-customer-info">
                    <div className="cat-customer-name">{c.company}</div>
                    <div className="cat-customer-reason">{c.count} 筆相關日誌</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="panel">
              <div className="panel-head"><div><div className="panel-title">此類別影響業務</div></div></div>
              {(detail.top_staff || []).map((s: any, i: number) => (
                <div key={s.name} className="cat-customer-card">
                  <div className="cat-customer-rank" style={{background: "#475569"}}>{i + 1}</div>
                  <div className="cat-customer-info">
                    <div className="cat-customer-name">{s.name}</div>
                    <div className="cat-customer-reason">{s.count} 筆相關日誌</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-head">
              <div><div className="panel-title">AI 洞察 - {activeCat.label}</div></div>
              <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>
                {aiLoading ? <><Loader2 size={14} className="spin" /> 分析中...</> : <><Brain size={14} /> 產生洞察</>}
              </button>
            </div>
            {aiInsight ? (
              <div className="ai-reason-box">
                <div className="ai-icon" style={{fontSize:14,fontWeight:700,color:"var(--primary)"}}>AI</div>
                <div className="ai-reason-content">
                  <div className="ai-reason-label">AI 類別深度分析</div>
                  <div className="ai-reason-text" style={{whiteSpace:"pre-line"}}>{aiInsight}</div>
                </div>
              </div>
            ) : !aiLoading ? (
              <p style={{color:"#94A3B8",fontSize:13,textAlign:"center",padding:16}}>點擊上方按鈕產生 AI 洞察</p>
            ) : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
'''

# --- DataSourcePage.tsx ---
files["src/pages/DataSourcePage.tsx"] = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Database, Loader2, RefreshCw, CheckCircle, XCircle, Link2, FileText, BarChart3 } from "lucide-react";

export default function DataSourcePage() {
  const [sources, setSources] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"status" | "logs">("status");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await runAction("fetch_crm_data", { action: "refs_status" });
      setSources(r.sources || []);
      const r2 = await runAction("fetch_crm_data", { action: "raw_logs" });
      setLogs(r2.logs || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /></div>;

  const connected = sources.filter(s => s.status === "connected").length;
  const connectorIcons = [Link2, FileText, BarChart3];

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">資料來源</h1>
          <p className="page-subtitle">管理 CRM/ERP 資料連線與原始日誌</p>
        </div>
        <button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> 更新</button>
      </div>

      <div className="data-status-card">
        <div className="data-status-icon"><Database size={24} color="#2563EB" /></div>
        <div className="data-status-info">
          <div className="data-status-title">資料來源連線狀態</div>
          <div className="data-status-meta">已連線 <strong>{connected}</strong> 個資料表 / 共 <strong>{sources.length}</strong> 個</div>
        </div>
      </div>

      <div className="data-source-tabs">
        <div className={`data-tab ${tab === "status" ? "active" : ""}`} onClick={() => setTab("status")}>連線狀態</div>
        <div className={`data-tab ${tab === "logs" ? "active" : ""}`} onClick={() => setTab("logs")}>原始日誌預覽</div>
      </div>

      {tab === "status" ? (
        <div className="connector-list">
          {sources.map((s, i) => {
            const Icon = connectorIcons[i % connectorIcons.length];
            return (
              <div key={s.name} className="connector-item">
                <div className="connector-head">
                  <div className="connector-logo"><Icon size={18} /></div>
                  <div className="connector-info">
                    <div className="connector-name">{s.name}</div>
                    <div className="connector-status">
                      {s.status === "connected" ? <><span className="dot" /> 已連線</> : <><XCircle size={12} color="#DC2626" /> 錯誤</>}
                    </div>
                  </div>
                </div>
                <div className="connector-meta">{s.type === "custom" ? "自訂資料表" : "Proxy Table"} {s.count !== undefined ? `/ ${s.count} 筆` : ""}</div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">原始日誌預覽</div><div className="panel-sub">最近 {logs.length} 筆</div></div></div>
          <table>
            <thead><tr><th>日期</th><th>業務人員</th><th>公司簡稱</th><th>工作性質</th><th>工作描述</th><th>狀態</th></tr></thead>
            <tbody>
              {logs.slice(0, 20).map((l: any) => {
                const d = l.data || {};
                return (
                  <tr key={l.id}>
                    <td>{d.date}</td>
                    <td>{d.salesperson}</td>
                    <td>{d.company}</td>
                    <td>{d.work_nature}</td>
                    <td style={{maxWidth:300,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{d.description}</td>
                    <td><span className="badge" style={{background:d.status==="analyzed"?"#DCFCE7":"#FEF3C7",color:d.status==="analyzed"?"#16A34A":"#CA8A04"}}>{d.status === "analyzed" ? "已分析" : "待分析"}</span></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
'''

# --- NotFoundPage.tsx ---
files["src/pages/NotFoundPage.tsx"] = '''import { useNavigate } from "react-router-dom";
import { Home } from "lucide-react";

export default function NotFoundPage() {
  const nav = useNavigate();
  return (
    <div className="page" style={{textAlign:"center",padding:"80px 0"}}>
      <h1 style={{fontSize:64,fontWeight:700,color:"#E2E8F0",marginBottom:8}}>404</h1>
      <p style={{color:"#64748B",marginBottom:24}}>頁面不存在</p>
      <button className="btn btn-primary" onClick={() => nav("/")}><Home size={14} /> 回首頁</button>
    </div>
  );
}
'''

# --- App.css (白底清爽風格，移植 manager-dashboard 核心 CSS) ---
files["src/App.css"] = ''':root {
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
  --text: #0F172A;
  --text-2: #475569;
  --text-3: #94A3B8;
  --border: #E2E8F0;
  --bg: #F8FAFC;
  --bg-card: #FFFFFF;
}

/* KPI */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.kpi-card { background: white; border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
.kpi-icon { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; }
.kpi-icon.blue { background: var(--primary-light); color: var(--primary); }
.kpi-icon.red { background: var(--danger-light); color: var(--danger); }
.kpi-icon.orange { background: var(--warning-light); color: var(--warning); }
.kpi-icon.purple { background: var(--purple-light); color: var(--purple); }
.kpi-icon.teal { background: var(--teal-light); color: var(--teal); }
.kpi-label { font-size: 13px; color: var(--text-2); margin-bottom: 6px; }
.kpi-value { font-size: 28px; font-weight: 700; line-height: 1.1; }
.kpi-card.danger .kpi-value { color: var(--danger); }

/* Dashboard grid */
.dashboard-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
.panel { background: white; border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
.panel-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 10px; }
.panel-title { font-size: 16px; font-weight: 600; }
.panel-sub { font-size: 12px; color: var(--text-3); margin-top: 2px; }

/* Page */
.page { padding: 28px 32px; }
.page-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; gap: 20px; }
.page-title { font-size: 24px; font-weight: 600; margin-bottom: 4px; }
.page-subtitle { color: var(--text-2); font-size: 14px; }

/* Buttons */
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 9px 14px; border-radius: 8px; font-size: 13px; font-weight: 500; transition: all .15s; cursor: pointer; border: none; }
.btn-primary { background: var(--primary); color: white; }
.btn-primary:hover:not(:disabled) { background: var(--primary-dark); }
.btn-primary:disabled { background: #CBD5E1; cursor: not-allowed; }
.btn-ghost { color: var(--text-2); border: 1px solid var(--border); background: white; }
.btn-ghost:hover { background: var(--bg); color: var(--text); }

/* Search */
.search-row { margin-bottom: 14px; display: flex; gap: 10px; }
.search-input { flex: 1; padding: 9px 14px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; background: var(--bg); }
.search-input:focus { outline: none; border-color: var(--primary); background: white; }

/* Table */
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead th { text-align: left; padding: 12px 14px; font-weight: 500; color: var(--text-2); font-size: 12px; border-bottom: 1px solid var(--border); background: var(--bg); white-space: nowrap; }
tbody td { padding: 14px; border-bottom: 1px solid #F1F5F9; }
tbody tr:hover { background: #FAFBFC; }
.company-cell { display: flex; align-items: center; gap: 8px; font-weight: 500; }

/* Badge */
.badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 500; white-space: nowrap; }
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
.score-cell { font-weight: 600; font-size: 14px; }
.score-cell.high { color: var(--danger); }

/* Bar chart */
.bar-chart { padding: 4px 0; }
.bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; font-size: 13px; }
.bar-label { width: 96px; color: var(--text-2); flex-shrink: 0; }
.bar-track { flex: 1; height: 22px; background: var(--bg); border-radius: 4px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
.bar-value { width: 40px; text-align: right; font-weight: 600; flex-shrink: 0; }

/* Top list */
.top-list { margin-top: 8px; }
.top-item { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 8px; cursor: pointer; transition: background .15s; }
.top-item:hover { background: var(--danger-light); }
.top-rank { width: 24px; height: 24px; background: var(--danger); color: white; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.top-content { flex: 1; min-width: 0; }
.top-name { font-weight: 500; font-size: 13px; }
.top-reason { font-size: 11px; color: var(--text-2); }
.top-score { font-size: 13px; font-weight: 700; color: var(--danger); }

/* AI */
.ai-reason-box { background: linear-gradient(135deg, #DBEAFE 0%, #EDE9FE 100%); border-radius: 10px; padding: 14px 16px; display: flex; gap: 12px; align-items: flex-start; }
.ai-icon { width: 32px; height: 32px; flex-shrink: 0; background: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.ai-reason-content { flex: 1; }
.ai-reason-label { font-size: 11px; font-weight: 600; color: var(--primary); letter-spacing: 0.3px; margin-bottom: 2px; }
.ai-reason-text { font-size: 14px; font-weight: 500; color: var(--text); line-height: 1.5; }

/* Sales */
.sales-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; margin-bottom: 16px; }

/* Categories */
.cat-tabs { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
.cat-tab { display: flex; align-items: center; gap: 10px; padding: 14px 18px; border: 2px solid var(--border); border-radius: 12px; background: white; cursor: pointer; transition: all 0.15s; flex: 1; min-width: 160px; }
.cat-tab:hover { border-color: var(--text-3); }
.cat-tab.active { box-shadow: 0 4px 12px rgba(15,23,42,0.08); }
.cat-tab-content { flex: 1; min-width: 0; text-align: left; }
.cat-tab-name { font-weight: 600; font-size: 13px; }
.cat-tab-stat { font-size: 11px; color: var(--text-3); margin-top: 2px; }
.cat-tab-value { font-size: 20px; font-weight: 700; }

.cat-summary-card { border-radius: 12px; padding: 22px 24px; color: white; position: relative; overflow: hidden; }
.cat-summary-name { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
.cat-summary-desc { font-size: 13px; opacity: 0.9; line-height: 1.6; margin-bottom: 16px; }
.cat-summary-stats { display: flex; gap: 24px; }
.cat-summary-stat-label { font-size: 11px; opacity: 0.8; }
.cat-summary-stat-value { font-size: 22px; font-weight: 700; }
.cat-detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.cat-customer-card { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border: 1px solid var(--border); border-radius: 10px; margin-bottom: 8px; cursor: pointer; transition: all 0.15s; }
.cat-customer-card:hover { border-color: var(--primary); background: var(--primary-light); }
.cat-customer-rank { width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; color: white; flex-shrink: 0; }
.cat-customer-info { flex: 1; }
.cat-customer-name { font-weight: 600; font-size: 13px; }
.cat-customer-reason { font-size: 11px; color: var(--text-2); margin-top: 2px; }

/* Data source */
.data-status-card { background: linear-gradient(135deg, #DBEAFE 0%, #EDE9FE 100%); border: 1px solid var(--primary-light); border-radius: 12px; padding: 20px; margin-bottom: 24px; display: flex; align-items: center; gap: 20px; }
.data-status-icon { width: 56px; height: 56px; background: white; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.data-status-info { flex: 1; }
.data-status-title { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.data-status-meta { font-size: 13px; color: var(--text-2); }
.data-status-meta strong { color: var(--text); }
.data-source-tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 1px solid var(--border); }
.data-tab { padding: 10px 16px; font-size: 14px; color: var(--text-2); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; }
.data-tab.active { color: var(--primary); border-bottom-color: var(--primary); font-weight: 500; }
.connector-list { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
.connector-item { padding: 14px; border: 1px solid var(--border); border-radius: 10px; background: white; }
.connector-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.connector-logo { width: 36px; height: 36px; background: var(--bg); border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.connector-info { flex: 1; }
.connector-name { font-weight: 500; font-size: 13px; }
.connector-status { font-size: 11px; color: var(--success); display: flex; align-items: center; gap: 4px; }
.connector-status .dot { width: 6px; height: 6px; background: var(--success); border-radius: 50%; }
.connector-meta { font-size: 11px; color: var(--text-3); margin-top: 6px; }

/* Spinner */
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }
'''

# ==========================================
# 刪除舊檔案
# ==========================================
files_to_delete = ["src/pages/ListPage.tsx", "src/components/FormCard.tsx", "src/data.json"]

# ==========================================
# 上傳到 VFS
# ==========================================
# 一次上傳所有檔案
all_updates = {}
for path, content in files.items():
    all_updates[path] = content

print(f"\n=== 上傳 {len(all_updates)} 個 VFS 檔案 ===")
r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": all_updates}, token)
if r and "_error" not in r:
    print(f"  OK: all files uploaded")
else:
    print(f"  FAIL: {json.dumps(r, ensure_ascii=False)[:500]}")

# 刪除不需要的檔案（用空字串替代）
del_updates = {}
for path in files_to_delete:
    if path in vfs:
        del_updates[path] = ""
if del_updates:
    print(f"\n=== 清空 {len(del_updates)} 個舊檔案 ===")
    r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": del_updates}, token)
    if r and "_error" not in r:
        print(f"  OK")
    else:
        print(f"  FAIL: {json.dumps(r, ensure_ascii=False)[:200]}")

# ==========================================
# 編譯
# ==========================================
print("\n=== 編譯 ===")
time.sleep(2)
compile_r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
if compile_r and "_error" not in compile_r:
    print(f"  OK: {json.dumps(compile_r, ensure_ascii=False)[:300]}")
else:
    print(f"  FAIL: {json.dumps(compile_r, ensure_ascii=False)[:500]}")
    # 嘗試重試
    time.sleep(3)
    compile_r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
    print(f"  Retry: {json.dumps(compile_r, ensure_ascii=False)[:500]}")

# ==========================================
# 發佈
# ==========================================
print("\n=== 發佈 ===")
time.sleep(2)
# Publish 需要 body: {"version_note": "..."}
pub_r = api("POST", f"/builder/apps/{APP}/publish", {"version_note": "churn dashboard v1"}, token)
if pub_r and "_error" not in pub_r:
    print(f"  OK: published")
else:
    print(f"  Note: publish response: {json.dumps(pub_r, ensure_ascii=False)[:300]}")
    # 嘗試不帶 body
    pub_r2 = api("PUT", f"/builder/apps/{APP}/publish", {}, token)
    print(f"  PUT attempt: {json.dumps(pub_r2, ensure_ascii=False)[:300]}")

# ==========================================
# 驗證
# ==========================================
print("\n=== 驗證 VFS ===")
app_final = api("GET", f"/builder/apps/{APP}", None, token)
vfs_final = app_final.get("vfs_state", {})
print(f"  Total files: {len(vfs_final)}")
for path in sorted(vfs_final):
    content = vfs_final[path] or ""
    print(f"    {path}: {len(content)} chars")

print("\nDone!")
