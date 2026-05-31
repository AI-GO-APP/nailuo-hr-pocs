import json

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
            raw = db.query("crm_leads", limit=500)
            if not isinstance(raw, list): raw = []
            import json as _json
            log_count = sum(1 for r in raw
                if isinstance((r.get("custom_data") if isinstance(r.get("custom_data"), dict)
                    else (_json.loads(r["custom_data"]) if isinstance(r.get("custom_data"), str) else {})),
                    dict) and (r.get("custom_data") if isinstance(r.get("custom_data"), dict)
                    else {}).get("log_type") == "sales_log")
            sources.append({"name": "crm_leads (sales_log)", "status": "connected", "count": log_count})
        except Exception as _e:
            sources.append({"name": "crm_leads (sales_log)", "status": "error", "error": str(_e)[:100]})
        
        ctx.response.json({"sources": sources})
    
    elif action == "raw_logs":
        try:
            import json as _json
            raw = db.query("crm_leads", limit=500)
            if not isinstance(raw, list): raw = []
            logs = []
            for r in raw:
                cd = r.get("custom_data") or {}
                if isinstance(cd, str):
                    try: cd = _json.loads(cd)
                    except: cd = {}
                if cd.get("log_type") != "sales_log":
                    continue
                logs.append({"id": r.get("id",""), "data": {
                    "company": r.get("partner_name",""),
                    "description": r.get("description",""),
                    "date": r.get("date_open",""),
                    "risk_score": cd.get("risk_score",0),
                    "risk_category": cd.get("risk_category",""),
                    "ai_reason": cd.get("ai_reason",""),
                    "work_nature": cd.get("work_nature",""),
                    "salesperson": cd.get("salesperson_name",""),
                    "customer_grade": cd.get("customer_grade",""),
                    "status": cd.get("status",""),
                }})
            ctx.response.json({"logs": logs})
        except Exception as e:
            ctx.response.json({"logs": [], "error": str(e)[:200]})
    
    else:
        ctx.response.json({"error": "Unknown action"})
