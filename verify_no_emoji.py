# -*- coding: utf-8 -*-
"""驗證所有 churn-analysis HTML 無 emoji"""
import re, os, urllib.request

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0000FE00-\U0000FE0F"
    "\U0001F900-\U0001F9FF"
    "\U0000200D"
    "]+", re.UNICODE
)

urls = [
    ("index.html", "http://localhost:8800/"),
    ("sales-input", "http://localhost:8800/churn-analysis/sales-input.html"),
    ("manager-dashboard", "http://localhost:8800/churn-analysis/manager-dashboard.html"),
]

all_ok = True
for name, url in urls:
    with urllib.request.urlopen(url, timeout=5) as r:
        content = r.read().decode("utf-8")
    matches = EMOJI_RE.findall(content)
    if matches:
        all_ok = False
        print(f"  FAIL {name}: {len(matches)} emoji 殘留")
        for m in matches[:10]:
            # Find context
            idx = content.index(m)
            ctx = content[max(0,idx-20):idx+len(m)+20].replace('\n',' ')
            print(f"    {repr(m)} @ ...{ctx}...")
    else:
        print(f"  OK   {name}: 無 emoji")

# Also check local files
BASE = r"c:\Users\User\dev project\AI GO-MODEL\nailuo-hr-pocs"
for fpath in [
    os.path.join(BASE, "index.html"),
    os.path.join(BASE, "churn-analysis", "sales-input.html"),
    os.path.join(BASE, "churn-analysis", "manager-dashboard.html"),
]:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    matches = EMOJI_RE.findall(content)
    name = os.path.basename(fpath)
    if matches:
        all_ok = False
        print(f"  FAIL (local) {name}: {len(matches)} emoji")
        for m in matches[:5]:
            idx = content.index(m)
            ctx = content[max(0,idx-30):idx+len(m)+30].replace('\n',' ')
            print(f"    {repr(m)} @ ...{ctx}...")
    else:
        print(f"  OK   (local) {name}: clean")

print(f"\n{'PASS' if all_ok else 'FAIL'}")
