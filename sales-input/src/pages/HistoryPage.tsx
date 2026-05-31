import React, { useState, useEffect } from "react";
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
        const d = r?.data || r;
        if (d?.logs) setLogs(d.logs);
        if (d?.kpi) setKpi(d.kpi);
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
