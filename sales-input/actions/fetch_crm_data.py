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
