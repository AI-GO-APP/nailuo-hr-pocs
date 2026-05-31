# -*- coding: utf-8 -*-
"""修正所有 Action 使用 ctx.response.json() 並重新部署"""
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
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:500]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# ===== analyze_churn.py (使用 ctx.response.json) =====
analyze_churn = '''import os, json

def execute(ctx):
    action = ctx.params.get("action", "dashboard")
    skip_ai = ctx.params.get("skip_ai", False)
    
    logs = ctx.db.query_object("sales_logs", limit=500)
    if not isinstance(logs, list):
        logs = []
    
    if action == "dashboard":
        result = _dashboard(ctx, logs, skip_ai)
    elif action == "sales_analysis":
        result = _sales_analysis(ctx, logs, skip_ai)
    elif action == "category_detail":
        category = ctx.params.get("category", "")
        result = _category_detail(ctx, logs, category, skip_ai)
    elif action == "log_analyze":
        result = _log_analyze(ctx, skip_ai)
    else:
        result = {"error": "Unknown action"}
    
    ctx.response.json(result)

def _dashboard(ctx, logs, skip_ai):
    from collections import Counter, defaultdict
    
    total_logs = len(logs)
    high_risk_logs = [l for l in logs if (l.get("risk_score") or 0) >= 3]
    high_risk_companies = set(l.get("company", "") for l in high_risk_logs)
    
    cat_counter = Counter(l.get("risk_category", "") for l in logs if (l.get("risk_score") or 0) >= 2 and l.get("risk_category") and l.get("risk_category") != "無風險")
    top_category = cat_counter.most_common(1)[0][0] if cat_counter else "無"
    
    kpi = {
        "total_logs": total_logs,
        "high_risk_customers": len(high_risk_companies),
        "high_risk_logs": len(high_risk_logs),
        "top_category": top_category,
    }
    
    company_data = defaultdict(lambda: {"logs": [], "risk_scores": [], "categories": [], "salesperson": "", "grade": ""})
    for l in logs:
        c = l.get("company", "")
        if not c:
            continue
        company_data[c]["logs"].append(l)
        company_data[c]["risk_scores"].append(l.get("risk_score", 0) or 0)
        if l.get("risk_category") and l.get("risk_category") != "無風險":
            company_data[c]["categories"].append(l.get("risk_category"))
        company_data[c]["salesperson"] = l.get("salesperson", "")
        company_data[c]["grade"] = l.get("customer_grade", "")
    
    customer_ranking = []
    for company, info in company_data.items():
        max_risk = max(info["risk_scores"]) if info["risk_scores"] else 0
        cat_c = Counter(info["categories"])
        main_cat = cat_c.most_common(1)[0][0] if cat_c else "無"
        customer_ranking.append({
            "company": company,
            "salesperson": info["salesperson"],
            "grade": info["grade"],
            "contact_count": len(info["logs"]),
            "max_risk": max_risk,
            "high_risk_count": sum(1 for s in info["risk_scores"] if s >= 3),
            "main_category": main_cat,
        })
    customer_ranking.sort(key=lambda x: -x["max_risk"])
    
    all_cats = Counter(l.get("risk_category", "") for l in logs if l.get("risk_category") and l.get("risk_category") != "無風險")
    category_dist = [{"name": k, "count": v} for k, v in all_cats.most_common()]
    
    result = {
        "kpi": kpi,
        "customer_ranking": customer_ranking,
        "category_distribution": category_dist,
        "top5_customers": customer_ranking[:5],
        "ai_insight": "",
    }
    
    if not skip_ai:
        result["ai_insight"] = _call_ai(ctx,
            "你是客戶流失風險分析專家。以下是本月業務日誌統計：\\n"
            + "- 總日誌數：" + str(total_logs) + "\\n"
            + "- 高風險客戶：" + str(len(high_risk_companies)) + " 個\\n"
            + "- 高風險日誌：" + str(len(high_risk_logs)) + " 筆\\n"
            + "- 主要風險類型：" + top_category + "\\n"
            + "- 風險分布：" + json.dumps(dict(all_cats), ensure_ascii=False) + "\\n\\n"
            + "請用3-5條條列式提供主管洞察與建議。不要使用任何emoji，用純文字。")
    
    return result

def _sales_analysis(ctx, logs, skip_ai):
    from collections import defaultdict
    
    staff = defaultdict(lambda: {"customers": set(), "high_risk": set(), "visits": 0, "risk_scores": []})
    for l in logs:
        sp = l.get("salesperson", "")
        if not sp:
            continue
        staff[sp]["customers"].add(l.get("company", ""))
        staff[sp]["visits"] += 1
        score = l.get("risk_score", 0) or 0
        staff[sp]["risk_scores"].append(score)
        if score >= 3:
            staff[sp]["high_risk"].add(l.get("company", ""))
    
    staff_ranking = []
    quadrant_data = []
    for name, info in staff.items():
        avg_risk = sum(info["risk_scores"]) / len(info["risk_scores"]) if info["risk_scores"] else 0
        staff_ranking.append({
            "name": name,
            "customer_count": len(info["customers"]),
            "high_risk_count": len(info["high_risk"]),
            "visits": info["visits"],
            "avg_risk": round(avg_risk, 1),
        })
        quadrant_data.append({
            "name": name,
            "x": info["visits"],
            "y": round(avg_risk, 1),
            "size": len(info["customers"]),
        })
    
    staff_ranking.sort(key=lambda x: -x["high_risk_count"])
    
    result = {
        "kpi": {
            "total_staff": len(staff),
            "concentrated_risk": sum(1 for s in staff_ranking if s["high_risk_count"] >= 2),
            "firefighter": sum(1 for q in quadrant_data if q["x"] > 8 and q["y"] > 2),
            "multi_visit": 0,
        },
        "staff_ranking": staff_ranking,
        "quadrant_data": quadrant_data,
        "ai_insight": "",
    }
    
    if not skip_ai:
        result["ai_insight"] = _call_ai(ctx,
            "分析以下業務人員的客戶風險狀況：\\n"
            + json.dumps(staff_ranking, ensure_ascii=False) + "\\n\\n"
            + "請用3-5條條列式提供建議。不要使用emoji。")
    
    return result

def _category_detail(ctx, logs, category, skip_ai):
    from collections import Counter, defaultdict
    
    cat_logs = [l for l in logs if l.get("risk_category") == category]
    
    companies = defaultdict(list)
    staff_impact = defaultdict(int)
    for l in cat_logs:
        companies[l.get("company", "")].append(l)
        staff_impact[l.get("salesperson", "")] += 1
    
    top_customers = sorted(companies.items(), key=lambda x: -len(x[1]))[:5]
    top_staff = sorted(staff_impact.items(), key=lambda x: -x[1])[:5]
    
    result = {
        "category": category,
        "total_logs": len(cat_logs),
        "total_customers": len(companies),
        "top_customers": [{"company": c, "count": len(ll)} for c, ll in top_customers],
        "top_staff": [{"name": n, "count": c} for n, c in top_staff],
        "ai_insight": "",
    }
    
    if not skip_ai:
        descs = [l.get("description", "")[:100] for l in cat_logs[:10]]
        result["ai_insight"] = _call_ai(ctx,
            "分析以下「" + category + "」風險類別的業務日誌摘要：\\n"
            + "\\n".join(descs) + "\\n\\n"
            + "請用3-5條條列式提供此類別的深度分析與建議。不要使用emoji。")
    
    return result

def _log_analyze(ctx, skip_ai):
    description = ctx.params.get("description", "")
    if not description:
        return {"error": "缺少日誌描述"}
    if skip_ai:
        return {"risk_score": 0, "risk_category": "待分析", "ai_reason": ""}
    ai_result = _call_ai(ctx,
        "你是客戶流失風險分析專家。請判讀以下業務日誌的風險：\\n\\n"
        + description + "\\n\\n請回傳 JSON：\\n"
        + "{\\\"risk_score\\\": 0-4, \\\"risk_category\\\": \\\"競爭搶單/品質客訴/營運下滑/帳款問題/關係惡化/無風險\\\", \\\"reason\\\": \\\"說明\\\"}\\n只回傳 JSON。")
    try:
        return json.loads(ai_result)
    except:
        return {"risk_score": 1, "risk_category": "無風險", "ai_reason": ai_result}

def _call_ai(ctx, prompt):
    import urllib.request as req2
    import ssl as ssl2
    ssl2._create_default_https_context = ssl2._create_unverified_context
    
    api_key = ctx.secrets.get("OPENAI_API_KEY")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return "- AI 金鑰未設定，無法分析"
    
    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 600,
    }).encode("utf-8")
    
    r = req2.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + api_key}
    )
    try:
        with req2.urlopen(r, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return "- AI 分析失敗: " + str(e)[:100]
'''

