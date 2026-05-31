import MarkdownText from "../components/MarkdownText";
import AILoadingSkeleton from "../components/AILoadingSkeleton";
import { useState, useEffect, useCallback } from "react";
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
    try { const r = await runAction("analyze_churn", { action: "category_detail", category: active, skip_ai: false }); setAiInsight((r.data || r).ai_insight || ""); } catch { setAiInsight("AI 分析失敗"); }
    setAiLoading(false);
  };

  const activeCat = CATEGORIES.find(c => c.id === active)!;

  return (
    <div className="page">
      <div className="page-head"><div><h1 className="page-title">風險類別分析</h1><p className="page-subtitle">深入剖析各類風險的真實成因</p></div></div>
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
            {aiLoading ? (
        <AILoadingSkeleton />
      ) : aiInsight ? (<div className="ai-reason-box"><div className="ai-icon">AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI 類別洞察</div><MarkdownText text={aiInsight} /></div></div>
      ) : (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>點擊上方按鈕產生 AI 洞察</p>)}
          </div>
        </>
      ) : null}
    </div>
  );
}
