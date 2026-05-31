# -*- coding: utf-8 -*-
"""
客戶流失風險分析 Phase 1 建置腳本
===================================
1. 建立 sales_logs custom table
2. 插入 40-50 筆模擬業務日誌（台灣螺絲/扣件產業場景）
3. 上傳 analyze_churn.py 與 fetch_crm_data.py 到 VFS
"""

import json, urllib.request, ssl, sys, time, random
ssl._create_default_https_context = ssl._create_unverified_context

BASE = "https://ai-go.app/api/v1"
APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"

# ============================================================
# API 輔助函式
# ============================================================
def api(m, p, d=None, t=None):
    """通用 API 呼叫"""
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t:
        req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:500]
        print(f"  HTTP {e.code}: {detail}")
        return {"_error": e.code, "_detail": detail}

# ============================================================
# 登入
# ============================================================
print("=" * 60)
print("  Phase 1: 客戶流失風險分析 - 資料建置")
print("=" * 60)

auth = api("POST", "/auth/login", {"email": "admin@tslg.com.tw", "password": "password123"})
if not auth or "_error" in auth:
    print("  登入失敗！")
    sys.exit(1)
token = auth["access_token"]
print(f"  登入成功")

# 取得 App 資訊
app_data = api("GET", f"/builder/apps/{APP}", None, token)
if not app_data or "_error" in app_data:
    print("  無法取得 App 資訊！")
    sys.exit(1)
vfs = app_data.get("vfs_state", {})
version = app_data.get("vfs_version", 0)
slug = app_data.get("slug", "")
print(f"  App: {app_data.get('name')} (v{version}, slug={slug})")

# ============================================================
# 任務 1: 建立 sales_logs custom table
# ============================================================
print("\n" + "-" * 60)
print("  任務 1: 建立 sales_logs custom table")
print("-" * 60)

# 先檢查是否已存在（空陣列 [] 也代表 table 存在）
test = api("GET", f"/data/objects/sales_logs/records?limit=1", None, token)
if isinstance(test, (list, dict)) and "_error" not in (test if isinstance(test, dict) else {}):
    print("  sales_logs 已存在，跳過建立")
else:
    # 建立 custom table
    table_def = {
        "app_id": APP,
        "name": "業務日誌",
        "api_slug": "sales_logs",
        "schema": {
            "fields": [
                {"name": "date", "type": "text", "label": "拜訪日期"},
                {"name": "salesperson", "type": "text", "label": "業務人員"},
                {"name": "company", "type": "text", "label": "公司簡稱"},
                {"name": "work_nature", "type": "text", "label": "工作性質"},
                {"name": "description", "type": "text", "label": "工作描述"},
                {"name": "risk_score", "type": "number", "label": "風險分數"},
                {"name": "risk_category", "type": "text", "label": "風險類別"},
                {"name": "ai_reason", "type": "text", "label": "AI判讀理由"},
                {"name": "customer_grade", "type": "text", "label": "客戶等級"},
                {"name": "status", "type": "text", "label": "狀態"},
            ]
        }
    }
    r = api("POST", "/data/objects", table_def, token)
    if r and "_error" not in r:
        print(f"  sales_logs 建立成功 (id={r.get('id', '')})")
    else:
        print(f"  sales_logs 建立失敗: {r}")
        # 嘗試用舊格式建立
        print("  嘗試使用 fields 格式...")
        table_def2 = {
            "app_id": APP,
            "name": "業務日誌",
            "api_slug": "sales_logs",
            "fields": [
                {"name": "date", "field_type": "text", "display_name": "拜訪日期"},
                {"name": "salesperson", "field_type": "text", "display_name": "業務人員"},
                {"name": "company", "field_type": "text", "display_name": "公司簡稱"},
                {"name": "work_nature", "field_type": "text", "display_name": "工作性質"},
                {"name": "description", "field_type": "text", "display_name": "工作描述"},
                {"name": "risk_score", "field_type": "number", "display_name": "風險分數"},
                {"name": "risk_category", "field_type": "text", "display_name": "風險類別"},
                {"name": "ai_reason", "field_type": "text", "display_name": "AI判讀理由"},
                {"name": "customer_grade", "field_type": "text", "display_name": "客戶等級"},
                {"name": "status", "field_type": "text", "display_name": "狀態"},
            ]
        }
        r2 = api("POST", "/data/objects", table_def2, token)
        if r2 and "_error" not in r2:
            print(f"  sales_logs 建立成功 (id={r2.get('id', '')})")
        else:
            print(f"  sales_logs 建立失敗: {r2}")
            sys.exit(1)

