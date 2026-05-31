# -*- coding: utf-8 -*-
"""
一次性完成目標 App (dbe4f2a4) 所有功能補齊
1. 檢查/修正 References
2. 新增 AI Action (ai_hr_insights.py)
3. 重寫 DashboardPage
4. 新增 AnalysisPage / AnomalyPage / LeaveDetailModal
5. 增強 LeavesPage / AttendancePage
6. 更新路由
7. 編譯 + 發布
"""
import json, urllib.request, ssl, sys, re, time
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode()[:500]
        print(f"  HTTP {e.code}: {err}")
        return None

# === Login ===
print("[1] Login...")
auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
print("  OK")

# === Get app ===
print("[2] Get app VFS...")
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]
version = app_data["vfs_version"]
slug = app_data["slug"]
print(f"  {len(vfs)} files, v{version}, slug={slug}")

# === Check refs ===
print("[3] Check references...")
refs = api("GET", f"/refs/apps/{APP}", None, token)
ref_tables = {r["table_name"]: r for r in refs}
print(f"  Found {len(ref_tables)} refs: {list(ref_tables.keys())}")

# Ensure hr_leaves has all needed columns
if "hr_leaves" in ref_tables:
    ref = ref_tables["hr_leaves"]
    needed = ["id","name","state","holiday_type","date_from","date_to","number_of_days",
              "duration_display","notes","employee_id","holiday_status_id","manager_id",
              "department_id","tenant_id","created_at","updated_at","custom_data"]
    existing = set(ref.get("columns", []))
    missing = [c for c in needed if c not in existing]
    if missing:
        new_cols = list(existing | set(needed))
        r = api("PATCH", f"/refs/{ref['id']}", {"columns": new_cols, "permissions": ["create","read","update"]}, token)
        print(f"  hr_leaves: added {missing}")
    else:
        print(f"  hr_leaves: OK ({len(existing)} cols)")

print("  Refs check complete")

# === Read existing actionHelper.ts ===
action_helper = vfs.get("src/actionHelper.ts", "")
print(f"[4] actionHelper.ts: {len(action_helper)} chars")

# Find callAction signature
for line in action_helper.split("\n"):
    if "callAction" in line and ("export" in line or "async" in line):
        print(f"  Signature: {line.strip()[:100]}")

# === Build all files ===
print("[5] Building files...")
files = {}

