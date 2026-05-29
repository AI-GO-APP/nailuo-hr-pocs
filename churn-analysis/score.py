#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客戶流失風險評分 — 純規則版（不呼叫 API）
基於對日誌樣本的觀察，採用上下文敏感的 pattern matching。
"""
import re
import pandas as pd

INPUT_XLSX = "/Users/lialilingchen/Downloads/CRM POC資料_2026-04-09.xlsx"
OUTPUT_XLSX = "/Users/lialilingchen/AI agent/churn_analysis/churn_risk_report.xlsx"

# ---------------------------------------------------------------
# 風險樣態定義
# 每個 pattern：(正則, 加分, 風險類別, 描述)
# ---------------------------------------------------------------
HIGH_RISK_PATTERNS = [
    # 明確流失/搶單
    (r"被[^，。\s]{0,15}(?:切走|搶走|搶單|搶去|拿走|奪走)", 4, "競爭搶單", "訂單被搶"),
    (r"(?:切走|搶走|搶單|拿走)[^，。\s]{0,10}(?:訂單|料號|料件|生意)", 4, "競爭搶單", "訂單被搶"),
    (r"轉(?:給|單給|向|至)[^，。\s]{0,10}(?:其他|別家|對手|競爭)", 4, "競爭搶單", "轉單"),
    (r"(?:改用|換成|採用|選用)[^，。\s]{0,15}(?:其他|別家|替代|對手)(?:供應商|廠|品牌)", 4, "競爭搶單", "改用對手"),
    (r"終止(?:合作|往來|供應|採購)", 5, "競爭搶單", "終止合作"),
    (r"(?:停止|不再)(?:採購|下單|合作|使用)", 4, "競爭搶單", "停止採購"),
    (r"丟(?:單|生意|料號)", 4, "競爭搶單", "丟單"),
    (r"掉(?:單|生意)", 3, "競爭搶單", "掉單"),
    (r"(?:春秋|競品|對手).*?(?:搶|拿|奪|切)", 4, "競爭搶單", "競品搶單"),

    # 我司被客訴/品質爭議（區分自家vs外部）
    (r"我司.*?(?:客訴|抱怨|不滿|投訴|索賠|退貨)", 4, "品質客訴", "我司被客訴"),
    (r"(?:客訴|投訴|索賠|退貨).*?(?:我司|耐落|NYLOK|nylok)", 4, "品質客訴", "我司被客訴"),
    (r"耐落.*?(?:生鏽|鏽蝕|失效|剝落|不良|脫落)", 4, "品質客訴", "耐落品質問題"),
    (r"(?:鹽霧|防鬆|塗佈).*?(?:不合格|失效|不良|問題|異常)", 3, "品質客訴", "我司產品問題"),
    (r"索賠|賠償|罰款", 4, "品質客訴", "賠償索賠"),

    # 帳款
    (r"帳款.*?(?:逾期|未付|催收|拖欠|呆帳)", 3, "帳款問題", "帳款逾期"),
    (r"賬款.*?(?:逾期|未付|催收|拖欠|呆帳)", 3, "帳款問題", "帳款逾期"),
    (r"貨款.*?(?:未付|沒付|拖|催)", 3, "帳款問題", "貨款未付"),
    (r"(?:催收|催款|追討).*?(?:帳款|賬款|貨款)", 3, "帳款問題", "催收"),
    (r"(?:欠款|呆帳|拒付)", 4, "帳款問題", "欠款呆帳"),

    # 營運下滑（針對該客戶）
    (r"(?:訂單|生意|業績).*?(?:下降|下滑|衰退|縮減|減少|砍|削減)", 3, "營運下滑", "訂單下滑"),
    (r"砍單|減量|降量", 3, "營運下滑", "砍單減量"),
    (r"(?:停產|關廠|倒閉|歇業)", 4, "營運下滑", "停產關廠"),

    # 關係惡化
    (r"客戶[^，。]{0,10}(?:不滿|失望|抱怨|質疑|施壓|強硬)", 3, "關係惡化", "客戶不滿"),
    (r"(?:威脅|警告).*?(?:換廠|轉單|不再|停)", 4, "關係惡化", "威脅轉單"),
    (r"關係.*?(?:惡化|緊張|降溫)", 3, "關係惡化", "關係惡化"),

    # 評估/比較對手（中度警訊）
    (r"(?:正在|考慮|評估|比較).*?(?:其他|別家|替代|對手)(?:供應商|廠|品牌|產品)", 3, "競爭搶單", "評估對手"),
    (r"(?:其他|別家|對手).*?(?:報價|試樣|送樣|測試|認證)", 3, "競爭搶單", "對手送樣"),
]

# 降風險的反向 pattern（出現這些字眼則扣分或忽略）
NEGATIVE_INDICATORS = [
    r"非.{0,5}我司",
    r"非.{0,5}耐落",
    r"不(?:是|涉及|關於).{0,8}(?:我司|耐落)",
    r"(?:其他|別家|外包).{0,8}(?:廠|供應商).{0,10}(?:問題|異常|不良)",
    r"未加工.{0,5}(?:耐落|螺絲)",
    r"訂單(?:成長|增加|穩定|順利|起量)",
    r"關係(?:良好|穩定|順利)",
    r"沒有.{0,5}(?:問題|異常|抱怨|客訴)",
    r"(?:整體|大環境|市場).{0,5}下滑",  # 大環境因素
    r"教學|培訓|示範|說明|介紹",
]

# 加重情境（出現會額外加分）
ESCALATION_PATTERNS = [
    (r"(?:已經|確定|明確).{0,8}(?:被搶|流失|切走|轉走)", 1, "情勢明確"),
    (r"(?:大量|嚴重|重大).{0,5}(?:流失|下滑|損失|不良)", 1, "嚴重"),
    (r"客戶[^，。]{0,5}(?:不來|不接|拒絕|拒收)", 1, "客戶迴避"),
]


def score_text(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        return {"risk": 0, "category": "無風險", "hits": [], "reason": ""}

    score = 0
    cats = {}
    reasons = []

    # 反向指標 - 計算後用於折減
    neg_count = sum(1 for p in NEGATIVE_INDICATORS if re.search(p, text))

    # 主風險樣態
    for pat, pts, cat, label in HIGH_RISK_PATTERNS:
        if re.search(pat, text):
            score += pts
            cats[cat] = cats.get(cat, 0) + pts
            reasons.append(label)

    # 升級
    for pat, pts, label in ESCALATION_PATTERNS:
        if re.search(pat, text):
            score += pts
            reasons.append(label)

    # 反向折減：每命中一個反向指標扣 1 分（最多扣到 score 的一半）
    if neg_count:
        deduction = min(neg_count, score // 2 + 1)
        score = max(0, score - deduction)
        reasons.append(f"反向折減-{neg_count}")

    # 換算 risk 0-5
    if score == 0:
        risk = 0
    elif score <= 1:
        risk = 1
    elif score <= 2:
        risk = 2
    elif score <= 4:
        risk = 3
    elif score <= 6:
        risk = 4
    else:
        risk = 5

    category = max(cats.items(), key=lambda x: x[1])[0] if cats else "無風險"

    return {
        "risk": risk,
        "raw_score": score,
        "category": category,
        "hits": reasons[:5],
        "reason": "/".join(reasons[:3]) if reasons else "",
    }


def main():
    print("讀取資料…")
    df = pd.read_excel(INPUT_XLSX, sheet_name="CRM")

    # 排除 TSLG 集團內部
    df = df[~df["公司簡稱"].astype(str).str.contains("TSLG", na=False)].copy()
    df["工作描述"] = df["工作描述"].astype(str)

    # 去重
    df = df.drop_duplicates(subset=["公司簡稱","業務人員","日期","工作描述"]).reset_index(drop=True)
    print(f"外部客戶日誌（去重後）: {len(df)} 筆 / {df['公司簡稱'].nunique()} 客戶")

    print("逐筆評分中…")
    results = df["工作描述"].apply(score_text)
    df["風險分數"] = results.apply(lambda x: x["risk"])
    df["風險類別"] = results.apply(lambda x: x["category"])
    df["判讀理由"] = results.apply(lambda x: x["reason"])
    df["原始分數"] = results.apply(lambda x: x["raw_score"])

    # 客戶層級彙整
    g = df.groupby("公司簡稱")
    cust = pd.DataFrame({
        "客戶等級": g["客戶等級"].first(),
        "業務人員": g["業務人員"].apply(lambda s: ",".join(sorted(set(s.dropna().astype(str))))),
        "接觸次數": g.size(),
        "最高風險分": g["風險分數"].max(),
        "平均風險分": g["風險分數"].mean().round(2),
        "高風險日誌數": g["風險分數"].apply(lambda s: (s >= 3).sum()),
        "主要風險類別": g.apply(
            lambda d: d[d["風險分數"] >= 3]["風險類別"].mode().iloc[0]
            if (d["風險分數"] >= 3).any() else "—"
        ),
    }).reset_index()

    # 拜訪頻率風險：在 2 週內被多次拜訪且工作性質偏異常處理的客戶
    abnormal_natures = ["異常服務處理","客戶品質會議","客訴處理"]
    abn_counts = df[df["工作性質"].isin(abnormal_natures)].groupby("公司簡稱").size()
    cust["異常處理次數"] = cust["公司簡稱"].map(abn_counts).fillna(0).astype(int)

    # 綜合風險分 = 最高 *2 + 平均 + 高風險日誌數 *0.5 + 異常處理次數 *0.5
    cust["綜合風險分"] = (
        cust["最高風險分"] * 2
        + cust["平均風險分"]
        + cust["高風險日誌數"] * 0.5
        + cust["異常處理次數"] * 0.5
    ).round(2)

    cust = cust.sort_values(["綜合風險分","最高風險分"], ascending=False).reset_index(drop=True)

    # 高風險日誌明細
    detail = df[df["風險分數"] >= 3].sort_values("風險分數", ascending=False)[
        ["公司簡稱","業務人員","客戶等級","日期","工作性質","風險分數","風險類別","判讀理由","工作描述"]
    ]

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as w:
        cust.to_excel(w, sheet_name="客戶風險排名", index=False)
        detail.to_excel(w, sheet_name="高風險日誌明細", index=False)

    print(f"\n完成！輸出 {OUTPUT_XLSX}")
    print(f"\n=== 高風險客戶 Top 20 ===")
    print(cust.head(20).to_string(index=False))
    print(f"\n=== 高風險日誌統計 ===")
    print(f"風險分≥3 的日誌: {(df['風險分數']>=3).sum()} 筆")
    print(f"風險分=5 的日誌: {(df['風險分數']==5).sum()} 筆")
    print(f"風險分=4 的日誌: {(df['風險分數']==4).sum()} 筆")
    print(f"風險分=3 的日誌: {(df['風險分數']==3).sum()} 筆")


if __name__ == "__main__":
    main()