# 驗證 table 已建立
time.sleep(1)
verify = api("GET", f"/data/objects/sales_logs/records?limit=1", None, token)
if isinstance(verify, (list, dict)) and "_error" not in (verify if isinstance(verify, dict) else {}):
    print("  驗證: sales_logs 可存取")
else:
    print(f"  驗證失敗: {verify}")
    sys.exit(1)

# ============================================================
# 任務 2: 插入模擬資料
# ============================================================
print("\n" + "-" * 60)
print("  任務 2: 插入模擬業務日誌 (40-50 筆)")
print("-" * 60)

# 客戶清單 (公司, 等級, 風險分數, 風險類別, 負責業務)
CUSTOMERS = [
    ("金盈佳", "A", 4, "競爭搶單", "張文武"),
    ("昆山-仁寶二廠", "A", 4, "品質客訴", "張文武"),
    ("惠州友仁", "B", 3, "帳款問題", "張文武"),
    ("太倉-文順", "E", 4, "帳款問題", "張文武"),
    ("耐力(耐鵬)", "A", 3, "帳款問題", "張文武"),
    ("嘉定-連盈", "D", 4, "關係惡化", "張文武"),
    ("昆山-杜爾伯", "D", 2, "品質客訴", "張文武"),
    ("泰都分廠", "D", 0, "無風險", "張文武"),
    ("蕪湖-奇瑞新能源", "A", 2, "營運下滑", "林秉軒"),
    ("錩泰", "C", 2, "競爭搶單", "林秉軒"),
    ("中盛達(中興達)", "A", 3, "關係惡化", "林秉軒"),
    ("伸銘", "D", 1, "無風險", "林秉軒"),
    ("南通-聯鋼", "B", 4, "品質客訴", "林秉軒"),
    ("建興安泰", "B", 1, "無風險", "陳彥廷"),
    ("聚巨豐", "A", 1, "無風險", "陳彥廷"),
    ("雷堤", "B", 4, "競爭搶單", "陳彥廷"),
]

# 工作性質選項
WORK_NATURES = [
    "訂單追蹤", "人脈建立維護", "導入進度追蹤", "探詢客戶產品資訊",
    "技術規範研討", "電話案例追蹤", "客戶約訪", "異常服務處理",
    "客戶品質會議", "報價作業", "客戶來廠參觀"
]

# 風險類別
RISK_CATEGORIES = ["競爭搶單", "品質客訴", "營運下滑", "帳款問題", "關係惡化", "無風險"]