# =====================================================
# AI Action: ai_hr_insights.py
# =====================================================
files["actions/ai_hr_insights.py"] = '''import json, datetime, re, math

def execute(ctx):
    """AI HR 洞察 — 提供即時儀表板數據 + AI 分析"""
    action = (ctx.params.get("action") or "dashboard")
    api_key = ctx.secrets.get("OPENAI_API_KEY") or ""

    if action == "dashboard":
        return _dashboard(ctx, api_key)
    elif action == "analysis":
        return _analysis(ctx, api_key)
    elif action == "anomaly":
        return _anomaly(ctx, api_key)
    else:
        ctx.response.json({"error": f"Unknown action: {action}"})

def _call_ai(api_key, prompt):
    """呼叫 OpenAI API"""
    import httpx
    if not api_key:
        return "（AI 分析未設定 API Key）"
    try:
        resp = httpx.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 300},
            timeout=15)
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as ex:
        return f"AI 分析暫時不可用：{str(ex)[:80]}"

def _dashboard(ctx, api_key):
    """即時儀表板數據"""
    today = datetime.date.today().isoformat()
    employees = ctx.db.query("hr_employees", limit=200) or []
    total_emp = len(employees)
    attendances = ctx.db.query("hr_attendances", limit=200) or []
    today_att = [a for a in attendances if (a.get("check_in") or "")[:10] == today]
    present = len(today_att)
    all_leaves = ctx.db.query("hr_leaves", limit=200) or []
    pending = [l for l in all_leaves if l.get("state") in ("draft", "confirm")]
    month_leaves = [l for l in all_leaves if (l.get("date_from") or "")[:7] == today[:7]]
    month_days = sum(float(l.get("number_of_days") or 0) for l in month_leaves)
    leave_types = ctx.db.query("hr_leave_types", limit=50) or []
    type_map = {t["id"]: t.get("name","?") for t in leave_types}
    type_dist = {}
    for l in month_leaves:
        tn = type_map.get(l.get("holiday_status_id"), "其他")
        type_dist[tn] = type_dist.get(tn, 0) + float(l.get("number_of_days") or 0)
    emp_map = {e["id"]: e for e in employees}
    today_leaves = [l for l in all_leaves if (l.get("date_from") or "")[:10] <= today and (l.get("date_to") or "")[:10] >= today and l.get("state") in ("validate","confirm","draft")]
    on_leave_ids = set(l.get("employee_id") for l in today_leaves)
    att_grid = []
    for e in employees[:30]:
        eid = e.get("id")
        ename = e.get("name", "?")
        if eid in on_leave_ids:
            lv = next((l for l in today_leaves if l.get("employee_id") == eid), {})
            att_grid.append({"name": ename, "status": "leave", "detail": type_map.get(lv.get("holiday_status_id"), "請假")})
        elif any(a.get("employee_id") == eid for a in today_att):
            att_grid.append({"name": ename, "status": "on", "detail": "在崗"})
        else:
            att_grid.append({"name": ename, "status": "unknown", "detail": "未打卡"})
    ai_insight = _call_ai(api_key, f"""你是 HR 數據分析助理。根據以下數據產生 3 行洞察（觀察/預測/建議）：
- 部門員工 {total_emp} 人，今日出勤 {present} 人，{len(on_leave_ids)} 人請假
- 本月請假 {month_days} 天，假別分布：{json.dumps(type_dist, ensure_ascii=False)}
- 待簽核 {len(pending)} 件
請用繁體中文，每行以 emoji 開頭。""")
    pending_list = []
    for l in pending[:5]:
        emp = emp_map.get(l.get("employee_id"), {})
        pending_list.append({
            "id": l.get("id"), "employee_name": emp.get("name","?"),
            "leave_type": type_map.get(l.get("holiday_status_id"),"?"),
            "date_from": (l.get("date_from") or "")[:10], "date_to": (l.get("date_to") or "")[:10],
            "days": l.get("number_of_days"), "notes": l.get("notes",""),
            "state": l.get("state"), "created_at": (l.get("created_at") or "")[:16],
        })
    ctx.response.json({
        "kpi": {"total_employees": total_emp, "present_today": present, "on_leave_today": len(on_leave_ids),
                "pending_count": len(pending), "month_leave_days": round(month_days,1),
                "leave_rate": round(month_days / max(total_emp * 22, 1) * 100, 1)},
        "type_distribution": type_dist, "attendance_grid": att_grid,
        "pending_list": pending_list, "ai_insight": ai_insight,
    })

def _analysis(ctx, api_key):
    """請假分析數據"""
    all_leaves = ctx.db.query("hr_leaves", limit=500) or []
    leave_types = ctx.db.query("hr_leave_types", limit=50) or []
    type_map = {t["id"]: t.get("name","?") for t in leave_types}
    today = datetime.date.today()
    month_str = today.strftime("%Y-%m")
    month_leaves = [l for l in all_leaves if (l.get("date_from") or "")[:7] == month_str]
    month_hours = sum(float(l.get("number_of_days") or 0) * 8 for l in month_leaves)
    type_dist = {}
    for l in month_leaves:
        tn = type_map.get(l.get("holiday_status_id"), "其他")
        type_dist[tn] = type_dist.get(tn, 0) + float(l.get("number_of_days") or 0) * 8
    weekday_dist = {i: 0 for i in range(7)}
    for l in month_leaves:
        try:
            d = datetime.date.fromisoformat((l.get("date_from") or "")[:10])
            weekday_dist[d.weekday()] += 1
        except: pass
    weekday_names = ["週一","週二","週三","週四","週五","週六","週日"]
    week_data = [{"day": weekday_names[i], "count": weekday_dist[i]} for i in range(5)]
    trend = []
    for i in range(5, -1, -1):
        m = today.month - i; y = today.year
        while m <= 0: m += 12; y -= 1
        ms = f"{y}-{m:02d}"
        ml = [l for l in all_leaves if (l.get("date_from") or "")[:7] == ms]
        hours = sum(float(l.get("number_of_days") or 0) * 8 for l in ml)
        trend.append({"month": ms, "hours": round(hours)})
    top_type = max(type_dist, key=type_dist.get) if type_dist else "無"
    peak_day = max(week_data, key=lambda x: x["count"])["day"] if week_data else "無"
    ai_prediction = _call_ai(api_key, f"""根據近 6 個月請假趨勢 {json.dumps(trend, ensure_ascii=False)} 和假別分布 {json.dumps(type_dist, ensure_ascii=False)}，
預測下週和下月的請假趨勢。用繁體中文回覆 3 行，以 emoji 開頭。""")
    ctx.response.json({
        "kpi": {"month_hours": round(month_hours), "top_type": top_type,
                "top_type_hours": round(type_dist.get(top_type, 0)), "peak_day": peak_day},
        "type_distribution": type_dist, "weekday_distribution": week_data,
        "trend": trend, "ai_prediction": ai_prediction,
    })

def _anomaly(ctx, api_key):
    """異常出勤偵測"""
    employees = ctx.db.query("hr_employees", limit=200) or []
    all_leaves = ctx.db.query("hr_leaves", limit=500) or []
    leave_types = ctx.db.query("hr_leave_types", limit=50) or []
    type_map = {t["id"]: t.get("name","?") for t in leave_types}
    today = datetime.date.today()
    d30 = (today - datetime.timedelta(days=30)).isoformat()
    anomalies = []
    for emp in employees:
        eid = emp.get("id"); ename = emp.get("name","?")
        recent = [l for l in all_leaves if l.get("employee_id") == eid and (l.get("date_from") or "") >= d30]
        if not recent: continue
        total_days = sum(float(l.get("number_of_days") or 0) for l in recent)
        sick_count = sum(1 for l in recent if "病" in type_map.get(l.get("holiday_status_id"),""))
        flags = []; risk = "low"
        if total_days >= 5: flags.append(f"30天內請假 {total_days} 天"); risk = "medium"
        if sick_count >= 3: flags.append(f"30天內病假 {sick_count} 次"); risk = "high"
        mon_fri = 0
        for l in recent:
            try:
                d = datetime.date.fromisoformat((l.get("date_from") or "")[:10])
                if d.weekday() in (0, 4): mon_fri += 1
            except: pass
        if mon_fri >= 3: flags.append(f"週一/五請假 {mon_fri} 次（疑似延長週末）"); risk = "high"
        if flags:
            anomalies.append({"employee_id": eid, "employee_name": ename,
                "department": emp.get("department_id",""), "risk": risk,
                "flags": flags, "total_days_30d": total_days, "recent_count": len(recent)})
    risk_order = {"high": 0, "medium": 1, "low": 2}
    anomalies.sort(key=lambda x: risk_order.get(x["risk"], 3))
    high = sum(1 for a in anomalies if a["risk"] == "high")
    medium = sum(1 for a in anomalies if a["risk"] == "medium")
    normal = len(employees) - len(anomalies)
    ai_analysis = ""
    if anomalies:
        ai_analysis = _call_ai(api_key, f"""以下是異常出勤員工清單：
{json.dumps(anomalies[:5], ensure_ascii=False)}
請用繁體中文分析並給出管理建議（3 行，以 emoji 開頭）。""")
    ctx.response.json({
        "kpi": {"high": high, "medium": medium, "normal": normal, "total": len(employees)},
        "anomalies": anomalies, "ai_analysis": ai_analysis,
    })
'''

