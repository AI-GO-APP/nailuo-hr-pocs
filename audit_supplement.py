# -*- coding: utf-8 -*-
"""補充調查：routes.ts 實際結構、manifest.json、PayslipsPage 引用"""
import json, urllib.request, ssl
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

# routes.ts 完整內容
print("=== routes.ts ===")
routes = vfs.get("src/routes.ts", "")
for i, line in enumerate(routes.split("\n")):
    print(f"  L{i+1}: {line[:130]}")

# manifest.json 完整內容
print("\n=== manifest.json ===")
manifest = vfs.get("manifest.json", "")
print(f"  {manifest[:500]}")

# App.tsx 完整 — 看路由如何組裝
print("\n=== App.tsx ===")
app_tsx = vfs.get("src/App.tsx", "")
for i, line in enumerate(app_tsx.split("\n")):
    print(f"  L{i+1}: {line[:130]}")

# 查看 BonusRulesPage 是否有任何引用
print("\n=== BonusRulesPage 引用 ===")
for path in sorted(vfs):
    if path == "src/pages/BonusRulesPage.tsx":
        continue
    content = vfs.get(path, "")
    if "BonusRules" in content:
        print(f"  {path}")

# 查看 PayslipsPage 引用
print("\n=== PayslipsPage 引用 ===")
for path in sorted(vfs):
    if path == "src/pages/PayslipsPage.tsx":
        continue
    content = vfs.get(path, "")
    if "PayslipsPage" in content or "Payslips" in content:
        print(f"  {path}")

# 查看 summarize_leads action
print("\n=== summarize_leads ===")
sl = vfs.get("actions/summarize_leads.py", "")
for i, line in enumerate(sl.split("\n")[:10]):
    print(f"  L{i+1}: {line[:120]}")
# Where is it called?
for path in sorted(vfs):
    if "summarize_leads" in vfs.get(path, "") and path != "actions/summarize_leads.py":
        print(f"  called from: {path}")

# 查看 manage_leaves, confirm_payroll_run 是否被呼叫
for action_name in ["manage_leaves", "confirm_payroll_run", "run_monthly_payroll"]:
    callers = []
    for path in sorted(vfs):
        if path.startswith("actions/"):
            continue
        if action_name in vfs.get(path, ""):
            callers.append(path)
    status = "called" if callers else "NOT called"
    print(f"\n  {action_name}: {status} — {callers}")

# PayslipDetail 引用
print("\n=== PayslipDetail 引用 ===")
for path in sorted(vfs):
    if "PayslipDetail" in vfs.get(path, "") and path != "src/components/PayslipDetail.tsx":
        print(f"  {path}")
