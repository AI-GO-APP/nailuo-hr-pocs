# -*- coding: utf-8 -*-
"""檢查前端 VFS 中的顏文字 (emoji) 和樣式引用問題"""
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

# Emoji regex: matches most emoji ranges
emoji_re = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"
    "\U0001f900-\U0001f9FF"  # supplemental symbols
    "\U00002600-\U000026FF"  # misc symbols
    "\U0000200D"             # ZWJ
    "\U0000FE0F"             # variation selector
    "\U00002B50"             # star
    "\U000023F3"             # hourglass
    "\U0000231A-\U0000231B"
    "\U00002934-\U00002935"
    "\U000025AA-\U000025AB"
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
    "\U00002B55"
    "\U00003030"
    "\U0000303D"
    "\U00003297"
    "\U00003299"
    "]+", re.UNICODE
)

print("=" * 60)
print("  顏文字 (Emoji) 掃描")
print("=" * 60)

total_emoji_count = 0
files_with_emoji = {}

for path in sorted(vfs):
    if not (path.startswith("src/") and path.endswith(".tsx")) and \
       not (path.startswith("src/") and path.endswith(".ts")):
        continue
    content = vfs[path]
    lines = content.split("\n")
    found = []
    for i, line in enumerate(lines):
        matches = emoji_re.findall(line)
        if matches:
            for m in matches:
                found.append((i + 1, m, line.strip()[:120]))
    if found:
        files_with_emoji[path] = found
        total_emoji_count += len(found)

for path, items in files_with_emoji.items():
    print(f"\n  📄 {path} ({len(items)} 處)")
    for lineno, emoji, context in items:
        print(f"    L{lineno}: [{emoji}] → {context[:100]}")

print(f"\n  總計: {total_emoji_count} 處顏文字，分佈在 {len(files_with_emoji)} 個檔案")

# === Style reference check ===
print("\n" + "=" * 60)
print("  樣式引用檢查")
print("=" * 60)

app_css = vfs.get("src/App.css", "")

# 1. Collect all className references from TSX
class_re = re.compile(r'className="([^"]+)"')
all_classes_used = set()
class_usage = {}  # class -> [(file, line)]

for path in sorted(vfs):
    if not path.endswith(".tsx"):
        continue
    content = vfs[path]
    for i, line in enumerate(content.split("\n")):
        for m in class_re.finditer(line):
            for cls in m.group(1).split():
                all_classes_used.add(cls)
                class_usage.setdefault(cls, []).append((path, i + 1))

# 2. Collect classes defined in CSS
css_class_re = re.compile(r'\.([a-zA-Z_][\w-]*)\s*[{,:]')
defined_classes = set()
for m in css_class_re.finditer(app_css):
    defined_classes.add(m.group(1))

# 3. Check for inline style issues in TSX
print("\n  --- className 引用檢查 ---")
# Only flag custom-looking classes (skip common utility names)
utility_prefixes = {"flex", "grid", "text-", "bg-", "border-", "rounded-", "p-", "m-",
                    "w-", "h-", "min-", "max-", "gap-", "items-", "justify-", "overflow-",
                    "hidden", "block", "inline", "relative", "absolute", "fixed", "sticky"}
missing = []
for cls in sorted(all_classes_used):
    if cls in defined_classes:
        continue
    # Skip if it looks like a tailwind utility
    is_utility = any(cls.startswith(p) for p in utility_prefixes)
    if is_utility:
        continue
    # Custom class names that might be missing from CSS
    if "-" in cls or "_" in cls or cls[0].isupper():
        continue  # likely a CSS module or framework class
    # Simple custom names
    usages = class_usage.get(cls, [])
    if usages:
        missing.append((cls, usages))

if missing:
    for cls, usages in missing:
        locs = ", ".join(f"{f.split('/')[-1]}:L{l}" for f, l in usages[:3])
        in_css = cls in app_css
        print(f"    className=\"{cls}\" → {'✅ found in CSS' if in_css else '⚠️  NOT in CSS'} (used in {locs})")
else:
    print("    ✅ 所有 className 引用無明顯問題")

# 4. Check CSS for common issues
print("\n  --- CSS 語法掃描 ---")
css_issues = []

# Check for invalid escape sequences
invalid_escapes = re.findall(r"\\#[a-fA-F0-9]", app_css)
if invalid_escapes:
    css_issues.append(f"疑似無效轉義序列: {invalid_escapes[:5]}")

# Check for broken selectors
broken_selectors = re.findall(r'\.\\\[.*?\]', app_css)
if broken_selectors:
    css_issues.append(f"可能有問題的選擇器: {broken_selectors[:3]}")

# Check :host usage
if ":host" not in app_css:
    css_issues.append(":host 選擇器缺失")

# Check for duplicate property warnings
if css_issues:
    for issue in css_issues:
        print(f"    ⚠️  {issue}")
else:
    print("    ✅ CSS 無明顯語法問題")

# 5. Check for import issues
print("\n  --- Import 引用檢查 ---")
import_issues = []
for path in sorted(vfs):
    if not path.endswith(".tsx") and not path.endswith(".ts"):
        continue
    if path.startswith("actions/"):
        continue
    content = vfs[path]
    for i, line in enumerate(content.split("\n")):
        if line.strip().startswith("import ") and " from " in line:
            # Extract module path
            m2 = re.search(r'from\s+"([^"]+)"', line)
            if not m2:
                m2 = re.search(r"from\s+'([^']+)'", line)
            if m2:
                mod = m2.group(1)
                if mod.startswith("."):
                    # Resolve relative path
                    parts = path.split("/")
                    base_dir = "/".join(parts[:-1])
                    resolved = mod.replace("../", "").replace("./", "")
                    # Try finding the file
                    candidates = [
                        f"{base_dir}/{resolved}.tsx",
                        f"{base_dir}/{resolved}.ts",
                        f"{base_dir}/{resolved}/index.tsx",
                        f"{base_dir}/{resolved}/index.ts",
                    ]
                    if mod.startswith("../"):
                        parent = "/".join(parts[:-2])
                        rest = mod.replace("../", "", 1)
                        candidates = [
                            f"{parent}/{rest}.tsx",
                            f"{parent}/{rest}.ts",
                            f"{parent}/{rest}/index.tsx",
                            f"{parent}/{rest}/index.ts",
                        ]
                    found = any(c in vfs for c in candidates)
                    if not found:
                        import_issues.append((path, i + 1, mod, line.strip()[:100]))

if import_issues:
    for fpath, lineno, mod, ctx in import_issues:
        print(f"    ⚠️  {fpath.split('/')[-1]}:L{lineno} → import \"{mod}\" 找不到")
else:
    print("    ✅ 所有 import 引用正確")

print("\n" + "=" * 60)