# ===== fetch_crm_data.py =====
fetch_crm = '''import json

def execute(ctx):
    action = ctx.params.get("action", "refs_status")
    db = ctx.db
    
    if action == "refs_status":
        sources = []
        for table in ["crm_leads", "sale_orders", "crm_tags", "crm_teams", "crm_stages", "sale_order_lines"]:
            try:
                data = db.query(table, limit=1)
                count = len(data) if isinstance(data, list) else 0
                sources.append({"name": table, "status": "connected", "count": count})
            except:
                sources.append({"name": table, "status": "error"})
        
        try:
            logs = db.query_object("sales_logs", limit=500)
            log_count = len(logs) if isinstance(logs, list) else 0
            sources.append({"name": "sales_logs", "status": "connected", "count": log_count, "type": "custom"})
        except:
            sources.append({"name": "sales_logs", "status": "error", "type": "custom"})
        
        ctx.response.json({"sources": sources})
    
    elif action == "raw_logs":
        try:
            logs = db.query_object("sales_logs", limit=100)
            if not isinstance(logs, list):
                logs = []
            formatted = [{"id": l.get("id", ""), "data": l} for l in logs]
            ctx.response.json({"logs": formatted})
        except Exception as e:
            ctx.response.json({"logs": [], "error": str(e)})
    
    else:
        ctx.response.json({"error": "Unknown action"})
'''

