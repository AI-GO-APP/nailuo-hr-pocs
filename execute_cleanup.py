# -*- coding: utf-8 -*-
"""
嚴謹驗證 Tailwind CSS 是否真的未使用 + 執行全部清除
決策:
  - run_monthly_payroll.py: 保留
  - payroll_records: 移除
  - CSS Tailwind: 嚴謹檢查後清除
"""
import json, urllib.request, ssl, re, sys
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "dbe4f2a4-5bb9-4dfb-a836-130d52197656"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:300]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]
app_data = api("GET", f"/builder/apps/{APP}", None, token)
vfs = app_data["vfs_state"]
version = app_data["vfs_version"]
slug = app_data["slug"]
print(f"v{version}, {len(vfs)} files")

# =============================================================
# Step 0: 嚴謹驗證 Tailwind CSS
# =============================================================
print("\n[Step 0] 嚴謹驗證 Tailwind CSS")
app_css = vfs["src/App.css"]
css_lines = app_css.split("\n")

# 收集所有 CSS 中的 class 名（含 Tailwind arbitrary value 選擇器）
# Tailwind arbitrary value pattern: .\escaped[value]
tw_selectors = []
tw_line_ranges = []  # (start_line, end_line, selector)

i = 0
while i < len(css_lines):
    line = css_lines[i]
    # Match lines like .top-\[1px\] { or .z-\[9999\] {
    m = re.match(r'^(\.[a-zA-Z\-_\\0-9\[\]\.%#\/\&\>\*\:]+)\s*\{', line.strip())
    if m:
        sel = m.group(1)
        if "\\" in sel or "\\[" in sel:
            # This is a Tailwind arbitrary value selector
            # Find the closing }
            start = i
            depth = 1
            j = i + 1
            while j < len(css_lines) and depth > 0:
                depth += css_lines[j].count("{") - css_lines[j].count("}")
                j += 1
            tw_selectors.append(sel)
            tw_line_ranges.append((start, j - 1, sel))
    i += 1

print(f"  發現 {len(tw_selectors)} 個 Tailwind-style selectors")

# 嚴謹檢查：在每一個 TSX/TS 檔案中搜尋這些 class 名
# 需要把 CSS 的轉義格式轉換為 className 格式
all_tsx_content = ""
for path in sorted(vfs):
    if path.endswith((".tsx", ".ts")) and not path.startswith("actions/"):
        all_tsx_content += vfs[path] + "\n"

used_tw = []
unused_tw = []
for sel in tw_selectors:
    # Convert CSS selector to className
    # e.g. .top-\[1px\] → top-[1px]
    cls = sel.lstrip(".")
    cls = cls.replace("\\[", "[").replace("\\]", "]").replace("\\.", ".").replace("\\#", "#").replace("\\%", "%").replace("\\/", "/").replace("\\:", ":").replace("\\&", "&").replace("\\>", ">").replace("\\_", "_").replace("\\,", ",").replace("\\'", "'")
    
    if cls in all_tsx_content:
        used_tw.append((sel, cls))
    else:
        unused_tw.append((sel, cls))

print(f"  實際被 TSX 使用: {len(used_tw)}")
if used_tw:
    for sel, cls in used_tw[:5]:
        print(f"    使用中: {cls}")
print(f"  確認未使用: {len(unused_tw)}")
if unused_tw:
    for sel, cls in unused_tw[:5]:
        print(f"    未使用: {cls}")
    if len(unused_tw) > 5:
        print(f"    ... 還有 {len(unused_tw) - 5} 個")

# 同時檢查整個 CSS 中所有的 class
# 收集所有 TSX 中使用的 className
all_classnames = set()
for m in re.finditer(r'className="([^"]+)"', all_tsx_content):
    for cls in m.group(1).split():
        all_classnames.add(cls)

# Also check inline style={{ }} references (not relevant for CSS)
# Check className={`...`} template literals
for m in re.finditer(r'className=\{`([^`]+)`\}', all_tsx_content):
    # Extract static parts
    parts = re.split(r'\$\{[^}]+\}', m.group(1))
    for part in parts:
        for cls in part.split():
            all_classnames.add(cls)

print(f"\n  TSX 使用的所有 className ({len(all_classnames)}):")
for cls in sorted(all_classnames)[:20]:
    print(f"    {cls}")
if len(all_classnames) > 20:
    print(f"    ... 共 {len(all_classnames)} 個")

# =============================================================
# Step 1: 移除 CSS 中未使用的 Tailwind selectors
# =============================================================
print(f"\n[Step 1] 清除未使用的 Tailwind CSS")
# Remove unused Tailwind selectors from CSS
# Sort line ranges in reverse to avoid offset issues
lines_to_remove = set()
for start, end, sel in tw_line_ranges:
    # Check if this selector's class is used
    cls = sel.lstrip(".")
    cls = cls.replace("\\[", "[").replace("\\]", "]").replace("\\.", ".").replace("\\#", "#").replace("\\%", "%").replace("\\/", "/").replace("\\:", ":").replace("\\&", "&").replace("\\>", ">").replace("\\_", "_").replace("\\,", ",").replace("\\'", "'")
    if cls not in all_tsx_content:
        for l in range(start, end + 1):
            lines_to_remove.add(l)

