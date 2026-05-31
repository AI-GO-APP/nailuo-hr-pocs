import json, re, httpx
from collections import defaultdict

def execute(ctx):
    action = ctx.params.get("action", "get_options")

    if action == "get_options":
        leads = ctx.db.query("crm_leads", limit=500)
        if not isinstance(leads, list): leads = []
        companies = sorted(set(
            l.get("partner_name", "") for l in leads
            if l.get("partner_name")
        ))
        ctx.response.json({"companies": companies})

    elif action == "submit_log":
        desc = ctx.params.get("description", "")
        company = ctx.params.get("company", "")
        date = ctx.params.get("date", "")
        work_nature = ctx.params.get("work_nature", "")
        hours = ctx.params.get("hours", 2)

        ai = _call_ai(ctx, desc)

        teams = ctx.db.query("crm_teams", limit=1)
        stages = ctx.db.query("crm_stages", limit=1)
        team_id = teams[0]["id"] if isinstance(teams, list) and teams else None
        stage_id = stages[0]["id"] if isinstance(stages, list) and stages else None

        record = {
            "name": "Log: " + str(company) + " " + str(date),
            "partner_name": company,
            "description": desc,
            "date_open": date,
            "type": "opportunity",
            "custom_data": {
                "log_type": "sales_log",
                "work_nature": work_nature,
                "hours": hours,
                "risk_score": ai.get("risk_score", 0),
                "risk_category": ai.get("risk_category", ""),
                "ai_reason": ai.get("reason", ""),
                "status": "analyzed",
            }
        }
        if team_id: record["team_id"] = team_id
        if stage_id: record["stage_id"] = stage_id

        inserted = ctx.db.insert("crm_leads", record)

        ctx.response.json({
            "success": True,
            "risk_score": ai.get("risk_score", 0),
            "risk_category": ai.get("risk_category", ""),
            "ai_reason": ai.get("reason", ""),
        })

    elif action == "list_logs":
        leads = ctx.db.query("crm_leads", limit=500)
        if not isinstance(leads, list): leads = []
        logs = []
        for l in leads:
            cd = l.get("custom_data") or {}
            if cd.get("log_type") != "sales_log": continue
            logs.append({
                "id": l.get("id", ""),
                "date": l.get("date_open", ""),
                "company": l.get("partner_name", ""),
                "work_nature": cd.get("work_nature", ""),
                "description": l.get("description", ""),
                "risk_score": cd.get("risk_score", 0),
                "risk_category": cd.get("risk_category", ""),
                "ai_reason": cd.get("ai_reason", ""),
            })
        logs.sort(key=lambda x: x.get("date", ""), reverse=True)
        total = len(logs)
        high_risk = len([l for l in logs if l.get("risk_score", 0) >= 3])
        positive = len([l for l in logs if l.get("risk_score", 0) <= 1])
        ctx.response.json({"logs": logs, "kpi": {"total": total, "high_risk": high_risk, "positive": positive}})

    elif action == "my_customers":
        leads = ctx.db.query("crm_leads", limit=500)
        if not isinstance(leads, list): leads = []
        cust = defaultdict(lambda: {"visits": 0, "max_risk": 0, "last_date": ""})
        for l in leads:
            cd = l.get("custom_data") or {}
            if cd.get("log_type") != "sales_log": continue
            company = l.get("partner_name", "")
            if not company: continue
            c = cust[company]
            c["visits"] += 1
            rs = cd.get("risk_score", 0)
            if rs > c["max_risk"]: c["max_risk"] = rs
            d = l.get("date_open", "")
            if d > c["last_date"]: c["last_date"] = d
        result = [{"company": n, **c} for n, c in cust.items()]
        result.sort(key=lambda x: -x["max_risk"])
        high_risk_count = len([c for c in result if c["max_risk"] >= 3])
        ctx.response.json({"customers": result, "high_risk_count": high_risk_count})


    elif action == "seed_data":
        records = ctx.params.get("records", [])
        teams = ctx.db.query("crm_teams", limit=1)
        stages = ctx.db.query("crm_stages", limit=1)
        team_id = teams[0]["id"] if isinstance(teams, list) and teams else None
        stage_id = stages[0]["id"] if isinstance(stages, list) and stages else None
        ok = 0
        errors = []
        for i, rec in enumerate(records):
            data = {
                "name": "Log: " + str(rec.get("company","")) + " " + str(rec.get("date","")),
                "partner_name": rec.get("company", ""),
                "description": rec.get("desc", ""),
                "date_open": rec.get("date", ""),
                "type": "opportunity",
                "custom_data": {
                    "log_type": "sales_log",
                    "work_nature": rec.get("nature", ""),
                    "hours": rec.get("hours", 2),
                    "customer_grade": rec.get("grade", ""),
                    "salesperson_name": rec.get("salesperson", ""),
                    "risk_score": rec.get("risk", 0),
                    "risk_category": rec.get("cat", ""),
                    "ai_reason": rec.get("reason", ""),
                    "status": "analyzed",
                }
            }
            if team_id: data["team_id"] = team_id
            if stage_id: data["stage_id"] = stage_id
            try:
                ctx.db.insert("crm_leads", data)
                ok += 1
            except Exception as e:
                errors.append({"i": i, "err": str(e)[:100]})
        ctx.response.json({"inserted": ok, "total": len(records), "errors": errors[:5]})

    elif action == "ai_preview":
        desc = ctx.params.get("description", "")
        ai = _call_ai(ctx, desc)
        ctx.response.json(ai)

    else:
        ctx.response.json({"error": "Unknown action"})