# ===== 修正前端 — runAction 回傳 {data: result, file: ...} =====
# 所以前端頁面呼叫 `const r = await runAction(...)` 得到的是 {data: {...}}
# 需要用 r.data 來存取真正的結果

# 不，再仔細看 action.ts:
# return { data: result.data || result, file: result.file || undefined };
# 如果 action result 是 {kpi: ...}，沒有 .data，所以回傳 {data: {kpi: ...}}
# 前端呼叫 const r = await runAction(...) -> r = {data: {kpi:...}}
# 所以頁面應該用 r.data 來存取

# 讓我修正所有頁面：
dashboard_page = open("c:/Users/User/dev project/AI GO-MODEL/nailuo-hr-pocs/build_churn_frontend.py", encoding="utf-8").read()
# 不用讀檔，直接重新上傳修正版

# DashboardPage 修正
dashboard_tsx = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { FileText, AlertTriangle, Clock, Star, RefreshCw, Loader2, Brain } from "lucide-react";

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
      setData(r.data || r);
    } catch (e: any) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const loadAI = async () => {
    setAiLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "dashboard", skip_ai: false });
      const d = r.data || r;
      setAiInsight(d.ai_insight || "");
    } catch (e: any) { setAiInsight("AI 分析失敗: " + (e.message || "")); }
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
        <div className="kpi-card"><div className="kpi-icon blue"><FileText size={18} /></div><div className="kpi-label">分析日誌總數</div><div className="kpi-value">{kpi.total_logs || 0}</div></div>
        <div className="kpi-card danger"><div className="kpi-icon red"><AlertTriangle size={18} /></div><div className="kpi-label">高風險客戶</div><div className="kpi-value">{kpi.high_risk_customers || 0}</div></div>
        <div className="kpi-card"><div className="kpi-icon orange"><Clock size={18} /></div><div className="kpi-label">高風險日誌</div><div className="kpi-value">{kpi.high_risk_logs || 0}</div></div>
        <div className="kpi-card"><div className="kpi-icon purple"><Star size={18} /></div><div className="kpi-label">主要風險類型</div><div className="kpi-value" style={{fontSize:20}}>{kpi.top_category || "-"}</div></div>
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">客戶風險排名</div><div className="panel-sub">依最高風險分數排序</div></div></div>
          <div className="search-row"><input className="search-input" placeholder="搜尋公司、業務..." value={search} onChange={e => setSearch(e.target.value)} /></div>
          <table>
            <thead><tr><th>公司簡稱</th><th>業務人員</th><th>等級</th><th>接觸次數</th><th>最高風險</th><th>高風險日誌</th><th>主要風險類別</th></tr></thead>
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
          <div className="panel"><div className="panel-head"><div><div className="panel-title">風險類別分布</div></div></div><BarChart data={data.category_distribution || []} /></div>
          <div className="panel">
            <div className="panel-head"><div><div className="panel-title">最該關注的 5 個客戶</div><div className="panel-sub">依風險分數排序</div></div></div>
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
            <div className="panel-head">
              <div><div className="panel-title">AI 洞察</div></div>
              <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>
                {aiLoading ? <><Loader2 size={14} className="spin" /> 分析中...</> : <><Brain size={14} /> 產生洞察</>}
              </button>
            </div>
            {aiInsight ? (
              <div className="ai-reason-box">
                <div className="ai-icon" style={{fontSize:14,fontWeight:700,color:"var(--primary)"}}>AI</div>
                <div className="ai-reason-content"><div className="ai-reason-label">AI 主管洞察</div><div className="ai-reason-text" style={{whiteSpace:"pre-line"}}>{aiInsight}</div></div>
              </div>
            ) : !aiLoading ? (<p style={{color:"#94A3B8",fontSize:13,textAlign:"center",padding:16}}>點擊上方按鈕產生 AI 洞察</p>) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
'''

# SalesPage 修正
sales_tsx = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Users, AlertTriangle, Flame, UserCheck, RefreshCw, Loader2, Brain } from "lucide-react";

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
      <line x1={pad.left} y1={H-pad.bottom} x2={W-pad.right} y2={H-pad.bottom} stroke="#E2E8F0" strokeWidth={1} />
      <line x1={pad.left} y1={pad.top} x2={pad.left} y2={H-pad.bottom} stroke="#E2E8F0" strokeWidth={1} />
      <line x1={pad.left+innerW*(midX/maxX)} y1={pad.top} x2={pad.left+innerW*(midX/maxX)} y2={H-pad.bottom} stroke="#E2E8F0" strokeDasharray="4" />
      <line x1={pad.left} y1={pad.top+innerH*(1-midY/maxY)} x2={W-pad.right} y2={pad.top+innerH*(1-midY/maxY)} stroke="#E2E8F0" strokeDasharray="4" />
      <text x={W-pad.right-10} y={pad.top+15} textAnchor="end" fontSize={11} fill="#94A3B8">救火型</text>
      <text x={pad.left+10} y={pad.top+15} textAnchor="start" fontSize={11} fill="#94A3B8">失聯型</text>
      <text x={W-pad.right-10} y={H-pad.bottom-8} textAnchor="end" fontSize={11} fill="#94A3B8">穩定型</text>
      {data.map((d, i) => {
        const cx = pad.left + (d.x / maxX) * innerW;
        const cy = pad.top + (1 - d.y / maxY) * innerH;
        const r = Math.max(8, Math.min(20, d.size * 4));
        const color = d.y > midY ? (d.x > midX ? "#DC2626" : "#CA8A04") : (d.x > midX ? "#16A34A" : "#94A3B8");
        return (<g key={i}><circle cx={cx} cy={cy} r={r} fill={color} opacity={0.7} stroke="white" strokeWidth={2} /><text x={cx} y={cy-r-4} textAnchor="middle" fontSize={10} fill="#0F172A">{d.name}</text></g>);
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
      setData(r.data || r);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  const loadAI = async () => {
    setAiLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "sales_analysis", skip_ai: false });
      setAiInsight((r.data || r).ai_insight || "");
    } catch (e: any) { setAiInsight("AI 分析失敗"); }
    setAiLoading(false);
  };

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /></div>;
  if (!data) return <div className="page"><p>無資料</p></div>;
  const kpi = data.kpi || {};

  return (
    <div className="page">
      <div className="page-head"><div><h1 className="page-title">業務分析</h1><p className="page-subtitle">從業務角度看：誰的客戶最該關注</p></div><button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> 更新</button></div>
      <div className="kpi-grid">
        <div className="kpi-card"><div className="kpi-icon teal"><Users size={18} /></div><div className="kpi-label">分析業務人員</div><div className="kpi-value">{kpi.total_staff || 0}</div></div>
        <div className="kpi-card danger"><div className="kpi-icon red"><AlertTriangle size={18} /></div><div className="kpi-label">高風險集中業務</div><div className="kpi-value">{kpi.concentrated_risk || 0}</div></div>
        <div className="kpi-card"><div className="kpi-icon orange"><Flame size={18} /></div><div className="kpi-label">救火型業務</div><div className="kpi-value">{kpi.firefighter || 0}</div></div>
        <div className="kpi-card"><div className="kpi-icon blue"><UserCheck size={18} /></div><div className="kpi-label">客戶被多人拜訪</div><div className="kpi-value">{kpi.multi_visit || 0}</div></div>
      </div>
      <div className="sales-grid">
        <div className="panel"><div className="panel-head"><div><div className="panel-title">業務人員風險地圖</div><div className="panel-sub">X: 拜訪次數 / Y: 平均風險 / 大小: 客戶數</div></div></div><QuadrantChart data={data.quadrant_data || []} /></div>
        <div className="panel"><div className="panel-head"><div><div className="panel-title">業務人員風險排名</div></div></div>
          <table><thead><tr><th>業務人員</th><th>管轄客戶</th><th>高風險</th><th>拜訪次數</th><th>平均風險</th></tr></thead>
          <tbody>{(data.staff_ranking || []).map((s: any) => (<tr key={s.name}><td style={{fontWeight:500}}>{s.name}</td><td>{s.customer_count}</td><td className={`score-cell ${s.high_risk_count > 0 ? "high" : ""}`}>{s.high_risk_count}</td><td>{s.visits}</td><td>{s.avg_risk}</td></tr>))}</tbody></table>
        </div>
      </div>
      <div className="panel" style={{marginTop:16}}>
        <div className="panel-head"><div><div className="panel-title">AI 洞察</div></div>
          <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>{aiLoading ? <><Loader2 size={14} className="spin" /> 分析中...</> : <><Brain size={14} /> 產生洞察</>}</button>
        </div>
        {aiInsight ? (<div className="ai-reason-box"><div className="ai-icon" style={{fontSize:14,fontWeight:700,color:"var(--primary)"}}>AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI 業務分析</div><div className="ai-reason-text" style={{whiteSpace:"pre-line"}}>{aiInsight}</div></div></div>
        ) : !aiLoading ? (<p style={{color:"#94A3B8",fontSize:13,textAlign:"center",padding:16}}>點擊上方按鈕產生 AI 洞察</p>) : null}
      </div>
    </div>
  );
}
'''

# CategoriesPage 修正
categories_tsx = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Loader2, Brain, Swords, Wrench, TrendingDown, Wallet, HeartCrack } from "lucide-react";