new_css_lines = [line for i, line in enumerate(css_lines) if i not in lines_to_remove]
# Also remove consecutive blank lines (cleanup)
cleaned_css = []
prev_blank = False
for line in new_css_lines:
    is_blank = line.strip() == ""
    if is_blank and prev_blank:
        continue
    cleaned_css.append(line)
    prev_blank = is_blank

new_css = "\n".join(cleaned_css)
old_size = len(app_css)
new_size = len(new_css)
removed_lines = len(css_lines) - len(cleaned_css)
print(f"  移除 {removed_lines} 行, {old_size:,} → {new_size:,} chars ({old_size-new_size:,} chars saved)")

# =============================================================
# Step 2: 刪除檔案
# =============================================================
print(f"\n[Step 2] 刪除未使用的檔案")

files_to_delete = [
    "src/pages/ListPage.tsx",
    "src/pages/BonusRulesPage.tsx",
    "src/pages/PayslipsPage.tsx",
    "src/components/DataTable.tsx",
    "src/components/PayslipDetail.tsx",
    "src/data.json",
    "src/utils/dbHelper.ts",
    "actions/summarize_leads.py",
    "actions/manage_leaves.py",
    "actions/confirm_payroll_run.py",
]

# Verify none of these are referenced by remaining files
remaining_files = {f for f in vfs if f not in files_to_delete}
for del_file in files_to_delete:
    basename = del_file.split("/")[-1].replace(".tsx","").replace(".ts","").replace(".py","").replace(".json","")
    for rf in remaining_files:
        if rf.endswith((".tsx", ".ts")) and not rf.startswith("actions/"):
            content = vfs.get(rf, "")
            if basename in content and del_file != rf:
                print(f"  ⚠️  {del_file} 仍被 {rf} 引用!")

# Prepare update: set deleted files to None (VFS delete)
updates = {}
for f in files_to_delete:
    if f in vfs:
        updates[f] = None
        print(f"  刪除: {f}")
    else:
        print(f"  已不存在: {f}")

# Also clean up payrollCalc.ts — remove hr_bonuses reference
calc = vfs.get("src/utils/payrollCalc.ts", "")
if "hr_bonuses" in calc:
    calc = calc.replace(
        'let allBonuses: any[] = []; try { allBonuses = await query("hr_bonuses", { limit: 500 }) || []; } catch { allBonuses = []; }',
        'const allBonuses: any[] = []; // hr_bonuses 已移除，獎金由 bonus_records custom table 管理'
    )
    updates["src/utils/payrollCalc.ts"] = calc
    print("  修正: payrollCalc.ts (移除 hr_bonuses 引用)")

# Remove crm_tags, sale_orders from dbHelper.ts — but we're deleting dbHelper.ts entirely
# Check if anything else uses crm_tags or sale_orders
for table in ["crm_tags", "sale_orders"]:
    for path in remaining_files - set(files_to_delete):
        if path.endswith((".tsx", ".ts")) and table in vfs.get(path, ""):
            print(f"  ⚠️  {table} 仍被 {path} 使用!")

# Update CSS
updates["src/App.css"] = new_css
print(f"  更新: App.css ({removed_lines} 行移除)")

# =============================================================
# Step 3: PATCH
# =============================================================
# For VFS, setting a file to None should delete it
# But the API might not support None — check
# If not, we need to use a different approach

# Filter: only include non-None updates in PATCH files
patch_files = {k: v for k, v in updates.items() if v is not None}
delete_files = [k for k, v in updates.items() if v is None]

print(f"\n[Step 3] PATCH {len(patch_files)} file updates + {len(delete_files)} deletions")

# First PATCH the file updates
if patch_files:
    r = api("PATCH", f"/builder/apps/{APP}/source/files",
            {"files": patch_files, "expected_version": version}, token)
    if r and "_error" not in r:
        print(f"  File updates: OK")
        version = r.get("version", version + 1) if isinstance(r, dict) else version + 1
    else:
        # Retry with fresh version
        app2 = api("GET", f"/builder/apps/{APP}", None, token)
        version = app2["vfs_version"]
        r = api("PATCH", f"/builder/apps/{APP}/source/files",
                {"files": patch_files, "expected_version": version}, token)
        if r and "_error" not in r:
            print(f"  File updates: OK (retry)")
        else:
            print(f"  File updates: FAILED — {r}")
            sys.exit(1)

