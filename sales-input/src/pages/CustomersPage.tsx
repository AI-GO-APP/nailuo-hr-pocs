import React, { useState, useEffect } from "react";
import { runAction } from "../action";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [highRiskCount, setHighRiskCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    runAction("sales_log", { action: "my_customers" })
      .then((r: any) => {
        const d = r?.data || r;
        if (d?.customers) setCustomers(d.customers);
        if (d?.high_risk_count != null) setHighRiskCount(d.high_risk_count);
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
