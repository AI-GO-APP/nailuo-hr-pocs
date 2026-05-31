import MarkdownText from "../components/MarkdownText";
import AILoadingSkeleton from "../components/AILoadingSkeleton";
import React, { useState, useEffect, useRef, useCallback } from "react";
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
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchActiveIdx, setSearchActiveIdx] = useState(-1);
  const searchRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const r = await runAction("analyze_churn", { action: "dashboard", skip_ai: true });
      setData(r.data || r);
    } catch (e: any) { setError(e.message || "載入失敗"); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) setSearchOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const loadAI = async () => {
    setAiLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "dashboard", skip_ai: false });
      setAiInsight((r.data || r).ai_insight || "");
    } catch (e: any) { setAiInsight("AI 分析失敗: " + (e.message || "")); }
    setAiLoading(false);
  };

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /><p style={{marginTop:12,color:"var(--text-3)"}}>{"載入中..."}</p></div>;
  if (error) return <div className="page"><div className="panel" style={{textAlign:"center"}}><p style={{color:"var(--danger)",marginBottom:12}}>{"載入失敗"}</p><p style={{fontSize:13,color:"var(--text-3)"}}>{error}</p><button className="btn btn-primary" onClick={load} style={{marginTop:16}}><RefreshCw size={14} /> {"重試"}</button></div></div>;
  if (!data) return <div className="page"><p>{"無資料"}</p></div>;

  const kpi = data.kpi || {};

  const allCompanyNames = (data.customer_ranking || []).map((c: any) => c.company || "");
  const searchSuggestions = search
    ? allCompanyNames.filter((c: string) => c.toLowerCase().includes(search.toLowerCase()))
    : allCompanyNames;

  const handleSearchKey = (e: React.KeyboardEvent) => {
    if (!searchOpen) { if (e.key === "ArrowDown") setSearchOpen(true); return; }
    if (e.key === "ArrowDown") { e.preventDefault(); setSearchActiveIdx(i => Math.min(i + 1, searchSuggestions.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setSearchActiveIdx(i => Math.max(i - 1, 0)); }
    else if (e.key === "Enter" && searchActiveIdx >= 0) { e.preventDefault(); setSearch(searchSuggestions[searchActiveIdx]); setSearchOpen(false); }
    else if (e.key === "Escape") setSearchOpen(false);
  };

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
          <div className="search-row" ref={searchRef} style={{position:"relative"}}>
              <input className="search-input" placeholder={"搜尋公司簡稱、業務人員..."} value={search}
                onChange={e => { setSearch(e.target.value); setSearchOpen(true); setSearchActiveIdx(-1); }}
                onFocus={() => setSearchOpen(true)}
                onKeyDown={handleSearchKey}
                autoComplete="off" />
              <svg className={`autocomplete-chevron${searchOpen ? " open" : ""}`} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{position:"absolute",right:14,top:"50%",transform:searchOpen?"translateY(-50%) rotate(180deg)":"translateY(-50%)",pointerEvents:"none",color:"#94a3b8"}}><polyline points="6 9 12 15 18 9"/></svg>
              {searchOpen && searchSuggestions.length > 0 && (
                <div className="autocomplete-dropdown">
                  {searchSuggestions.map((c: string, i: number) => (
                    <div key={c}
                      className={`ac-item${i === searchActiveIdx ? " active" : ""}`}
                      onMouseEnter={() => setSearchActiveIdx(i)}
                      onMouseDown={(e: React.MouseEvent) => { e.preventDefault(); setSearch(c); setSearchOpen(false); }}
                    >{search ? <>{c.slice(0, c.toLowerCase().indexOf(search.toLowerCase()))}<span className="ac-match">{c.slice(c.toLowerCase().indexOf(search.toLowerCase()), c.toLowerCase().indexOf(search.toLowerCase()) + search.length)}</span>{c.slice(c.toLowerCase().indexOf(search.toLowerCase()) + search.length)}</> : c}</div>
                  ))}
                </div>
              )}
            </div>
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
            {aiLoading ? (
      <AILoadingSkeleton />
    ) : aiInsight ? (
      <div className="ai-reason-box">
        <div className="ai-icon">AI</div>
        <div className="ai-reason-content"><div className="ai-reason-label">AI {"主管洞察"}</div><MarkdownText text={aiInsight} /></div>
      </div>
    ) : (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>{"點擊上方按鈕產生 AI 洞察"}</p>)}
          </div>
        </div>
      </div>
    </div>
  );
}