const CATEGORIES = [
  { id: "競爭搶單", label: "競爭搶單", color: "#DC2626", icon: Swords },
  { id: "品質客訴", label: "品質客訴", color: "#EA580C", icon: Wrench },
  { id: "營運下滑", label: "營運下滑", color: "#7C3AED", icon: TrendingDown },
  { id: "帳款問題", label: "帳款問題", color: "#CA8A04", icon: Wallet },
  { id: "關係惡化", label: "關係惡化", color: "#BE185D", icon: HeartCrack },
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
      const d = r.data || r;
      const dist = d.category_distribution || [];
      const map: Record<string, number> = {};
      dist.forEach((item: any) => { map[item.name] = item.count; });
      setCounts(map);
    } catch {}
  }, []);
  useEffect(() => { loadCounts(); }, [loadCounts]);

  const loadDetail = useCallback(async (cat: string) => {
    setLoading(true);
    setAiInsight("");
    try {
      const r = await runAction("analyze_churn", { action: "category_detail", category: cat, skip_ai: true });
      setDetail(r.data || r);
    } catch { setDetail(null); }
    setLoading(false);
  }, []);
  useEffect(() => { loadDetail(active); }, [active, loadDetail]);

  const loadAI = async () => {
    setAiLoading(true);
    try {
      const r = await runAction("analyze_churn", { action: "category_detail", category: active, skip_ai: false });
      setAiInsight((r.data || r).ai_insight || "");
    } catch { setAiInsight("AI 分析失敗"); }
    setAiLoading(false);
  };

  const activeCat = CATEGORIES.find(c => c.id === active)!;

  return (
    <div className="page">
      <div className="page-head"><div><h1 className="page-title">風險類別分析</h1><p className="page-subtitle">五大流失風險類別深度解析</p></div></div>
      <div className="cat-tabs">
        {CATEGORIES.map(cat => {
          const Icon = cat.icon;
          return (
            <div key={cat.id} className={`cat-tab ${active === cat.id ? "active" : ""}`} style={active === cat.id ? {borderColor: cat.color, color: cat.color} : {}} onClick={() => setActive(cat.id)}>
              <div className="cat-tab-icon"><Icon size={22} color={cat.color} /></div>
              <div className="cat-tab-content"><div className="cat-tab-name">{cat.label}</div><div className="cat-tab-stat">{counts[cat.id] || 0} 筆日誌</div></div>
              <div className="cat-tab-value" style={{color: cat.color}}>{counts[cat.id] || 0}</div>
            </div>
          );
        })}
      </div>
      {loading ? (<div style={{textAlign:"center",padding:60}}><Loader2 className="spin" size={32} /></div>) : detail ? (
        <>
          <div className="cat-summary-card" style={{background:`linear-gradient(135deg, ${activeCat.color}, ${activeCat.color}dd)`,marginBottom:16}}>
            <div className="cat-summary-name">{activeCat.label}</div>
            <div className="cat-summary-desc">共 {detail.total_logs} 筆日誌，影響 {detail.total_customers} 個客戶</div>
            <div className="cat-summary-stats"><div><div className="cat-summary-stat-label">日誌數</div><div className="cat-summary-stat-value">{detail.total_logs}</div></div><div><div className="cat-summary-stat-label">客戶數</div><div className="cat-summary-stat-value">{detail.total_customers}</div></div></div>
          </div>
          <div className="cat-detail-grid">
            <div className="panel"><div className="panel-head"><div><div className="panel-title">此類別 Top 客戶</div></div></div>
              {(detail.top_customers || []).map((c: any, i: number) => (<div key={c.company} className="cat-customer-card"><div className="cat-customer-rank" style={{background: activeCat.color}}>{i+1}</div><div className="cat-customer-info"><div className="cat-customer-name">{c.company}</div><div className="cat-customer-reason">{c.count} 筆相關日誌</div></div></div>))}
            </div>
            <div className="panel"><div className="panel-head"><div><div className="panel-title">此類別影響業務</div></div></div>
              {(detail.top_staff || []).map((s: any, i: number) => (<div key={s.name} className="cat-customer-card"><div className="cat-customer-rank" style={{background: "#475569"}}>{i+1}</div><div className="cat-customer-info"><div className="cat-customer-name">{s.name}</div><div className="cat-customer-reason">{s.count} 筆相關日誌</div></div></div>))}
            </div>
          </div>
          <div className="panel">
            <div className="panel-head"><div><div className="panel-title">AI 洞察 - {activeCat.label}</div></div>
              <button className="btn btn-primary" onClick={loadAI} disabled={aiLoading}>{aiLoading ? <><Loader2 size={14} className="spin" /> 分析中...</> : <><Brain size={14} /> 產生洞察</>}</button>
            </div>
            {aiInsight ? (<div className="ai-reason-box"><div className="ai-icon" style={{fontSize:14,fontWeight:700,color:"var(--primary)"}}>AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI 類別深度分析</div><div className="ai-reason-text" style={{whiteSpace:"pre-line"}}>{aiInsight}</div></div></div>
            ) : !aiLoading ? (<p style={{color:"#94A3B8",fontSize:13,textAlign:"center",padding:16}}>點擊上方按鈕產生 AI 洞察</p>) : null}
          </div>
        </>
      ) : null}
    </div>
  );
}
'''

# DataSourcePage 修正
datasource_tsx = '''import { useState, useEffect, useCallback } from "react";
import { runAction } from "../action";
import { Database, Loader2, RefreshCw, XCircle, Link2, FileText, BarChart3 } from "lucide-react";