# 模擬日誌描述模板 - 依風險類別分類（貼近台灣螺絲/扣件產業場景）
DESCRIPTIONS = {
    "競爭搶單": [
        "拜訪{company}採購部門，得知日本 ITW 已提供 Nylok 防鬆對標產品報價，價格低於我方約 8%。客戶表示月底前需提交最終比價，建議儘速調整報價策略。對方已取得 ITW 防鬆扭力測試報告，我方需提供同等規格的測試數據。",
        "與{company}研發課長陳先生討論新機種用 M8x1.25 法蘭面螺栓的防鬆需求。對方透露有國內競爭廠商已提供 Nycron 塗層替代方案的樣品，價格約低 12%。建議安排技術簡報展示我方 Nylok 預塗防鬆膠的耐溫優勢。",
        "接獲{company}通知，其集團總部正在推動供應商整併政策，螺絲扣件類供應商將從目前 5 家縮減為 3 家。我方需於下月前提交品質稽核文件與年度降價方案，否則恐被排除在合格供應商名單外。",
        "與{company}品保經理餐敘，對方私下提及東莞某同業已在該廠導入 Nylok 防鬆線的替代工藝。目前該替代品的扭力值尚未達標，但價格僅我方的七成。建議加強技術差異化宣傳與現場驗證。",
        "{company}下單量連續兩個月縮減約 20%，業務瞭解後確認為競爭對手以低價搶入部分料號。與主管討論後決議啟動客製化服務方案，針對客戶常用規格提供 JIT 備貨以提升交貨速度。",
    ],
    "品質客訴": [
        "{company}反映近期到貨的 M6 六角承穴螺栓有鍍鋅層剝落問題，影響產線使用。已安排品保前往取樣並啟動 8D 報告流程，初步判斷為電鍍液配方異常，需追查供應鏈源頭。",
        "收到{company}品保部正式客訴函，指出上批 Nylok 點膠螺栓的防鬆力矩不合格率達 4.2%，超出 AQL 標準。立即聯繫工廠安排全檢與補貨，並承諾三日內提供矯正報告。",
        "陪同品保主管前往{company}處理 M10 自攻螺絲斷裂問題。客戶產線已暫停組裝，影響出貨排程。經現場金相分析，初步判定為熱處理硬度偏高導致脆斷，已啟動緊急換貨流程。",
        "{company}通知其終端客戶退回一批含有異物的 Nycron 防鬆螺母，要求我方提供製程追溯報告。已協調工廠品保與生產部門進行批次追查，預計 48 小時內完成調查報告。",
        "前往{company}進行季度品質檢討會議，討論近三個月 PPM 指標與改善對策。客戶要求將來料不良率從目前 500 PPM 降至 200 PPM 以下，否則將啟動替代供應商評估程序。",
    ],
    "營運下滑": [
        "拜訪{company}，發現其主要客戶已開始縮減車用零件訂單量，連帶影響我方螺絲出貨。財務反映該公司帳款天數從 60 天延長至 90 天，需密切關注其營運狀況並調整授信額度。",
        "與{company}廠長電話聯繫，對方表示因下游需求疲軟，工廠已從三班制調整為兩班制，預計下季度訂單將再縮減 15%。建議主動提供小批量多批次的彈性交貨方案以維持供應關係。",
        "接獲{company}通知暫停新品開發合作，原因是其母公司正在進行組織調整。目前在途訂單維持不變，但新項目的 Nylok 防鬆膠導入時程將延後至下半年。需重新評估該客戶的年度業績貢獻。",
    ],
    "帳款問題": [
        "{company}應收帳款已超過 120 天，累計金額達 186 萬。電話催收時對方財務表示資金周轉困難，承諾月底前先支付 50%。已通報主管並建議暫停新訂單出貨，待帳款回收後再恢復供貨。",
        "前往{company}拜訪總經理協商逾期帳款事宜。對方提出以開立 90 天期票據方式清償欠款，經評估後同意其方案但要求加計利息。同時調降該客戶信用額度至 80 萬元。",
        "與{company}會計部門確認本月應付帳款明細，發現有三筆扣款項目未經我方同意即逕行沖抵。已發函要求說明扣款理由，並暫緩下批 Nylok 防鬆螺栓出貨。",
        "{company}以品質扣款為由拒付上月貨款 42 萬，但我方記錄顯示該批未有客訴。已請品保調閱出貨檢驗紀錄，並將於本週安排與客戶三方會議釐清事實。",
    ],
    "關係惡化": [
        "本月{company}已連續第二次臨時取消約訪，業務感受到客戶對我方的態度明顯轉冷。經側面瞭解，可能與上次品質問題的處理速度不佳有關，建議安排高階主管登門致歉並提出改善承諾。",
        "拜訪{company}時發現我方在該公司的供應商評等已從 A 級降為 B 級，主要原因是交期達成率下滑至 85%。採購窗口暗示若下季度未能改善，將被轉為備用供應商。建議啟動專案改善交期管理。",
        "{company}新任採購主管上任後，多次提出降價要求但態度較為強硬。今日會面時對方明確表示若本月底前無法達成 5% 降幅，將轉移 30% 的訂單量至其他供應商。需與業務主管研議對策。",
    ],
    "無風險": [
        "例行拜訪{company}，與採購確認下月排單計畫。客戶目前合作穩定，本季 Nylok 防鬆螺栓用量維持在每月 15 萬顆左右，預計下季度因新車型量產將增加約 20% 需求。",
        "陪同{company}品保課長參觀我方工廠，展示 Nylok 防鬆加工產線及品質管理系統。客戶對自動化檢測設備印象深刻，表示將考慮增加新機種的防鬆需求委託。",
        "與{company}業務窗口進行月度對帳作業，所有訂單出貨與帳款均正常。客戶對我方交期配合度表示滿意，並透露下季將有一批新開發的 Nycron 防鬆螺母需求，請我方先行備料評估。",
        "電話聯繫{company}確認近期訂單交貨排程，對方表示目前庫存水位正常，下月將依原計畫下單。雙方合作關係穩定，客戶評價我方產品品質穩定且交期準時。",
        "協助{company}研發部門完成 M5 微型防鬆螺栓的規格確認，提供 Nylok 防鬆膠塗佈工藝建議。客戶對技術支援表示滿意，雙方關係良好。",
        "前往{company}進行年度供應商評鑑面談。客戶給予品質、交期、服務均為優良評價，預計明年合作量將維持或微幅增長。",
    ]
}

