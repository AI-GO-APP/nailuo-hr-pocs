import MarkdownText from "../components/MarkdownText";
import AILoadingSkeleton from "../components/AILoadingSkeleton";
import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Users, AlertTriangle, Flame, UserCheck, RefreshCw, Loader2, Brain } from "lucide-react";

function QuadrantChart({ data }: { data: any[] }) {
  if (!data || data.length === 0) return <p style={{color:"var(--text-3)",textAlign:"center",padding:40}}>無資料</p>;
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
      <text x={W-pad.right-10} y={pad.top+15} textAnchor="end" fontSize={11} fill="#94A3B8" fontWeight={500}>救火型</text>
      <text x={pad.left+10} y={pad.top+15} fontSize={11} fill="#94A3B8" fontWeight={500}>失聯型</text>
      <text x={W-pad.right-10} y={H-pad.bottom-8} textAnchor="end" fontSize={11} fill="#94A3B8" fontWeight={500}>穩定型</text>
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
    try { const r = await runAction("analyze_churn", { action: "sales_analysis", skip_ai: true }); setData(r.data || r); } catch (e: any) { setError(e.message || "載入失敗"); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  const loadAI = async () => {
    setAiLoading(true);
    try { const r = await runAction("analyze_churn", { action: "sales_analysis", skip_ai: false }); setAiInsight((r.data || r).ai_insight || ""); } catch { setAiInsight("AI 分析失敗"); }
    setAiLoading(false);
  };

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /></div>;
  if (error) return <div className="page"><div className="panel" style={{textAlign:"center"}}><p style={{color:"var(--danger)"}}>{error}</p><button className="btn btn-primary" onClick={load} style={{marginTop:16}}><RefreshCw size={14} /> 重試</button></div></div>;
  if (!data) return <div className="page"><p>無資料</p></div>;
  const kpi = data.kpi || {};
  const staff = data.staff_ranking || [];
  const warnStaff = staff.filter((s: any) => s.high_risk_count >= 2);
  const goodStaff = staff.filter((s: any) => s.high_risk_count <= 0);
  const gradeData = data.grade_distribution || [];
  const actions = data.action_items || [];

  return (
    <div className="page">
      <div className="page-head"><div><h1 className="page-title">業務分析</h1><p className="page-subtitle">從業務角度看：誰的客戶最該關注、誰可能不擅於維繫客戶關係</p></div><button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> 更新</button></div>
      <div className="kpi-grid">
        <div className="kpi-card"><div className="kpi-icon teal"><Users size={18} /></div><div className="kpi-label">分析業務人員</div><div className="kpi-value">{kpi.total_staff || 0}</div><div className="kpi-meta">本期至少 1 筆日誌</div></div>
        <div className="kpi-card danger"><div className="kpi-icon red"><AlertTriangle size={18} /></div><div className="kpi-label">高風險集中業務</div><div className="kpi-value">{kpi.concentrated_risk || 0} 人</div><div className="kpi-meta">管轄 2 個以上高風險客戶</div></div>
        <div className="kpi-card"><div className="kpi-icon orange"><Flame size={18} /></div><div className="kpi-label">救火型業務</div><div className="kpi-value">{kpi.firefighter || 0} 人</div><div className="kpi-meta">高頻拜訪但客戶仍高風險</div></div>
        <div className="kpi-card"><div className="kpi-icon purple"><UserCheck size={18} /></div><div className="kpi-label">客戶被多人拜訪</div><div className="kpi-value">{kpi.multi_visit || 0} 個</div><div className="kpi-meta">交接混亂風險</div></div>
      </div>

      <div className="panel" style={{marginBottom:16}}>
        <div className="panel-head"><div><div className="panel-title">業務人員風險地圖</div><div className="panel-sub">X: 拜訪頻率 / Y: 平均風險分 / 圓圈大小: 高風險客戶數</div></div></div>
        <QuadrantChart data={data.quadrant_data || []} />
      </div>

      <div className="sales-grid">
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">業務人員風險排名</div><div className="panel-sub">依管轄高風險客戶數排序</div></div></div>
          <table><thead><tr><th>業務人員</th><th>管轄客戶</th><th>高風險客戶</th><th>拜訪總次數</th><th>平均風險</th></tr></thead>
          <tbody>{staff.map((s: any) => (<tr key={s.name}><td style={{fontWeight:500}}>{s.name}</td><td>{s.customer_count}</td><td className={`score-cell ${s.high_risk_count >= 2 ? "high" : ""}`}>{s.high_risk_count}</td><td>{s.visits}</td><td>{s.avg_risk}</td></tr>))}</tbody></table>
        </div>
        <div>
          {warnStaff.length > 0 && (
            <div className="warn-card">
              <div className="warn-card-title"><AlertTriangle size={14} /> 不擅維繫客戶 Top {Math.min(3, warnStaff.length)}</div>
              <div className="warn-card-desc">高風險客戶比例最高的業務，建議主管 1-on-1 了解狀況</div>
              <div className="warn-card-list">
                {warnStaff.slice(0, 3).map((s: any) => (
                  <div key={s.name} className="warn-staff-item">
                    <div className="warn-staff-avatar">{s.name[0]}</div>
                    <div className="warn-staff-info"><div className="warn-staff-name">{s.name}</div><div className="warn-staff-meta">管轄 {s.customer_count} 個客戶 / {s.high_risk_count} 個高風險</div></div>
                    <div className="warn-staff-stat">{s.customer_count > 0 ? Math.round(s.high_risk_count / s.customer_count * 100) : 0}%</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {goodStaff.length > 0 && (
            <div className="warn-card green">
              <div className="warn-card-title"><UserCheck size={14} /> 客戶維護優等生</div>
              <div className="warn-card-desc">客戶穩定的業務，值得肯定與經驗分享</div>
              <div className="warn-card-list">
                {goodStaff.slice(0, 3).map((s: any) => (
                  <div key={s.name} className="warn-staff-item">
                    <div className="warn-staff-avatar">{s.name[0]}</div>
                    <div className="warn-staff-info"><div className="warn-staff-name">{s.name}</div><div className="warn-staff-meta">管轄 {s.customer_count} 個客戶 / {s.high_risk_count} 個高風險</div></div>
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
          <div className="panel-head"><div><div className="panel-title">客戶等級風險分布</div><div className="panel-sub">A 級客戶流失損失最大，需優先處理</div></div></div>
          <div className="grade-matrix">
            {gradeData.map((g: any) => (
              <div key={g.grade} className="grade-cell">
                <div className="grade-cell-label">{g.grade} 級客戶</div>
                <div className={`grade-cell-letter ${g.grade}`}>{g.grade}</div>
                <div className="grade-cell-stat"><strong>{g.high_risk}</strong> / 高風險</div>
                <div className="grade-cell-stat" style={{fontSize:11,color:"var(--text-3)"}}>共 {g.total} 個客戶</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="panel" style={{marginTop:16}}>
        <div className="panel-head"><div><div className="panel-title">AI 洞察</div></div>
          <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>{aiLoading ? <><Loader2 size={14} className="spin" /> 分析中...</> : <><Brain size={14} /> 產生洞察</>}</button>
        </div>
        {aiLoading ? (
      <AILoadingSkeleton />
    ) : aiInsight ? (<div className="ai-reason-box"><div className="ai-icon">AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI 業務分析</div><MarkdownText text={aiInsight} /></div></div>
    ) : (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>點擊上方按鈕產生 AI 洞察</p>)}
      </div>
    </div>
  );
}