def _call_ai(ctx, description):
    # ctx.secrets.get 在金鑰不存在時會拋出例外
    api_key = None
    try:
        api_key = ctx.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass
    if not api_key:
        return _fallback_detect(description)
    try:
        prompt = (
            "你是客戶流失風險分析專家。請判讀以下業務日誌的風險。\n\n"
            "日誌內容：" + description + "\n\n"
            "請回傳 JSON：{\"risk_score\": 0-4, \"risk_category\": \"分類\", \"reason\": \"說明\"}\n"
            "risk_category 必須是：競爭搶單/品質客訴/營運下滑/帳款問題/關係惡化/無風險\n"
            "只回傳 JSON，不要其他文字。"
        )
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3},
            timeout=30,
        )
        content = resp.json()["choices"][0]["message"]["content"].strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        return json.loads(content)
    except Exception:
        return _fallback_detect(description)

def _fallback_detect(text):
    if not text or len(text) < 20:
        return {"risk_score": 0, "risk_category": "無風險", "reason": "內容過短，無法判讀"}
    if re.search(r'切走|搶單|轉給.{0,5}(別|其他|對手)|流失|被.{0,5}(切|搶)', text):
        return {"risk_score": 4, "risk_category": "競爭搶單", "reason": "偵測到「訂單流失/被切走」訊號"}
    if re.search(r'罰款|不良率|連續.{0,5}異常|退貨|客訴|索賠', text):
        return {"risk_score": 4, "risk_category": "品質客訴", "reason": "偵測到「品質爭議/罰款」訊號"}
    if re.search(r'(貨款|帳款|賬款).{0,5}(未付|沒付|逾期|催)|呆帳', text):
        return {"risk_score": 4, "risk_category": "帳款問題", "reason": "偵測到「貨款延遲」訊號"}
    if re.search(r'(下滑|下降|減量).{0,10}%', text):
        return {"risk_score": 3, "risk_category": "營運下滑", "reason": "偵測到客戶訂單下滑訊號"}
    if re.search(r'抱怨|不滿|拒絕.{0,5}(降價|配合)|施壓', text):
        return {"risk_score": 3, "risk_category": "關係惡化", "reason": "偵測到客戶關係緊張訊號"}
    return {"risk_score": 1, "risk_category": "無風險", "reason": "未偵測到明顯風險訊號，屬於常規互動"}