# 產生模擬日誌
def generate_logs():
    """產生 45 筆模擬業務日誌"""
    logs = []
    random.seed(42)  # 固定種子確保可重現

    # 每個客戶至少 2 筆，高風險客戶多一些
    for company, grade, risk_score, risk_category, salesperson in CUSTOMERS:
        # 決定此客戶的日誌筆數
        if risk_score >= 4:
            count = random.randint(3, 4)
        elif risk_score >= 3:
            count = random.randint(2, 3)
        elif risk_score >= 2:
            count = 2
        else:
            count = random.randint(1, 2)

        for i in range(count):
            day = random.randint(2, 30)
            date = f"2026-01-{day:02d}"

            # 決定此筆日誌的風險分數（基於客戶風險但有波動）
            if risk_score >= 3:
                log_risk = random.choice([risk_score, risk_score - 1, risk_score])
            elif risk_score >= 2:
                log_risk = random.choice([risk_score, risk_score - 1, risk_score + 1])
            else:
                log_risk = random.choice([0, 1, 0])

            log_risk = max(0, min(4, log_risk))

            # 決定風險類別
            if log_risk <= 1:
                log_category = "無風險"
            else:
                log_category = risk_category

            # 選擇工作性質
            if log_category == "品質客訴":
                work_nature = random.choice(["異常服務處理", "客戶品質會議", "電話案例追蹤"])
            elif log_category == "競爭搶單":
                work_nature = random.choice(["報價作業", "客戶約訪", "探詢客戶產品資訊", "技術規範研討"])
            elif log_category == "帳款問題":
                work_nature = random.choice(["訂單追蹤", "電話案例追蹤", "客戶約訪"])
            elif log_category == "關係惡化":
                work_nature = random.choice(["客戶約訪", "人脈建立維護", "電話案例追蹤"])
            elif log_category == "營運下滑":
                work_nature = random.choice(["訂單追蹤", "探詢客戶產品資訊", "電話案例追蹤"])
            else:
                work_nature = random.choice(WORK_NATURES)

            # 選擇描述
            cat_key = log_category if log_category in DESCRIPTIONS else "無風險"
            desc_templates = DESCRIPTIONS[cat_key]
            desc = random.choice(desc_templates).format(company=company)

            # AI 理由
            if log_risk >= 3:
                ai_reason = f"高風險警示：{log_category}跡象明顯，建議立即介入處理"
            elif log_risk >= 2:
                ai_reason = f"中度風險：有{log_category}傾向，建議密切追蹤"
            elif log_risk >= 1:
                ai_reason = "低風險：目前狀況穩定，建議持續維護關係"
            else:
                ai_reason = "無風險：合作關係良好，維持正常拜訪頻率即可"

            logs.append({
                "date": date,
                "salesperson": salesperson,
                "company": company,
                "work_nature": work_nature,
                "description": desc,
                "risk_score": log_risk,
                "risk_category": log_category,
                "ai_reason": ai_reason,
                "customer_grade": grade,
                "status": "analyzed",
            })

    # 排序按日期
    logs.sort(key=lambda x: x["date"])
    return logs

logs = generate_logs()
print(f"  產生 {len(logs)} 筆模擬日誌")

# 逐筆插入
success_count = 0
fail_count = 0
for i, log in enumerate(logs):
    r = api("POST", "/data/objects/sales_logs/records", {"data": log}, token)
    if r and "_error" not in r:
        success_count += 1
    else:
        fail_count += 1
        if fail_count <= 3:
            print(f"    第 {i+1} 筆失敗: {r}")
    # 避免 rate limiting
    if (i + 1) % 10 == 0:
        print(f"    已插入 {i+1}/{len(logs)} 筆...")
        time.sleep(0.5)

print(f"  插入完成: 成功 {success_count} 筆, 失敗 {fail_count} 筆")

