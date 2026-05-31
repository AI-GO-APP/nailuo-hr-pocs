import React, { useState, useEffect, useRef } from "react";
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

function CompanyAutocomplete({ companies, value, onChange, placeholder }: {
  companies: string[];
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const wrapRef = useRef<HTMLDivElement>(null);

  const filtered = value
    ? companies.filter(c => c.toLowerCase().includes(value.toLowerCase()))
    : companies;

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => { setActiveIdx(-1); }, [value]);

  const handleKey = (e: React.KeyboardEvent) => {
    if (!open) { if (e.key === "ArrowDown" || e.key === "Enter") setOpen(true); return; }
    if (e.key === "ArrowDown") { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, filtered.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, 0)); }
    else if (e.key === "Enter" && activeIdx >= 0 && activeIdx < filtered.length) { e.preventDefault(); onChange(filtered[activeIdx]); setOpen(false); }
    else if (e.key === "Escape") setOpen(false);
  };

  const selectItem = (c: string) => {
    onChange(c);
    setOpen(false);
  };

  const highlight = (text: string) => {
    if (!value) return text;
    const idx = text.toLowerCase().indexOf(value.toLowerCase());
    if (idx < 0) return text;
    return <>{text.slice(0, idx)}<span className="ac-match">{text.slice(idx, idx + value.length)}</span>{text.slice(idx + value.length)}</>;
  };

  return (
    <div className="autocomplete-wrap" ref={wrapRef}>
      <input
        type="text"
        className="form-input"
        placeholder={placeholder || "輸入或選擇客戶"}
        value={value}
        onChange={e => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKey}
        autoComplete="off"
      />
      <svg className={"autocomplete-chevron" + (open ? " open" : "")} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>
      {open && (
        <div className="autocomplete-dropdown">
          {filtered.length === 0 && !value && <div className="ac-empty">無客戶資料</div>}
          {filtered.length === 0 && value && (
            <>
              <div className="ac-empty">找不到符合的客戶</div>
              <div className="ac-new" onMouseDown={e => { e.preventDefault(); setOpen(false); }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                使用「{value}」作為新客戶
              </div>
            </>
          )}
          {filtered.map((c, i) => (
            <div key={c}
              className={"ac-item" + (i === activeIdx ? " active" : "")}
              onMouseEnter={() => setActiveIdx(i)}
              onMouseDown={e => { e.preventDefault(); selectItem(c); }}
            >{highlight(c)}</div>
          ))}
        </div>
      )}
    </div>
  );
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
      .then((r: any) => { const d = r?.data || r; if (d?.companies) setCompanies(d.companies); })
      .catch(() => {});
  }, []);

  const handleDescChange = (text: string) => {
    setDesc(text);
    clearTimeout(timerRef.current);
    if (text.length < 20) { setPreview(null); return; }
    setPreviewLoading(true);
    timerRef.current = setTimeout(() => {
      runAction("sales_log", { action: "ai_preview", description: text })
        .then((r: any) => { setPreview(r?.data || r); setPreviewLoading(false); })
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
      .then((r: any) => { setPreview(r?.data || r); setPreviewLoading(false); })
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
        setModal(r?.data || r);
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
              <CompanyAutocomplete
                companies={companies}
                value={company}
                onChange={setCompany}
                placeholder="輸入關鍵字搜尋或選擇客戶"
              />
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
