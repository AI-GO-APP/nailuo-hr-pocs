import os, json

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
            "你是客戶流失風險分析專家。以下是本月業務日誌統計：\n"
            + "- 總日誌數：" + str(total_logs) + "\n"
            + "- 高風險客戶：" + str(len(high_risk_companies)) + " 個\n"
            + "- 高風險日誌：" + str(len(high_risk_logs)) + " 筆\n"
            + "- 主要風險類型：" + top_category + "\n"
            + "- 風險分布：" + json.dumps(dict(all_cats), ensure_ascii=False) + "\n\n"
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
            "分析以下業務人員的客戶風險狀況：\n"
            + json.dumps(staff_ranking, ensure_ascii=False) + "\n\n"
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
            "分析以下「" + category + "」風險類別的業務日誌摘要：\n"
            + "\n".join(descs) + "\n\n"
            + "請用3-5條條列式提供此類別的深度分析與建議。不要使用emoji。")
    
    return result

def _log_analyze(ctx, skip_ai):
    description = ctx.params.get("description", "")
    if not description:
        return {"error": "缺少日誌描述"}
    if skip_ai:
        return {"risk_score": 0, "risk_category": "待分析", "ai_reason": ""}
    ai_result = _call_ai(ctx,
        "你是客戶流失風險分析專家。請判讀以下業務日誌的風險：\n\n"
        + description + "\n\n請回傳 JSON：\n"
        + "{\"risk_score\": 0-4, \"risk_category\": \"競爭搶單/品質客訴/營運下滑/帳款問題/關係惡化/無風險\", \"reason\": \"說明\"}\n只回傳 JSON。")
    try:
        return json.loads(ai_result)
    except:
        return {"risk_score": 1, "risk_category": "無風險", "ai_reason": ai_result}

def _call_ai(ctx, prompt):
    import httpx
    
    api_key = ctx.secrets.get("OPENAI_API_KEY")
    if not api_key:
        return "- AI 金鑰未設定，無法分析"
    
    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "max_tokens": 600,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return "- AI 服務回傳錯誤: " + str(resp.status_code)
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return "- AI 分析失敗: " + str(e)[:100]