# 驗證資料
verify_logs = api("GET", "/data/objects/sales_logs/records?limit=5", None, token)
if verify_logs and "_error" not in verify_logs:
    results = verify_logs if isinstance(verify_logs, list) else verify_logs.get("results", [])
    print(f"  驗證: 可查詢到 {len(results)} 筆 (取前5筆)")
    if results:
        first = results[0]
        d = first.get("data", {})
        print(f"    範例: {d.get('date')} | {d.get('salesperson')} | {d.get('company')} | 風險{d.get('risk_score')}")

# ============================================================
# 任務 3: 上傳 Action 檔案到 VFS
# ============================================================
print("\n" + "-" * 60)
print("  任務 3: 上傳 Action 檔案到 VFS")
print("-" * 60)

# analyze_churn.py
ANALYZE_CHURN_PY = '''import os, json

def execute(ctx):
    """客戶流失風險分析 Action"""
    action = ctx.params.get("action", "dashboard")
    skip_ai = ctx.params.get("skip_ai", False)
    
    db = ctx.db  # proxy table 存取
    
    # 從 sales_logs custom table 讀取
    logs_raw = ctx.data.list("sales_logs", limit=500)
    logs = logs_raw if isinstance(logs_raw, list) else logs_raw.get("results", [])
    
    if action == "dashboard":
        return _dashboard(ctx, db, logs, skip_ai)
    elif action == "sales_analysis":
        return _sales_analysis(ctx, db, logs, skip_ai)
    elif action == "category_detail":
        category = ctx.params.get("category", "")
        return _category_detail(ctx, db, logs, category, skip_ai)
    elif action == "log_analyze":
        return _log_analyze(ctx, skip_ai)
    
    return {"error": "Unknown action"}

def _dashboard(ctx, db, logs, skip_ai):
    """主儀表板資料"""
    from collections import Counter, defaultdict
    
    # KPI
    total_logs = len(logs)
    high_risk_logs = [l for l in logs if (l.get("data",{}).get("risk_score") or 0) >= 3]
    companies = set(l.get("data",{}).get("company","") for l in logs)
    high_risk_companies = set(l.get("data",{}).get("company","") for l in high_risk_logs)
    
    cat_counter = Counter(l.get("data",{}).get("risk_category","無風險") for l in logs if (l.get("data",{}).get("risk_score") or 0) >= 2)
    top_category = cat_counter.most_common(1)[0][0] if cat_counter else "無"
    
    kpi = {
        "total_logs": total_logs,
        "high_risk_customers": len(high_risk_companies),
        "high_risk_logs": len(high_risk_logs),
        "top_category": top_category,
    }
    
    # 客戶風險排名
    company_data = defaultdict(lambda: {"logs": [], "risk_scores": [], "categories": [], "salesperson": "", "grade": ""})
    for l in logs:
        d = l.get("data", {})
        c = d.get("company", "")
        if not c: continue
        company_data[c]["logs"].append(d)
        company_data[c]["risk_scores"].append(d.get("risk_score", 0) or 0)
        if d.get("risk_category") and d.get("risk_category") != "無風險":
            company_data[c]["categories"].append(d.get("risk_category"))
        company_data[c]["salesperson"] = d.get("salesperson", "")
        company_data[c]["grade"] = d.get("customer_grade", "")
    
    customer_ranking = []
    for company, info in company_data.items():
        max_risk = max(info["risk_scores"]) if info["risk_scores"] else 0
        cat_counter_c = Counter(info["categories"])
        main_cat = cat_counter_c.most_common(1)[0][0] if cat_counter_c else "無"
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
    
    # 風險類別分布
    all_cats = Counter(l.get("data",{}).get("risk_category","") for l in logs if l.get("data",{}).get("risk_category") and l.get("data",{}).get("risk_category") != "無風險")
    category_dist = [{"name": k, "count": v} for k, v in all_cats.most_common()]
    
    # 最該關注的 5 個客戶
    top5 = customer_ranking[:5]
    
    # 下週行動建議
    actions_list = []
    for c in customer_ranking[:8]:
        if c["max_risk"] >= 3:
            actions_list.append({
                "company": c["company"],
                "action": f"追蹤 {c['main_category']} 風險",
                "priority": "high" if c["max_risk"] >= 4 else "medium",
                "salesperson": c["salesperson"],
            })
    
    result = {
        "kpi": kpi,
        "customer_ranking": customer_ranking,
        "category_distribution": category_dist,
        "top5_customers": top5,
        "action_items": actions_list,
        "ai_insight": "",
    }
    
    if not skip_ai:
        result["ai_insight"] = _call_ai(ctx, f"""你是客戶流失風險分析專家。以下是本月業務日誌統計：
- 總日誌數：{total_logs}
- 高風險客戶：{len(high_risk_companies)} 個
- 高風險日誌：{len(high_risk_logs)} 筆
- 主要風險類型：{top_category}
- 風險分布：{json.dumps(dict(all_cats), ensure_ascii=False)}

請用3-5條條列式提供主管洞察與建議。不要使用任何emoji，用純文字。""")
    
    return result

def _sales_analysis(ctx, db, logs, skip_ai):
    """業務人員分析"""
    from collections import defaultdict, Counter
    
    staff = defaultdict(lambda: {"customers": set(), "high_risk": set(), "visits": 0, "risk_scores": []})
    for l in logs:
        d = l.get("data", {})
        sp = d.get("salesperson", "")
        if not sp: continue
        staff[sp]["customers"].add(d.get("company", ""))
        staff[sp]["visits"] += 1
        score = d.get("risk_score", 0) or 0
        staff[sp]["risk_scores"].append(score)
        if score >= 3:
            staff[sp]["high_risk"].add(d.get("company", ""))
    
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
    
    # KPI
    kpi = {
        "total_staff": len(staff),
        "concentrated_risk": sum(1 for s in staff_ranking if s["high_risk_count"] >= 2),
        "firefighter": sum(1 for q in quadrant_data if q["x"] > 8 and q["y"] > 2),
        "multi_visit": 0,
    }
    
    result = {
        "kpi": kpi,
        "staff_ranking": staff_ranking,
        "quadrant_data": quadrant_data,
        "ai_insight": "",
    }
    
    if not skip_ai:
        result["ai_insight"] = _call_ai(ctx, f"""分析以下業務人員的客戶風險狀況：
{json.dumps(staff_ranking, ensure_ascii=False)}

請用3-5條條列式提供建議。不要使用emoji。""")
    
    return result

def _category_detail(ctx, db, logs, category, skip_ai):
    """風險類別詳情"""
    from collections import Counter, defaultdict
    
    cat_logs = [l for l in logs if l.get("data",{}).get("risk_category") == category]
    
    # 統計
    companies = defaultdict(list)
    staff_impact = defaultdict(int)
    for l in cat_logs:
        d = l.get("data", {})
        companies[d.get("company", "")].append(d)
        staff_impact[d.get("salesperson", "")] += 1
    
    top_customers = sorted(companies.items(), key=lambda x: -len(x[1]))[:5]
    top_staff = sorted(staff_impact.items(), key=lambda x: -x[1])[:5]
    
    result = {
        "category": category,
        "total_logs": len(cat_logs),
        "total_customers": len(companies),
        "top_customers": [{"company": c, "count": len(logs_list)} for c, logs_list in top_customers],
        "top_staff": [{"name": n, "count": c} for n, c in top_staff],
        "ai_insight": "",
    }
    
    if not skip_ai:
        descs = [l.get("data",{}).get("description","")[:100] for l in cat_logs[:10]]
        result["ai_insight"] = _call_ai(ctx, f"""分析以下「{category}」風險類別的業務日誌摘要：
{chr(10).join(descs)}

請用3-5條條列式提供此類別的深度分析與建議。不要使用emoji。""")
    
    return result

def _log_analyze(ctx, skip_ai):
    """單筆日誌 AI 分析"""
    description = ctx.params.get("description", "")
    if not description:
        return {"error": "缺少日誌描述"}
    
    if skip_ai:
        return {"risk_score": 0, "risk_category": "待分析", "ai_reason": ""}
    
    ai_result = _call_ai(ctx, f"""你是客戶流失風險分析專家。請判讀以下業務日誌的風險：

{description}

請回傳 JSON 格式：
{{"risk_score": 0-4的整數, "risk_category": "競爭搶單/品質客訴/營運下滑/帳款問題/關係惡化/無風險", "reason": "一句話說明"}}

只回傳 JSON，不要其他文字。""")
    
    try:
        parsed = json.loads(ai_result)
        return parsed
    except:
        return {"risk_score": 1, "risk_category": "無風險", "ai_reason": ai_result}

def _call_ai(ctx, prompt):
    """呼叫 OpenAI API"""
    import urllib.request, ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    
    api_key = os.environ.get("OPENAI_API_KEY", ctx.secrets.get("OPENAI_API_KEY") or "")
    if not api_key:
        return "- AI 金鑰未設定，無法分析"
    
    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 600,
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"- AI 分析失敗: {str(e)[:100]}"
'''