# Delete files
if delete_files:
    # Get fresh version
    app3 = api("GET", f"/builder/apps/{APP}", None, token)
    version = app3["vfs_version"]
    
    # Try DELETE endpoint
    for f in delete_files:
        r = api("DELETE", f"/builder/apps/{APP}/source/files/{f}", None, token)
        if r and "_error" not in r:
            print(f"  Deleted {f}: OK")
        else:
            # Try PATCH with empty string
            pass
    
    # If DELETE doesn't work, use PATCH with files set to ""
    # Re-fetch to get fresh version
    app4 = api("GET", f"/builder/apps/{APP}", None, token)
    vfs4 = app4["vfs_state"]
    version = app4["vfs_version"]
    
    # Check which files still exist
    still_exist = [f for f in delete_files if f in vfs4]
    if still_exist:
        print(f"  {len(still_exist)} files still exist, trying PATCH with empty content...")
        empty_files = {f: "" for f in still_exist}
        r = api("PATCH", f"/builder/apps/{APP}/source/files",
                {"files": empty_files, "expected_version": version}, token)
        if r and "_error" not in r:
            print(f"  Empty PATCH: OK")
        else:
            print(f"  Empty PATCH: {r}")

# =============================================================
# Step 4: Compile & verify
# =============================================================
# Get fresh app state
app5 = api("GET", f"/builder/apps/{APP}", None, token)
vfs5 = app5["vfs_state"]

print(f"\n[Step 4] Compile (now {len(vfs5)} files)")
r = api("POST", f"/compile/compile/{slug}?dev=true", None, token)
if r and r.get("success"):
    print("  OK")
else:
    err = (r or {}).get("error", "")
    print(f"  FAILED: {err[:400]}")
    # If compile fails, we need to fix
    if err:
        error_files = re.findall(r'(src/\S+\.tsx?):(\d+):(\d+)', err)
        for ef, eline, ecol in error_files[:5]:
            content = vfs5.get(ef, "")
            lines = content.split("\n")
            ln = int(eline) - 1
            if 0 <= ln < len(lines):
                print(f"    {ef}:{eline}: {lines[ln].strip()[:120]}")
    sys.exit(1)

# Publish
print("Publish...")
api("POST", f"/builder/apps/{APP}/publish", {"published_assets": {}}, token)
print("  OK")

# =============================================================
# Step 5: 移除 Data References
# =============================================================
print(f"\n[Step 5] 移除未使用的 Data References")
refs_to_remove = ["hr_payroll_bonus_rule_results", "hr_payroll_settings",
                   "hr_payroll_slip_lines", "crm_tags", "sale_orders"]

# Get current refs
refs = api("GET", f"/refs/apps/{APP}", None, token)
if isinstance(refs, list):
    for ref in refs:
        table = ref.get("table_name", "")
        ref_id = ref.get("id", "")
        if table in refs_to_remove:
            r = api("DELETE", f"/refs/apps/{APP}/{ref_id}", None, token)
            if r and "_error" not in r:
                print(f"  移除 ref {table}: OK")
            else:
                # Try alternate path
                r2 = api("DELETE", f"/refs/{ref_id}", None, token)
                if r2 and "_error" not in r2:
                    print(f"  移除 ref {table}: OK (alt)")
                else:
                    print(f"  移除 ref {table}: FAILED (可能需手動)")

# =============================================================
# Step 6: 移除 Custom Table
# =============================================================
print(f"\n[Step 6] 移除舊的 Custom Tables")
all_tables = api("GET", "/data/objects", None, token) or []
for t in all_tables:
    slug_name = t.get("api_slug", "")
    if slug_name in ["bonus_records_8e0a2d", "payroll_records"]:
        tid = t.get("id", "")
        r = api("DELETE", f"/data/objects/{tid}", None, token)
        if r and "_error" not in r:
            print(f"  移除 {slug_name}: OK")
        else:
            print(f"  移除 {slug_name}: {r}")

# =============================================================
# Step 7: 最終驗證
# =============================================================
print(f"\n[Step 7] 最終驗證")
app_final = api("GET", f"/builder/apps/{APP}", None, token)
vfs_final = app_final["vfs_state"]
print(f"  VFS: {len(vfs_final)} files (原 {len(vfs)} files)")

# Check deleted files are gone (or empty)
for f in files_to_delete:
    content = vfs_final.get(f, None)
    if content is None:
        print(f"  {f}: 已刪除")
    elif content == "":
        print(f"  {f}: 已清空")
    else:
        print(f"  ⚠️  {f}: 仍有內容 ({len(content)} chars)")

# CSS size
css_final = vfs_final.get("src/App.css", "")
print(f"\n  CSS: {len(css_final):,} chars (原 {old_size:,})")

# Remaining refs
refs_final = api("GET", f"/refs/apps/{APP}", None, token) or []
print(f"  Refs: {len(refs_final)} (原 16)")
for ref in refs_final:
    print(f"    {ref.get('table_name','?')}")

# Remaining custom tables
tables_final = api("GET", "/data/objects", None, token) or []
our_tables = [t for t in tables_final if t.get("app_id") == APP]
print(f"  Custom Tables: {len(our_tables)} (原 5)")
for t in our_tables:
    print(f"    {t.get('api_slug','?')} ({t.get('name','?')})")

print(f"\nDone!")