export default function DataSourcePage() {
  const [sources, setSources] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"status" | "logs">("status");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await runAction("fetch_crm_data", { action: "refs_status" });
      const d = r.data || r;
      setSources(d.sources || []);
      const r2 = await runAction("fetch_crm_data", { action: "raw_logs" });
      const d2 = r2.data || r2;
      setLogs(d2.logs || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);
  useEffect(() => { load(); }, [load]);

  if (loading) return <div className="page" style={{textAlign:"center",padding:"80px 0"}}><Loader2 className="spin" size={32} /></div>;

  const connected = sources.filter(s => s.status === "connected").length;
  const icons = [Link2, FileText, BarChart3];

  return (
    <div className="page">
      <div className="page-head"><div><h1 className="page-title">資料來源</h1><p className="page-subtitle">管理 CRM/ERP 資料連線與原始日誌</p></div><button className="btn btn-ghost" onClick={load}><RefreshCw size={14} /> 更新</button></div>
      <div className="data-status-card"><div className="data-status-icon"><Database size={24} color="#2563EB" /></div><div className="data-status-info"><div className="data-status-title">資料來源連線狀態</div><div className="data-status-meta">已連線 <strong>{connected}</strong> 個 / 共 <strong>{sources.length}</strong> 個</div></div></div>
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
'''

# ===== Upload all =====
all_files = {
    "actions/analyze_churn.py": analyze_churn,
    "actions/fetch_crm_data.py": fetch_crm,
    "actions/debug_ctx.py": "# removed",
    "src/pages/DashboardPage.tsx": dashboard_tsx,
    "src/pages/SalesPage.tsx": sales_tsx,
    "src/pages/CategoriesPage.tsx": categories_tsx,
    "src/pages/DataSourcePage.tsx": datasource_tsx,
}

print("=== Upload all files ===")
r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": all_files}, token)
print("Upload:", "OK" if r and "_error" not in r else json.dumps(r, ensure_ascii=False)[:300])

# Update manifest
manifest = {"actions": [
    {"name": "analyze_churn", "file": "actions/analyze_churn.py", "description": "risk"},
    {"name": "fetch_crm_data", "file": "actions/fetch_crm_data.py", "description": "data"},
]}
r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": {"actions/manifest.json": json.dumps(manifest)}}, token)

# Compile + Publish
slug = "da1900f990b0"
time.sleep(1)
c = api("POST", f"/compile/compile/{slug}", None, token)
html = c.get("html", "")
errors = c.get("compile_errors", [])
print(f"Compile: success={c.get('success')}, errors={len(errors)}")
for e in errors:
    print(f"  {e}")

r = api("POST", f"/builder/apps/{APP}/publish", {"published_assets": {"html": html}}, token)
print("Publish:", "OK" if r and "_error" not in r else "FAIL")

# ===== E2E =====
print("\n=== E2E Test ===")

r = api("POST", f"/actions/apps/{APP}/run/analyze_churn", {"params": {"action": "dashboard", "skip_ai": True}}, token)
result = r.get("result") or {}
kpi = result.get("kpi", {})
print(f"Dashboard: total={kpi.get('total_logs')}, high_risk={kpi.get('high_risk_customers')}, top={kpi.get('top_category')}")
print(f"  Customers: {len(result.get('customer_ranking', []))}")

r = api("POST", f"/actions/apps/{APP}/run/analyze_churn", {"params": {"action": "sales_analysis", "skip_ai": True}}, token)
result = r.get("result") or {}
print(f"Sales: staff={len(result.get('staff_ranking', []))}")

r = api("POST", f"/actions/apps/{APP}/run/fetch_crm_data", {"params": {"action": "refs_status"}}, token)
result = r.get("result") or {}
sources = result.get("sources", [])
print(f"DataSource: {len(sources)} tables")
for s in sources:
    print(f"  {s.get('name')}: {s.get('status')} ({s.get('count', '?')})")

print("\nAll done! App: https://tslg-churn-analysis-manager.ai-go.app")