# fetch_crm_data.py
FETCH_CRM_DATA_PY = '''def execute(ctx):
    """純資料查詢，不走 AI"""
    action = ctx.params.get("action", "refs_status")
    db = ctx.db
    
    if action == "refs_status":
        # 資料來源連線狀態
        sources = []
        for table in ["crm_leads", "sale_orders", "crm_tags", "crm_teams", "crm_stages", "sale_order_lines"]:
            try:
                data = db.query(table, limit=1)
                sources.append({"name": table, "status": "connected", "count": len(data) if isinstance(data, list) else 0})
            except:
                sources.append({"name": table, "status": "error"})
        
        # Custom table
        logs = ctx.data.list("sales_logs", limit=500)
        log_list = logs if isinstance(logs, list) else logs.get("results", [])
        sources.append({"name": "sales_logs", "status": "connected", "count": len(log_list), "type": "custom"})
        
        return {"sources": sources}
    
    elif action == "raw_logs":
        logs = ctx.data.list("sales_logs", limit=100)
        log_list = logs if isinstance(logs, list) else logs.get("results", [])
        return {"logs": log_list}
    
    return {"error": "Unknown action"}
'''

# 重新取得最新版本號
app_data = api("GET", f"/builder/apps/{APP}", None, token)
version = app_data.get("vfs_version", 0)
vfs = app_data.get("vfs_state", {})

