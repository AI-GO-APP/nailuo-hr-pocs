# -*- coding: utf-8 -*-
"""掃描並移除 churn-analysis HTML 中的 emoji"""
import re, os

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # 各種符號與象形文字
    "\U00002600-\U000027BF"  # 雜項符號
    "\U0000FE00-\U0000FE0F"  # 變體選擇器
    "\U0000200D"             # 零寬連接
    "\U0000231A-\U0000231B"
    "\U00002328"
    "\U000023CF"
    "\U000023E9-\U000023F3"
    "\U000023F8-\U000023FA"
    "\U00002934-\U00002935"
    "\U000025AA-\U000025AB"
    "\U000025B6"
    "\U000025C0"
    "\U000025FB-\U000025FE"
    "\U00002614-\U00002615"
    "\U00002648-\U00002653"
    "\U0000267F"
    "\U00002693"
    "\U000026A1"
    "\U000026AA-\U000026AB"
    "\U000026BD-\U000026BE"
    "\U000026C4-\U000026C5"
    "\U000026CE"
    "\U000026D4"
    "\U000026EA"
    "\U000026F2-\U000026F3"
    "\U000026F5"
    "\U000026FA"
    "\U000026FD"
    "\U00002702"
    "\U00002705"
    "\U00002708-\U0000270D"
    "\U0000270F"
    "\U00002712"
    "\U00002714"
    "\U00002716"
    "\U0000271D"
    "\U00002721"
    "\U00002728"
    "\U00002733-\U00002734"
    "\U00002744"
    "\U00002747"
    "\U0000274C"
    "\U0000274E"
    "\U00002753-\U00002755"
    "\U00002757"
    "\U00002763-\U00002764"
    "\U00002795-\U00002797"
    "\U000027A1"
    "\U000027B0"
    "\U00002B05-\U00002B07"
    "\U00002B1B-\U00002B1C"
    "\U00002B50"
    "\U00002B55"
    "\U00003030"
    "\U0000303D"
    "\U00003297"
    "\U00003299"
    "]+", re.UNICODE
)

BASE = r"c:\Users\User\dev project\AI GO-MODEL\nailuo-hr-pocs\churn-analysis"

for fname in ["sales-input.html", "manager-dashboard.html"]:
    fpath = os.path.join(BASE, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find all emoji with line numbers
    lines = content.split("\n")
    total_found = 0
    for i, line in enumerate(lines):
        matches = EMOJI_RE.findall(line)
        if matches:
            total_found += len(matches)
            trimmed = line.strip()[:120]
            emojis = " ".join(matches)
            print(f"  {fname}:L{i+1}: [{emojis}] {trimmed}")
    
    # Remove emoji
    cleaned = EMOJI_RE.sub("", content)
    
    # Clean up leftover spaces (e.g. "💥 客戶" → " 客戶" → "客戶")
    # But be careful not to remove meaningful spaces
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(cleaned)
    
    print(f"\n  {fname}: {total_found} emoji 已移除\n")

# Verify
print("=== 驗證 ===")
for fname in ["sales-input.html", "manager-dashboard.html"]:
    fpath = os.path.join(BASE, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    remaining = EMOJI_RE.findall(content)
    print(f"  {fname}: {len(remaining)} emoji 剩餘")
