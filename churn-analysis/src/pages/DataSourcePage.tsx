import { useState, useEffect, useCallback } from "react";
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
      <div className="page-head"><div><h1 className="page-title">資料來源</h1><p className="page-subtitle">CRM 業務日誌資料即時同步，AI 分析自動更新</p></div><div style={{display:"flex",gap:8}}><button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> 更新</button></div></div>
      <div className="data-status-card">
        <div className="data-status-icon"><Database size={24} color="#2563EB" /></div>
        <div className="data-status-info">
          <div className="data-status-title">資料來源連線狀態</div>
          <div className="data-status-meta">已連線 <strong>{connected}</strong> 個 / 共 <strong>{sources.length}</strong> 個資料表，總計 <strong>{totalRecords}</strong> 筆資料</div>
        </div>
      </div>
      <div className="data-source-tabs">
        <div className={`data-tab ${tab === "status" ? "active" : ""}`} onClick={() => setTab("status")}>連線狀態</div>
        <div className={`data-tab ${tab === "logs" ? "active" : ""}`} onClick={() => setTab("logs")}>原始日誌預覽</div>
      </div>
      {tab === "status" ? (
        <div className="connector-list">
          {sources.map((s, i) => {
            const Icon = icons[i % icons.length];
            return (<div key={s.name} className="connector-item"><div className="connector-head"><div className="connector-logo"><Icon size={18} /></div><div className="connector-info"><div className="connector-name">{s.name}</div><div className="connector-status">{s.status === "connected" ? <><span className="dot" /> 已連線</> : <><XCircle size={12} color="#DC2626" /> 錯誤</>}</div></div></div><div className="connector-meta">{s.type === "custom" ? "自訂資料表" : "Proxy Table"} {s.count !== undefined ? `/ ${s.count} 筆` : ""}</div></div>);
          })}
        </div>
      ) : (
        <div className="panel"><div className="panel-head"><div><div className="panel-title">原始日誌預覽</div><div className="panel-sub">最近 {logs.length} 筆</div></div></div>
          <table><thead><tr><th>日期</th><th>業務人員</th><th>公司簡稱</th><th>工作性質</th><th>工作描述</th><th>狀態</th></tr></thead>
          <tbody>{logs.slice(0, 20).map((l: any) => { const d = l.data || {}; return (<tr key={l.id}><td>{d.date}</td><td>{d.salesperson}</td><td>{d.company}</td><td>{d.work_nature}</td><td style={{maxWidth:300,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{d.description}</td><td><span className="badge" style={{background:d.status==="analyzed"?"#DCFCE7":"#FEF3C7",color:d.status==="analyzed"?"#16A34A":"#CA8A04"}}>{d.status === "analyzed" ? "已分析" : "待分析"}</span></td></tr>); })}</tbody></table>
        </div>
      )}
    </div>
  );
}
