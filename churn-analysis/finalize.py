#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終彙整：以 Claude 親自判讀的結果取代規則分，產出 Excel
"""
import re
import pandas as pd
from judgments import JUDGMENTS

INPUT_XLSX = "/Users/lialilingchen/Downloads/CRM POC資料_2026-04-09.xlsx"
OUTPUT_XLSX = "/Users/lialilingchen/AI agent/churn_analysis/客戶流失風險報告.xlsx"

# 與 score.py 相同的規則樣態（這次只用來標記候選，不直接給分）
RISK_KEYWORDS = [
    "搶","切走","切掉","轉單","流失","競爭","對手","別家","其他供應商","改用","替代","丟單","掉單",
    "異常","客訴","抱怨","不良","生鏽","鏽","鹽霧","失效","剝落","退貨","索賠","投訴",
    "下滑","下降","縮減","不暢","衰退","停產","關廠","砍單",
    "催收","賬款","帳款","逾期","欠款","未付","呆帳",
    "不滿","失望","質疑","拒絕","推脫","拖延","冷淡","施壓",
    "切單","萎縮","減量","降量",
]


def main():
    df = pd.read_excel(INPUT_XLSX, sheet_name="CRM")
    df = df[~df["公司簡稱"].astype(str).str.contains("TSLG", na=False)].copy()
    df["工作描述"] = df["工作描述"].astype(str)
    df = df.drop_duplicates(subset=["公司簡稱","業務人員","日期","工作描述"]).reset_index(drop=True)

    # 第一步：所有日誌預設 0 分
    df["風險分數"] = 0
    df["風險類別"] = "無風險"
    df["判讀理由"] = ""

    # 第二步：找出原本被規則命中的候選（用 score.py 的邏輯重新跑一次，得到 candidates 順序）
    pat = "|".join(map(re.escape, RISK_KEYWORDS))
    candidates_mask = df["工作描述"].str.contains(pat, regex=True)
    candidates = df[candidates_mask].copy().reset_index().rename(columns={"index": "orig_idx"})

    # 直接以原 score.py 產出的 churn_risk_report.xlsx「高風險日誌明細」順序作為 judge_id
    orig_detail = pd.read_excel(
        "/Users/lialilingchen/AI agent/churn_analysis/churn_risk_report.xlsx",
        sheet_name="高風險日誌明細",
    ).reset_index(drop=True)
    orig_detail["judge_id"] = orig_detail.index

    # 用 (公司簡稱, 業務人員, 日期, 工作描述) 作 key 對應到 df
    key_cols = ["公司簡稱","業務人員","日期","工作描述"]
    df_key = df[key_cols].astype(str).apply(lambda r: "|".join(r), axis=1)
    df["__key"] = df_key

    orig_detail["__key"] = orig_detail[key_cols].astype(str).apply(lambda r: "|".join(r), axis=1)

    for _, row in orig_detail.iterrows():
        jid = int(row["judge_id"])
        if jid not in JUDGMENTS:
            continue
        risk, cat, reason = JUDGMENTS[jid]
        match_idx = df.index[df["__key"] == row["__key"]]
        for orig in match_idx:
            df.at[orig, "風險分數"] = risk
            df.at[orig, "風險類別"] = cat
            df.at[orig, "判讀理由"] = reason

    df = df.drop(columns=["__key"])

    # 對於規則命中但未進判讀池的，跑 score 補個保守分
    from score import score_text
    candidates["__score"] = candidates["工作描述"].apply(lambda t: score_text(t)["risk"])

    # 對於規則命中但 risk<3 沒進判讀池的，也跑 score 取個保守分（最多 2）
    for _, row in candidates.iterrows():
        orig = int(row["orig_idx"])
        if df.at[orig, "風險分數"] == 0:  # 還沒被 Claude 判讀
            s = row["__score"]
            if s > 0:
                df.at[orig, "風險分數"] = min(s, 2)
                # 不指定類別，留為「待觀察」
                df.at[orig, "風險類別"] = "待觀察"
                df.at[orig, "判讀理由"] = "規則命中但未達高風險閾值"

    # --- 客戶層級彙整 ---
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
            if (d["風險分數"] >= 3).any() else "—",
            include_groups=False,
        ),
    }).reset_index()

    # 拜訪頻率風險
    abnormal_natures = ["異常服務處理","客戶品質會議"]
    abn_counts = df[df["工作性質"].isin(abnormal_natures)].groupby("公司簡稱").size()
    cust["異常處理次數"] = cust["公司簡稱"].map(abn_counts).fillna(0).astype(int)

    # 綜合分
    cust["綜合風險分"] = (
        cust["最高風險分"] * 2
        + cust["平均風險分"]
        + cust["高風險日誌數"] * 0.5
        + cust["異常處理次數"] * 0.5
    ).round(2)
    cust = cust.sort_values(["綜合風險分","最高風險分","高風險日誌數"], ascending=False).reset_index(drop=True)

    # 高風險日誌明細
    detail = df[df["風險分數"] >= 3].sort_values(["風險分數","公司簡稱"], ascending=[False, True])[
        ["公司簡稱","業務人員","客戶等級","日期","工作性質","風險分數","風險類別","判讀理由","工作描述"]
    ]

    # 摘要分頁
    summary_rows = [
        ["分析日期區間", f"{df['日期'].min()} ~ {df['日期'].max()}"],
        ["外部客戶日誌總數", len(df)],
        ["外部客戶數", df["公司簡稱"].nunique()],
        ["高風險日誌(≥3)總數", (df["風險分數"] >= 3).sum()],
        ["高風險客戶(綜合分≥10)數", (cust["綜合風險分"] >= 10).sum()],
        ["", ""],
        ["Risk=5 日誌數", (df["風險分數"] == 5).sum()],
        ["Risk=4 日誌數", (df["風險分數"] == 4).sum()],
        ["Risk=3 日誌數", (df["風險分數"] == 3).sum()],
    ]
    summary = pd.DataFrame(summary_rows, columns=["項目","數值"])

    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as w:
        summary.to_excel(w, sheet_name="總覽", index=False)
        cust.to_excel(w, sheet_name="客戶風險排名", index=False)
        detail.to_excel(w, sheet_name="高風險日誌明細", index=False)

        # 調整欄寬
        for sheet_name in ["總覽","客戶風險排名","高風險日誌明細"]:
            ws = w.sheets[sheet_name]
            for col in ws.columns:
                col_letter = col[0].column_letter
                max_len = 12
                for cell in col:
                    try:
                        v = str(cell.value) if cell.value is not None else ""
                        max_len = max(max_len, min(len(v) * 2, 60))
                    except Exception:
                        pass
                ws.column_dimensions[col_letter].width = max_len

    print(f"完成！輸出 {OUTPUT_XLSX}")
    print(f"\n=== 高風險客戶 Top 20 ===")
    print(cust.head(20).to_string(index=False))
    print(f"\n=== Risk 分布 ===")
    print(df["風險分數"].value_counts().sort_index())


if __name__ == "__main__":
    main()