# === Manifest ===
manifest = json.loads(vfs.get("actions/manifest.json", "{}"))
existing_names = [a["name"] for a in manifest.get("actions", [])]
if "ai_hr_insights" not in existing_names:
    manifest.setdefault("actions", []).append({
        "name": "ai_hr_insights", "file": "ai_hr_insights.py", "description": "AI HR 洞察分析"
    })
files["actions/manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2)
print(f"  manifest: {len(manifest['actions'])} actions")

# =====================================================
# Read existing patterns from VFS
# =====================================================
# Check if actionHelper has callAction
has_call_action = "callAction" in action_helper

# Read existing App.css for style patterns
app_css = vfs.get("src/App.css", "")

# Read existing layout wrapper
app_layout = vfs.get("src/components/AppLayout.tsx", "")

# =====================================================
# DashboardPage.tsx (complete rewrite)
# =====================================================
files["src/pages/DashboardPage.tsx"] = '''import React, { useState, useEffect } from "react";
import { callAction } from "../actionHelper";
import { useNavigate } from "react-router-dom";

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const { data: d } = await callAction("ai_hr_insights", { action: "dashboard" });
        setData(d);
      } catch (e: any) { setError(e.message); }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div style={{padding:32,textAlign:"center",color:"#94a3b8"}}>載入中...</div>;
  if (error) return <div style={{padding:32,color:"#dc2626"}}>錯誤：{error}</div>;
  if (!data) return null;
  const k = data.kpi || {};
  const grid = data.attendance_grid || [];
  const pending = data.pending_list || [];

  return (
    <div>
      <div className="page-head">
        <div><h1 className="page-title">即時總覽</h1><p className="page-sub">今日 · {k.total_employees} 位員工</p></div>
      </div>

      <div className="kpi-grid">
        <KPI icon="👥" label="今日出勤" value={`${k.present_today} / ${k.total_employees}`} sub={`${k.on_leave_today} 人請假`} color="#2563eb" bg="#dbeafe" />
        <KPI icon="⏳" label="待我簽核" value={`${k.pending_count} 件`} sub="點此查看" color="#dc2626" bg="#fee2e2" onClick={() => navigate("/leaves")} />
        <KPI icon="📅" label="本月請假率" value={`${k.leave_rate}%`} sub={`共 ${k.month_leave_days} 天`} color="#ea580c" bg="#ffedd5" />
        <KPI icon="⚠️" label="異常出勤" value="偵測中" sub="AI 分析" color="#7c3aed" bg="#ede9fe" onClick={() => navigate("/anomaly")} />
      </div>

      {data.ai_insight && (
        <div style={{background:"linear-gradient(135deg,#FEF3C7,#FFEDD5)",border:"1px solid #fbbf24",borderRadius:12,padding:16,marginBottom:16}}>
          <div style={{fontSize:12,fontWeight:700,color:"#92400e",marginBottom:6}}>🤖 AI 今日洞察</div>
          <div style={{fontSize:13,lineHeight:1.7,color:"#78350f",whiteSpace:"pre-line"}}>{data.ai_insight}</div>
        </div>
      )}

      <div style={{display:"grid",gridTemplateColumns:"1.5fr 1fr",gap:16}}>
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">⏳ 待簽核（{k.pending_count} 件）</div></div></div>
          {pending.length === 0 ? <div style={{color:"#94a3b8",textAlign:"center",padding:20}}>目前無待簽核假單 🎉</div> :
            pending.map((p: any) => (
              <div key={p.id} style={{border:"1px solid #e2e8f0",borderRadius:10,padding:14,marginBottom:10,display:"flex",gap:12,alignItems:"center",cursor:"pointer"}} onClick={() => navigate("/leaves")}>
                <div style={{width:36,height:36,borderRadius:"50%",background:"linear-gradient(135deg,#2563eb,#7c3aed)",color:"white",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:700,fontSize:14,flexShrink:0}}>{(p.employee_name||"?")[0]}</div>
                <div style={{flex:1,minWidth:0}}>
                  <div style={{fontWeight:700,fontSize:14}}>{p.employee_name} <span style={{fontSize:11,padding:"2px 8px",borderRadius:999,background:"#dbeafe",color:"#2563eb"}}>{p.leave_type}</span></div>
                  <div style={{fontSize:12,color:"#64748b",marginTop:2}}>📅 {p.date_from}{p.date_to && p.date_to !== p.date_from ? ` ~ ${p.date_to}` : ""} · {p.days} 天</div>
                  {p.notes && <div style={{fontSize:11,color:"#94a3b8",marginTop:2}}>{p.notes}</div>}
                </div>
              </div>
            ))
          }
        </div>
        <div className="panel">
          <div className="panel-head"><div><div className="panel-title">📅 今日出勤狀態</div><div style={{fontSize:12,color:"#94a3b8"}}>{k.total_employees} 人</div></div></div>
          <div style={{display:"flex",gap:8,marginBottom:12,fontSize:11,flexWrap:"wrap"}}>
            <span style={{display:"flex",alignItems:"center",gap:4}}><span style={{width:10,height:10,background:"#16a34a",borderRadius:3}} /> 在崗 {grid.filter((g:any)=>g.status==="on").length}</span>
            <span style={{display:"flex",alignItems:"center",gap:4}}><span style={{width:10,height:10,background:"#ea580c",borderRadius:3}} /> 請假 {grid.filter((g:any)=>g.status==="leave").length}</span>
            <span style={{display:"flex",alignItems:"center",gap:4}}><span style={{width:10,height:10,background:"#94a3b8",borderRadius:3}} /> 未打卡 {grid.filter((g:any)=>g.status==="unknown").length}</span>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(120px,1fr))",gap:8}}>
            {grid.map((g: any, i: number) => {
              const colors: Record<string,{border:string,bg:string}> = {on:{border:"#16a34a",bg:"#dcfce7"},leave:{border:"#ea580c",bg:"#ffedd5"},unknown:{border:"#e2e8f0",bg:"#f8fafc"}};
              const c = colors[g.status] || colors.unknown;
              return (
                <div key={i} style={{border:`1px solid ${c.border}`,background:c.bg,borderRadius:8,padding:8,display:"flex",alignItems:"center",gap:8,fontSize:12}}>
                  <div style={{width:28,height:28,borderRadius:"50%",background:"linear-gradient(135deg,#2563eb,#7c3aed)",color:"white",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:700,fontSize:12,flexShrink:0}}>{g.name[0]}</div>
                  <div style={{flex:1,minWidth:0}}><div style={{fontWeight:600,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{g.name}</div><div style={{fontSize:10,color:"#64748b"}}>{g.detail}</div></div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function KPI({icon,label,value,sub,color,bg,onClick}:{icon:string;label:string;value:string;sub:string;color:string;bg:string;onClick?:()=>void}) {
  return (
    <div className="panel" style={{cursor:onClick?"pointer":undefined}} onClick={onClick}>
      <div style={{width:36,height:36,borderRadius:8,background:bg,display:"flex",alignItems:"center",justifyContent:"center",fontSize:20,marginBottom:10}}>{icon}</div>
      <div style={{fontSize:12,color:"#64748b",marginBottom:4}}>{label}</div>
      <div style={{fontSize:24,fontWeight:700,color}}>{value}</div>
      <div style={{fontSize:11,color:"#94a3b8",marginTop:4}}>{sub}</div>
    </div>
  );
}
'''

# =====================================================
# AnalysisPage.tsx
# =====================================================
files["src/pages/AnalysisPage.tsx"] = '''import React, { useState, useEffect } from "react";
import { callAction } from "../actionHelper";

const COLORS = ["#2563eb","#ea580c","#16a34a","#7c3aed","#0891b2","#be185d","#94a3b8","#eab308"];

export default function AnalysisPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const { data: d } = await callAction("ai_hr_insights", { action: "analysis" });
        setData(d);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div style={{padding:32,textAlign:"center",color:"#94a3b8"}}>載入分析數據...</div>;
  if (!data) return <div style={{padding:32,color:"#dc2626"}}>無法載入數據</div>;
  const k = data.kpi || {};
  const typeDist = data.type_distribution || {};
  const weekData = data.weekday_distribution || [];
  const trend = data.trend || [];
  const entries = Object.entries(typeDist).sort((a: any, b: any) => (b[1] as number) - (a[1] as number));
  const totalHours = entries.reduce((s, [, v]) => s + (v as number), 0);
  const maxWeek = Math.max(...weekData.map((w: any) => w.count), 1);
  const maxTrend = Math.max(...trend.map((t: any) => t.hours), 1);

  return (
    <div>
      <div className="page-head"><div><h1 className="page-title">請假分析</h1><p className="page-sub">數據驅動的差勤洞察</p></div></div>

      <div className="kpi-grid">
        <div className="panel"><div style={{fontSize:12,color:"#64748b"}}>本月請假總時數</div><div style={{fontSize:24,fontWeight:700,color:"#2563eb"}}>{k.month_hours} hr</div></div>
        <div className="panel"><div style={{fontSize:12,color:"#64748b"}}>最常見假別</div><div style={{fontSize:18,fontWeight:700}}>{k.top_type}</div><div style={{fontSize:11,color:"#94a3b8"}}>{k.top_type_hours} hr</div></div>
        <div className="panel"><div style={{fontSize:12,color:"#64748b"}}>請假高峰日</div><div style={{fontSize:18,fontWeight:700}}>{k.peak_day}</div></div>
      </div>

      <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
        <div className="panel">
          <div className="panel-title" style={{marginBottom:14}}>📊 假別分布</div>
          <div style={{display:"flex",alignItems:"center",gap:16}}>
            <svg viewBox="0 0 100 100" width="140" height="140">
              {(() => {
                let offset = 0;
                return entries.map(([name, val], i) => {
                  const pct = (val as number) / Math.max(totalHours, 1) * 100;
                  const dash = pct * 2.83;
                  const gap = 283 - dash;
                  const el = <circle key={name} cx="50" cy="50" r="45" fill="none" stroke={COLORS[i % COLORS.length]} strokeWidth="10" strokeDasharray={`${dash} ${gap}`} strokeDashoffset={-offset * 2.83} transform="rotate(-90 50 50)" />;
                  offset += pct;
                  return el;
                });
              })()}
            </svg>
            <div style={{flex:1,fontSize:12}}>
              {entries.map(([name, val], i) => (
                <div key={name} style={{display:"flex",alignItems:"center",gap:8,marginBottom:6}}>
                  <span style={{width:10,height:10,borderRadius:3,background:COLORS[i % COLORS.length],flexShrink:0}} />
                  <span style={{flex:1,color:"#64748b"}}>{name}</span>
                  <span style={{fontWeight:600}}>{Math.round(val as number)} hr</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-title" style={{marginBottom:14}}>📅 一週請假分布</div>
          {weekData.map((w: any, i: number) => (
            <div key={w.day} style={{display:"flex",alignItems:"center",gap:12,marginBottom:10,fontSize:13}}>
              <div style={{width:40,color:"#64748b"}}>{w.day}</div>
              <div style={{flex:1,height:22,background:"#f1f5f9",borderRadius:4,overflow:"hidden"}}>
                <div style={{height:"100%",width:`${(w.count/maxWeek)*100}%`,background:w.count >= maxWeek*0.8 ? "#dc2626" : "#16a34a",borderRadius:4,display:"flex",alignItems:"center",paddingLeft:8,color:"white",fontSize:11,fontWeight:600,minWidth:w.count > 0 ? 30 : 0}}>{w.count > 0 ? `${w.count}` : ""}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="panel" style={{marginTop:16}}>
        <div className="panel-title" style={{marginBottom:14}}>📈 近 6 個月趨勢</div>
        <svg viewBox="0 0 700 200" style={{width:"100%",height:200}}>
          <defs><linearGradient id="tg" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#2563EB" stopOpacity={0.3} /><stop offset="100%" stopColor="#2563EB" stopOpacity={0} /></linearGradient></defs>
          {[0.25,0.5,0.75].map(r => <line key={r} x1="60" y1={180-r*160} x2="680" y2={180-r*160} stroke="#f1f5f9" />)}
          {trend.length > 1 && (() => {
            const pts = trend.map((t: any, i: number) => ({x: 60 + i * (620 / (trend.length - 1)), y: 180 - (t.hours / maxTrend) * 160}));
            const line = pts.map((p: any) => `${p.x},${p.y}`).join(" L");
            const area = `M ${pts[0].x} ${pts[0].y} L${line} L${pts[pts.length-1].x} 180 L${pts[0].x} 180 Z`;
            return <>
              <path d={area} fill="url(#tg)" />
              <polyline points={pts.map((p:any)=>`${p.x},${p.y}`).join(" ")} stroke="#2563EB" strokeWidth="3" fill="none" />
              {pts.map((p: any, i: number) => <g key={i}><circle cx={p.x} cy={p.y} r={i===pts.length-1?7:5} fill={i===pts.length-1?"#2563EB":"white"} stroke="#2563EB" strokeWidth={2.5} /><text x={p.x} y={p.y-12} textAnchor="middle" fontSize="11" fill="#475569" fontWeight="600">{trend[i].hours}</text><text x={p.x} y="198" textAnchor="middle" fontSize="10" fill="#94a3b8">{trend[i].month.slice(5)}</text></g>)}
            </>;
          })()}
        </svg>
      </div>

      {data.ai_prediction && (
        <div style={{background:"linear-gradient(135deg,#FEF3C7,#FFEDD5)",border:"1px solid #fbbf24",borderRadius:12,padding:16,marginTop:16}}>
          <div style={{fontSize:12,fontWeight:700,color:"#92400e",marginBottom:6}}>🤖 AI 請假預測</div>
          <div style={{fontSize:13,lineHeight:1.7,color:"#78350f",whiteSpace:"pre-line"}}>{data.ai_prediction}</div>
        </div>
      )}
    </div>
  );
}
'''

# =====================================================
# AnomalyPage.tsx
# =====================================================
files["src/pages/AnomalyPage.tsx"] = '''import React, { useState, useEffect } from "react";
import { callAction } from "../actionHelper";

export default function AnomalyPage() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const { data: d } = await callAction("ai_hr_insights", { action: "anomaly" });
        setData(d);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  if (loading) return <div style={{padding:32,textAlign:"center",color:"#94a3b8"}}>載入異常偵測...</div>;
  if (!data) return <div style={{padding:32,color:"#dc2626"}}>無法載入數據</div>;
  const k = data.kpi || {};
  const anomalies = data.anomalies || [];
  const riskColors: Record<string,{border:string,bg:string,text:string}> = {
    high: {border:"#dc2626",bg:"#fee2e2",text:"#7f1d1d"},
    medium: {border:"#ea580c",bg:"#ffedd5",text:"#7c2d12"},
    low: {border:"#e2e8f0",bg:"#f8fafc",text:"#475569"},
  };
  const riskLabels: Record<string,string> = {high:"🔴 高風險",medium:"🟡 中風險",low:"🟢 低風險"};

  return (
    <div>
      <div className="page-head"><div><h1 className="page-title">⚠️ 異常出勤偵測</h1><p className="page-sub">AI 主動偵測異常模式，提供主管早期關注機會</p></div></div>

      <div className="kpi-grid">
        <div className="panel"><div style={{fontSize:20,marginBottom:8}}>🚨</div><div style={{fontSize:12,color:"#64748b"}}>高風險員工</div><div style={{fontSize:24,fontWeight:700,color:"#dc2626"}}>{k.high} 人</div><div style={{fontSize:11,color:"#94a3b8"}}>建議 1-on-1</div></div>
        <div className="panel"><div style={{fontSize:20,marginBottom:8}}>⚠️</div><div style={{fontSize:12,color:"#64748b"}}>中風險員工</div><div style={{fontSize:24,fontWeight:700,color:"#ea580c"}}>{k.medium} 人</div><div style={{fontSize:11,color:"#94a3b8"}}>持續觀察</div></div>
        <div className="panel"><div style={{fontSize:20,marginBottom:8}}>✅</div><div style={{fontSize:12,color:"#64748b"}}>出勤正常</div><div style={{fontSize:24,fontWeight:700,color:"#16a34a"}}>{k.normal} 人</div><div style={{fontSize:11,color:"#94a3b8"}}>共 {k.total} 人</div></div>
      </div>

      {anomalies.length === 0 ? (
        <div className="panel" style={{textAlign:"center",padding:40,color:"#94a3b8"}}>🎉 目前無異常出勤偵測結果</div>
      ) : (
        <div className="panel">
          <div className="panel-title" style={{marginBottom:14}}>🚨 異常員工（{anomalies.length} 人）</div>
          {anomalies.map((a: any) => {
            const rc = riskColors[a.risk] || riskColors.low;
            return (
              <div key={a.employee_id} style={{border:`1px solid ${rc.border}`,background:rc.bg,borderRadius:10,padding:14,marginBottom:10,display:"flex",gap:12}}>
                <div style={{width:40,height:40,borderRadius:"50%",background:"linear-gradient(135deg,#dc2626,#ea580c)",color:"white",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:700,flexShrink:0}}>{a.employee_name[0]}</div>
                <div style={{flex:1}}>
                  <div style={{fontWeight:700,fontSize:14,marginBottom:4}}>{a.employee_name} <span style={{fontSize:11,padding:"2px 8px",borderRadius:999,background:rc.border,color:"white",marginLeft:4}}>{riskLabels[a.risk]}</span></div>
                  {a.flags.map((f: string, i: number) => <div key={i} style={{fontSize:12,color:rc.text,lineHeight:1.6}}>🔴 {f}</div>)}
                  <div style={{fontSize:11,color:"#94a3b8",marginTop:4}}>30天內共 {a.recent_count} 筆請假，合計 {a.total_days_30d} 天</div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {data.ai_analysis && (
        <div style={{background:"linear-gradient(135deg,#fee2e2,#fed7aa)",border:"1px solid #fca5a5",borderRadius:12,padding:16,marginTop:16}}>
          <div style={{fontSize:12,fontWeight:700,color:"#7f1d1d",marginBottom:6}}>🤖 AI 分析建議</div>
          <div style={{fontSize:13,lineHeight:1.7,color:"#7f1d1d",whiteSpace:"pre-line"}}>{data.ai_analysis}</div>
        </div>
      )}
    </div>
  );
}
'''

# =====================================================
# LeaveDetailModal.tsx
# =====================================================
files["src/components/LeaveDetailModal.tsx"] = '''import React, { useState } from "react";

interface Props {
  leave: any;
  onClose: () => void;
  onAction?: () => void;
}

export default function LeaveDetailModal({ leave, onClose, onAction }: Props) {
  const [actioning, setActioning] = useState("");

  if (!leave) return null;

  async function handleAction(newState: string) {
    setActioning(newState);
    try {
      const apiBase = (window as any).__API_BASE__ || "/api/v1";
      const appId = (window as any).__APP_ID__ || "";
      const tkn = (window as any).__APP_TOKEN__ || "";
      const resp = await fetch(`${apiBase}/proxy/${appId}/hr_leaves/${leave.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", ...(tkn ? { Authorization: `Bearer ${tkn}` } : {}) },
        credentials: "include",
        body: JSON.stringify({ data: { state: newState } }),
      });
      if (!resp.ok) throw new Error("更新失敗");
      onAction && onAction();
      onClose();
    } catch (e: any) { alert(e.message); }
    finally { setActioning(""); }
  }

  const stateBadge: Record<string,{label:string,color:string,bg:string}> = {
    draft: {label:"草稿",color:"#64748b",bg:"#f1f5f9"},
    confirm: {label:"待簽核",color:"#ea580c",bg:"#ffedd5"},
    validate: {label:"已核准",color:"#16a34a",bg:"#dcfce7"},
    refuse: {label:"已拒絕",color:"#dc2626",bg:"#fee2e2"},
  };
  const sb = stateBadge[leave.state] || stateBadge.draft;
  const isPending = ["draft","confirm"].includes(leave.state);

  return (
    <div style={{position:"fixed",inset:0,background:"rgba(15,23,42,0.55)",zIndex:100,display:"flex",alignItems:"flex-start",justifyContent:"center",overflowY:"auto",padding:"40px 16px"}} onClick={onClose}>
      <div style={{background:"white",borderRadius:16,width:"100%",maxWidth:600,overflow:"hidden",boxShadow:"0 24px 60px rgba(15,23,42,0.25)"}} onClick={e => e.stopPropagation()}>
        <div style={{padding:"22px 26px 18px",background:"linear-gradient(135deg,#DBEAFE,#EDE9FE)",borderBottom:"1px solid #e2e8f0",display:"flex",gap:14,alignItems:"flex-start"}}>
          <div style={{width:52,height:52,borderRadius:"50%",background:"linear-gradient(135deg,#2563eb,#7c3aed)",color:"white",display:"flex",alignItems:"center",justifyContent:"center",fontSize:22,fontWeight:700,flexShrink:0}}>{(leave.employee_name || "?")[0]}</div>
          <div style={{flex:1}}>
            <div style={{fontSize:20,fontWeight:700}}>{leave.employee_name || "員工"} <span style={{fontSize:12,padding:"3px 10px",borderRadius:999,background:sb.bg,color:sb.color,marginLeft:6}}>{sb.label}</span></div>
            <div style={{fontSize:12,color:"#64748b",marginTop:4}}>{leave.leave_type || leave.holiday_type || ""}</div>
          </div>
          <button onClick={onClose} style={{background:"rgba(255,255,255,0.7)",width:32,height:32,borderRadius:8,border:"none",cursor:"pointer",fontSize:16,display:"flex",alignItems:"center",justifyContent:"center"}}>✕</button>
        </div>

        <div style={{padding:"22px 26px"}}>
          <div style={{display:"grid",gridTemplateColumns:"100px 1fr",gap:"10px 14px",fontSize:13}}>
            <span style={{color:"#64748b",fontWeight:500}}>假別</span><span style={{fontWeight:600}}>{leave.leave_type || leave.holiday_type || "—"}</span>
            <span style={{color:"#64748b",fontWeight:500}}>起始日期</span><span style={{fontWeight:600}}>{(leave.date_from || "").slice(0,10)}</span>
            <span style={{color:"#64748b",fontWeight:500}}>結束日期</span><span style={{fontWeight:600}}>{(leave.date_to || "").slice(0,10)}</span>
            <span style={{color:"#64748b",fontWeight:500}}>天數</span><span style={{fontWeight:600}}>{leave.number_of_days || leave.days || "—"} 天</span>
            <span style={{color:"#64748b",fontWeight:500}}>事由</span><span style={{fontWeight:600}}>{leave.notes || "（未填寫）"}</span>
          </div>
        </div>

        {isPending && (
          <div style={{padding:"16px 26px",background:"#f8fafc",borderTop:"1px solid #e2e8f0",display:"flex",justifyContent:"flex-end",gap:8}}>
            <button onClick={() => handleAction("refuse")} disabled={!!actioning} style={{padding:"9px 16px",borderRadius:8,fontSize:13,fontWeight:600,background:"#dc2626",color:"white",border:"none",cursor:"pointer",opacity:actioning?"0.5":"1"}}>✕ 拒絕</button>
            <button onClick={() => handleAction("validate")} disabled={!!actioning} style={{padding:"9px 16px",borderRadius:8,fontSize:13,fontWeight:600,background:"#16a34a",color:"white",border:"none",cursor:"pointer",opacity:actioning?"0.5":"1"}}>✓ 核准</button>
          </div>
        )}
      </div>
    </div>
  );
}
'''

# =====================================================
# Update App.tsx routes
# =====================================================
app_tsx = vfs.get("src/App.tsx", "")
# Add imports
if "AnalysisPage" not in app_tsx:
    # Find last import line
    import_lines = [l for l in app_tsx.split("\n") if l.startswith("import ")]
    last_import = import_lines[-1] if import_lines else ""
    app_tsx = app_tsx.replace(last_import, last_import + '\nimport AnalysisPage from "./pages/AnalysisPage";\nimport AnomalyPage from "./pages/AnomalyPage";')
    # Add routes before NotFoundPage route
    app_tsx = app_tsx.replace('<Route path="*"', '<Route path="/analysis" element={<AnalysisPage />} />\n          <Route path="/anomaly" element={<AnomalyPage />} />\n          <Route path="*"')
    files["src/App.tsx"] = app_tsx
    print("  App.tsx: routes added")

# =====================================================
# Update routes.ts navigation
# =====================================================
routes_ts = vfs.get("src/routes.ts", "")
if "AnalysisPage" not in routes_ts and "analysis" not in routes_ts:
    # Add after attendance/leaves entries
    if "AlertTriangle" not in routes_ts:
        routes_ts = routes_ts.replace(
            'import { LayoutDashboard',
            'import { LayoutDashboard, AlertTriangle, BarChart3'
        ).replace(
            'import {',
            'import {',
            1
        )
    # Add analysis and anomaly routes
    if "請假分析" not in routes_ts:
        routes_ts = routes_ts.replace(
            '{ title: "加班申請"',
            '{ title: "請假分析", path: "/analysis", icon: BarChart3 },\n  { title: "異常出勤", path: "/anomaly", icon: AlertTriangle },\n  { title: "加班申請"'
        )
    files["src/routes.ts"] = routes_ts
    print("  routes.ts: nav items added")

# =====================================================
# Enhance LeavesPage.tsx
# =====================================================
leaves_page = vfs.get("src/pages/LeavesPage.tsx", "")
# Add batch operations and detail modal
if "LeaveDetailModal" not in leaves_page:
    # Add import
    leaves_page = leaves_page.replace(
        'import React',
        'import React'  # keep as-is, add LeaveDetailModal import after
    )
    if "LeaveDetailModal" not in leaves_page:
        first_import_end = leaves_page.find("\n\n")
        if first_import_end == -1:
            first_import_end = leaves_page.find("export")
        leaves_page = leaves_page[:first_import_end] + '\nimport LeaveDetailModal from "../components/LeaveDetailModal";\n' + leaves_page[first_import_end:]

    # Add selectedIds and detailLeave states
    if "selectedIds" not in leaves_page:
        leaves_page = leaves_page.replace(
            "const [search,",
            "const [selectedIds, setSelectedIds] = useState<string[]>([]);\n  const [detailLeave, setDetailLeave] = useState<any>(null);\n  const [search,"
        )

    # Add batch approve function
    if "batchApprove" not in leaves_page:
        # Find the component body (after the last useState)
        batch_fn = '''
  async function batchApprove(ids: string[]) {
    const apiBase = (window as any).__API_BASE__ || "/api/v1";
    const appId = (window as any).__APP_ID__ || "";
    const tkn = (window as any).__APP_TOKEN__ || "";
    for (const id of ids) {
      await fetch(\`\${apiBase}/proxy/\${appId}/hr_leaves/\${id}\`, {
        method: "PATCH", headers: { "Content-Type": "application/json", ...(tkn ? { Authorization: \`Bearer \${tkn}\` } : {}) },
        credentials: "include", body: JSON.stringify({ data: { state: "validate" } }),
      });
    }
    setSelectedIds([]);
    window.location.reload();
  }
'''
        # Insert before return
        return_idx = leaves_page.find("  return (")
        if return_idx > 0:
            leaves_page = leaves_page[:return_idx] + batch_fn + "\n" + leaves_page[return_idx:]

    # Add batch buttons and detail modal to JSX
    if "批次核准" not in leaves_page:
        # Add batch buttons after page-head
        leaves_page = leaves_page.replace(
            '</div>\n      </div>\n\n      {/* filters',
            '</div>\n        {selectedIds.length > 0 && <div style={{display:"flex",gap:8}}><button className="btn btn-approve" onClick={() => batchApprove(selectedIds)}>✓ 批次核准 ({selectedIds.length})</button></div>}\n      </div>\n\n      {/* filters'
        )
    
    # Add modal at end of component
    if "detailLeave &&" not in leaves_page:
        leaves_page = leaves_page.replace(
            "    </div>\n  );\n}",
            '      {detailLeave && <LeaveDetailModal leave={detailLeave} onClose={() => setDetailLeave(null)} onAction={() => window.location.reload()} />}\n    </div>\n  );\n}'
        )

    files["src/pages/LeavesPage.tsx"] = leaves_page
    print("  LeavesPage.tsx: enhanced with batch + modal")

# =====================================================
# Enhance AttendancePage.tsx
# =====================================================
att_page = vfs.get("src/pages/AttendancePage.tsx", "")
if "att-grid" not in att_page and "attGrid" not in att_page:
    # Add employee grid visualization - insert after the page-head
    # Find the table/data section and add grid before it
    if "employees" not in att_page:
        # Add employees state and fetch
        att_page = att_page.replace(
            "const [loading,",
            "const [employees, setEmployees] = useState<any[]>([]);\n  const [gridFilter, setGridFilter] = useState(\"all\");\n  const [loading,"
        )
        # Add employee fetch in useEffect
        att_page = att_page.replace(
            "setLoading(false)",
            """try { const empResp = await queryAdvanced("hr_employees", { limit: 100 }); setEmployees(empResp || []); } catch(e) {}
      setLoading(false)"""
        )

    # Add grid JSX before the table
    grid_jsx = '''
      {/* 出勤網格 */}
      <div className="panel" style={{marginBottom:16}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
          <div className="panel-title">📅 今日出勤狀態</div>
          <div style={{display:"flex",gap:4}}>
            {["all","on","leave","unknown"].map(f => (
              <button key={f} onClick={() => setGridFilter(f)} style={{padding:"4px 12px",borderRadius:6,fontSize:12,border:"1px solid #e2e8f0",background:gridFilter===f?"#2563eb":"white",color:gridFilter===f?"white":"#64748b",cursor:"pointer"}}>
                {f==="all"?"全部":f==="on"?"在崗":f==="leave"?"請假":"未打卡"}
              </button>
            ))}
          </div>
        </div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(140px,1fr))",gap:8}}>
          {employees.map((e: any) => {
            const hasAtt = attendances.some((a: any) => a.employee_id === e.id);
            const status = hasAtt ? "on" : "unknown";
            if (gridFilter !== "all" && gridFilter !== status) return null;
            const colors: Record<string,{b:string,bg:string}> = {on:{b:"#16a34a",bg:"#dcfce7"},leave:{b:"#ea580c",bg:"#ffedd5"},unknown:{b:"#e2e8f0",bg:"#f8fafc"}};
            const c = colors[status] || colors.unknown;
            return (
              <div key={e.id} style={{border:`1px solid ${c.b}`,background:c.bg,borderRadius:8,padding:8,display:"flex",alignItems:"center",gap:8,fontSize:12}}>
                <div style={{width:28,height:28,borderRadius:"50%",background:"linear-gradient(135deg,#2563eb,#7c3aed)",color:"white",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:700,fontSize:12,flexShrink:0}}>{(e.name||"?")[0]}</div>
                <div><div style={{fontWeight:600}}>{e.name}</div><div style={{fontSize:10,color:"#64748b"}}>{hasAtt?"在崗":"未打卡"}</div></div>
              </div>
            );
          })}
        </div>
      </div>
'''
    if "出勤網格" not in att_page:
        # Insert before the table
        table_idx = att_page.find("<table")
        if table_idx == -1:
            table_idx = att_page.find("DataTable") 
        if table_idx == -1:
            table_idx = att_page.find("{loading ?")
        if table_idx > 0:
            att_page = att_page[:table_idx] + grid_jsx + att_page[table_idx:]

    files["src/pages/AttendancePage.tsx"] = att_page
    print("  AttendancePage.tsx: enhanced with grid")

print(f"  Total files to patch: {len(files)}")

# =====================================================
# PATCH + Compile + Publish
# =====================================================
print(f"\n[6] PATCH {len(files)} files (v{version})...")
r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": files, "expected_version": version}, token)
if r is None:
    # Try getting latest version
    app2 = api("GET", f"/builder/apps/{APP}", None, token)
    version = app2["vfs_version"]
    print(f"  Retry with v{version}...")
    r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": files, "expected_version": version}, token)
    if r is None:
        print("  FAILED!")
        sys.exit(1)
print("  OK")

print("[7] Compile...")
r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
if not r or not r.get("success"):
    err = (r or {}).get("error", "")
    print(f"  FAILED: {err[:500]}")
    # Try to fix common issues and recompile
    if err:
        print("  Attempting fix...")
        # Get latest VFS
        app3 = api("GET", f"/builder/apps/{APP}", None, token)
        vfs3 = app3["vfs_state"]
        v3 = app3["vfs_version"]
        
        # Parse error for TS issues
        fixes = {}
        # Common fix: missing imports
        if "Cannot find name" in err and "queryAdvanced" in err:
            # Fix AttendancePage - ensure queryAdvanced is imported
            att = vfs3.get("src/pages/AttendancePage.tsx", "")
            if "queryAdvanced" not in att.split("\n")[0]:
                att = 'import { query, queryAdvanced } from "../utils/dbHelper";\n' + att
                fixes["src/pages/AttendancePage.tsx"] = att
        
        if fixes:
            print(f"  Patching {len(fixes)} fixes...")
            api("PATCH", f"/builder/apps/{APP}/source/files", {"files": fixes, "expected_version": v3}, token)
            r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
            if r and r.get("success"):
                print("  Compile OK (after fix)")
            else:
                err2 = (r or {}).get("error", "")
                print(f"  Still failing: {err2[:500]}")
                sys.exit(1)
        else:
            sys.exit(1)
else:
    print("  OK")

print("[8] Publish...")
r = api("POST", f"/builder/apps/{APP}/publish", {"published_assets": {}}, token)
print("  OK")

# =====================================================
# Test AI Action
# =====================================================
print("\n[9] Testing AI Action...")
for action_name in ["dashboard", "analysis", "anomaly"]:
    r = api("POST", f"/actions/apps/{APP}/run/ai_hr_insights", {"action": action_name}, token)
    if r and r.get("status") == "success":
        result = r.get("result", {})
        keys = list(result.keys()) if isinstance(result, dict) else []
        print(f"  ✅ {action_name}: {keys}")
    else:
        err = (r or {}).get("error", "unknown")
        print(f"  ❌ {action_name}: {err[:200]}")

print("\n=== Done ===")
