# -*- coding: utf-8 -*-
"""精確掃描真正的 emoji（排除中日韓文字）"""
import json, urllib.request, ssl, re
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]

# Only match real emoji (not CJK characters)
# This regex targets pictographic/symbol emoji only
emoji_re = re.compile(
    "[\U0001F600-\U0001F64F"   # emoticons (smileys)
    "\U0001F300-\U0001F5FF"    # symbols & pictographs
    "\U0001F680-\U0001F6FF"    # transport
    "\U0001F900-\U0001F9FF"    # supplemental symbols
    "\U0001FA00-\U0001FA6F"    # chess, extended-A
    "\U0001FA70-\U0001FAFF"    # extended-A cont
    "\U00002702-\U000027B0"    # dingbats
    "\U0000FE0F"               # variation selector
    "\U0000200D"               # ZWJ
    "\U00002600-\U000026FF"    # misc symbols (⚠️☀️ etc) — but not CJK
    "\U00002700-\U000027BF"    # dingbats
    "\U0001F1E0-\U0001F1FF"    # flags
    "]+", re.UNICODE
)

# Specific emoji chars commonly used in UI
specific_emoji = set("👥⏳📅⚠️🤖📊📈🚨✅❌🔴🟡🟢💡🎉✕✓☀️🌟⭐🏥🌍💬🔥✨💰📋🗓️📌🔔💻🏠🏢🎯⚡🛡️")

print("=" * 60)
print("  前端顏文字 (Emoji) 精確掃描")
print("=" * 60)

all_findings = {}

for path in sorted(vfs):
    if not path.endswith((".tsx", ".ts")):
        continue
    if path.startswith("actions/"):
        continue
    content = vfs[path]
    lines = content.split("\n")
    found = []
    for i, line in enumerate(lines):
        # Method 1: regex
        for m in emoji_re.finditer(line):
            char = m.group()
            # Skip variation selector alone
            if char == "\uFE0F" or char == "\u200D":
                continue
            found.append((i + 1, char, line.strip()[:120]))
        # Method 2: check each char
        for ci, ch in enumerate(line):
            cp = ord(ch)
            # Real emoji ranges (not CJK)
            if 0x1F600 <= cp <= 0x1F64F or \
               0x1F300 <= cp <= 0x1F5FF or \
               0x1F680 <= cp <= 0x1F6FF or \
               0x1F900 <= cp <= 0x1F9FF or \
               0x1FA00 <= cp <= 0x1FAFF:
                ctx = line.strip()[:120]
                entry = (i + 1, ch, ctx)
                if entry not in found:
                    found.append(entry)

    if found:
        # Deduplicate
        seen = set()
        unique = []
        for f in found:
            key = (f[0], f[1])
            if key not in seen:
                seen.add(key)
                unique.append(f)
        all_findings[path] = unique

total = sum(len(v) for v in all_findings.values())
for path, items in all_findings.items():
    print(f"\n  {path} ({len(items)} 處)")
    for lineno, emoji_char, context in items:
        # Show the emoji and its unicode codepoint
        cps = " ".join(f"U+{ord(c):04X}" for c in emoji_char)
        print(f"    L{lineno}: {emoji_char} ({cps})")
        print(f"           → {context[:100]}")

print(f"\n  總計: {total} 處真正的 emoji，分佈在 {len(all_findings)} 個檔案")

# === Style issues ===
print("\n" + "=" * 60)
print("  樣式引用問題")
print("=" * 60)

# 1. CSS escape issue
app_css = vfs.get("src/App.css", "")
# Find recharts-related selectors with backslash escapes
problematic_css = []
for i, line in enumerate(app_css.split("\n")):
    if "\\[" in line or "\\#" in line or "recharts" in line:
        problematic_css.append((i + 1, line.strip()[:120]))

if problematic_css:
    print(f"\n  CSS 疑似問題選擇器 ({len(problematic_css)} 處):")
    for lineno, ctx in problematic_css[:10]:
        print(f"    L{lineno}: {ctx}")

# 2. ListPage import issue
listpage = vfs.get("src/pages/ListPage.tsx", "")
if "data.json" in listpage:
    has_data_json = "src/data.json" in vfs or "data.json" in vfs
    print(f"\n  ListPage.tsx import data.json: {'✅ 存在' if has_data_json else '❌ 不存在'}")

print("\n" + "=" * 60)