# 準備上傳的檔案
files = {
    "actions/analyze_churn.py": ANALYZE_CHURN_PY,
    "actions/fetch_crm_data.py": FETCH_CRM_DATA_PY,
}

print(f"  上傳 {len(files)} 個 Action 檔案 (v{version})...")
for path in files:
    print(f"    {path} ({len(files[path])} chars)")

r = api("PATCH", f"/builder/apps/{APP}/source/files",
        {"files": files, "expected_version": version}, token)

if r and "_error" not in r:
    print("  VFS 上傳成功")
else:
    # 可能版本號已變更，重新取得
    print(f"  首次上傳失敗，重新取得版本號...")
    app_data2 = api("GET", f"/builder/apps/{APP}", None, token)
    version2 = app_data2.get("vfs_version", 0)
    r = api("PATCH", f"/builder/apps/{APP}/source/files",
            {"files": files, "expected_version": version2}, token)
    if r and "_error" not in r:
        print("  VFS 上傳成功 (第二次嘗試)")
    else:
        print(f"  VFS 上傳失敗: {r}")
        sys.exit(1)

# ============================================================
# 驗證結果
# ============================================================
print("\n" + "-" * 60)
print("  驗證結果")
print("-" * 60)

# 驗證 VFS 檔案
app_final = api("GET", f"/builder/apps/{APP}", None, token)
vfs_final = app_final.get("vfs_state", {})
for path in ["actions/analyze_churn.py", "actions/fetch_crm_data.py"]:
    if path in vfs_final:
        content = vfs_final[path]
        print(f"  {path}: 存在 ({len(content)} chars)")
    else:
        print(f"  {path}: 不存在!")

# 驗證 custom table 資料
logs_verify = api("GET", "/data/objects/sales_logs/records?limit=500", None, token)
if isinstance(logs_verify, (list, dict)) and "_error" not in (logs_verify if isinstance(logs_verify, dict) else {}):
    results = logs_verify if isinstance(logs_verify, list) else logs_verify.get("results", [])
    print(f"  sales_logs 資料: {len(results)} 筆")

    # 統計
    from collections import Counter
    companies = Counter()
    salespeople = Counter()
    risk_cats = Counter()
    for r in results:
        d = r.get("data", {})
        companies[d.get("company", "")] += 1
        salespeople[d.get("salesperson", "")] += 1
        risk_cats[d.get("risk_category", "")] += 1

    print(f"  客戶數: {len(companies)}")
    print(f"  業務人員: {dict(salespeople)}")
    print(f"  風險分布: {dict(risk_cats)}")
else:
    print(f"  驗證失敗: {logs_verify}")

print("\n" + "=" * 60)
print("  Phase 1 建置完成!")
print("=" * 60)
