# -*- coding: utf-8 -*-
"""
修改所有三個頁面：
1. AI 生成中 → 顯示 shimmer 骨架動畫
2. AI 回傳 → 用 Markdown 簡易解析渲染
3. 新增 Markdown 渲染元件到 VFS
4. 新增 shimmer CSS
"""
import json, urllib.request, ssl, time
ssl._create_default_https_context = ssl._create_unverified_context
BASE = "https://ai-go.app/api/v1"
APP = "7c80cf79-7225-49b6-9657-3f8c719658ec"
SLUG = "da1900f990b0"

def api(m, p, d=None, t=None):
    body = json.dumps(d).encode("utf-8") if d else None
    req = urllib.request.Request(f"{BASE}{p}", data=body, method=m)
    req.add_header("Content-Type", "application/json")
    if t: req.add_header("Authorization", f"Bearer {t}")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_detail": e.read().decode()[:1000]}

auth = api("POST", "/auth/login", {"email":"admin@tslg.com.tw","password":"password123"})
token = auth["access_token"]

# =============================================
# 1. Markdown 渲染元件
# =============================================
markdown_tsx = r'''import React from "react";

/**
 * 輕量 Markdown 渲染元件
 * 支援：**粗體**、*斜體*、- 無序列表、1. 有序列表、換行
 */
export default function MarkdownText({ text }: { text: string }) {
  if (!text) return null;

  // 按段落分割（雙換行 or 單換行）
  const blocks = text.split(/\n/).map(l => l.trimEnd());

  const rendered: React.ReactNode[] = [];
  let listItems: string[] = [];
  let listType: "ul" | "ol" | null = null;
  let idx = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    const Tag = listType === "ol" ? "ol" : "ul";
    rendered.push(
      <Tag key={`list-${idx++}`} className="md-list">
        {listItems.map((item, i) => <li key={i}>{inlineParse(item)}</li>)}
      </Tag>
    );
    listItems = [];
    listType = null;
  };

  for (const line of blocks) {
    // 空行 → flush
    if (!line.trim()) {
      flushList();
      continue;
    }

    // 無序列表：- 或 * 開頭
    const ulMatch = line.match(/^[\-\*]\s+(.+)/);
    if (ulMatch) {
      if (listType === "ol") flushList();
      listType = "ul";
      listItems.push(ulMatch[1]);
      continue;
    }

    // 有序列表：1. 2. 等
    const olMatch = line.match(/^\d+[\.\)]\s*(.+)/);
    if (olMatch) {
      if (listType === "ul") flushList();
      listType = "ol";
      listItems.push(olMatch[1]);
      continue;
    }

    // 非列表 → flush 之前的列表
    flushList();

    // 普通段落
    rendered.push(<p key={`p-${idx++}`} className="md-p">{inlineParse(line)}</p>);
  }

  flushList();

  return <div className="md-content">{rendered}</div>;
}

/** inline 解析：**粗體**、*斜體* */
function inlineParse(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  // 用 regex 匹配 **bold** 和 *italic*
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    // 前面的純文字
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[2]) {
      // **bold**
      parts.push(<strong key={key++}>{match[2]}</strong>);
    } else if (match[3]) {
      // *italic*
      parts.push(<em key={key++}>{match[3]}</em>);
    }
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length ? parts : [text];
}
'''

# =============================================
# 2. AI Loading Skeleton 元件
# =============================================
ai_loading_tsx = r'''import React from "react";

/**
 * AI 生成中骨架動畫
 */
export default function AILoadingSkeleton() {
  return (
    <div className="ai-loading-skeleton">
      <div className="ai-loading-header">
        <div className="ai-loading-dot-container">
          <span className="ai-loading-dot"></span>
          <span className="ai-loading-dot"></span>
          <span className="ai-loading-dot"></span>
        </div>
        <span className="ai-loading-label">AI 正在分析資料並生成洞察...</span>
      </div>
      <div className="ai-loading-lines">
        <div className="shimmer-line" style={{width: "92%"}}></div>
        <div className="shimmer-line" style={{width: "78%"}}></div>
        <div className="shimmer-line" style={{width: "85%"}}></div>
        <div className="shimmer-line" style={{width: "60%"}}></div>
      </div>
    </div>
  );
}
'''

# =============================================
# 3. CSS — AI Loading + Markdown 
# =============================================
ai_css_additions = r'''

/* === AI Loading Skeleton === */
.ai-loading-skeleton { padding: 20px; }
.ai-loading-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.ai-loading-dot-container { display: flex; gap: 4px; }
.ai-loading-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--primary); opacity: 0.5;
  animation: aiDotBounce 1.4s ease-in-out infinite;
}
.ai-loading-dot:nth-child(2) { animation-delay: 0.2s; }
.ai-loading-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes aiDotBounce {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1.2); }
}
.ai-loading-label { font-size: 13px; color: var(--primary); font-weight: 500; }
.ai-loading-lines { display: flex; flex-direction: column; gap: 10px; }
.shimmer-line {
  height: 14px; border-radius: 6px;
  background: linear-gradient(90deg, var(--primary-light) 25%, #EEF2FF 50%, var(--primary-light) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* === Markdown Content === */
.md-content { font-size: 14px; line-height: 1.75; color: var(--text); }
.md-content .md-p { margin-bottom: 8px; }
.md-content .md-p:last-child { margin-bottom: 0; }
.md-content .md-list { margin: 4px 0 8px 0; padding-left: 20px; }
.md-content .md-list li { margin-bottom: 6px; line-height: 1.6; }
.md-content .md-list li::marker { color: var(--primary); }
.md-content strong { font-weight: 600; color: var(--text); }
.md-content em { font-style: italic; color: var(--text-2); }
'''

# =============================================
# 4. 修改三個頁面
# =============================================
app_data = api("GET", f"/builder/apps/{APP}", None, token)
pvfs = app_data.get("published_vfs", {})

# --- DashboardPage ---
dash = pvfs.get("src/pages/DashboardPage.tsx", "")
# Add imports
if "MarkdownText" not in dash:
    dash = dash.replace(
        'import { runAction }',
        'import { runAction }'
    )
    # 在檔案最前面加入 import
    dash = ('import MarkdownText from "../components/MarkdownText";\n'
            'import AILoadingSkeleton from "../components/AILoadingSkeleton";\n'
            + dash)

# Replace AI rendering area
# Old: {aiInsight ? (<div className="ai-reason-box">...<div className="ai-reason-text">{aiInsight}</div>...
# 找到 AI 洞察的渲染區域並替換
old_dash_ai = '{aiInsight ? (\n      <div className="ai-reason-box">\n        <div className="ai-icon">AI</div>\n        <div className="ai-reason-content"><div className="ai-reason-label">AI {"\u4e3b\u7ba1\u6d1e\u5bdf"}</div><div className="ai-reason-text">{aiInsight}</div></div>\n      </div>\n    ) : !aiLoading ? (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>{"\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf"}</p>) : null}'

new_dash_ai = '{aiLoading ? (\n      <AILoadingSkeleton />\n    ) : aiInsight ? (\n      <div className="ai-reason-box">\n        <div className="ai-icon">AI</div>\n        <div className="ai-reason-content"><div className="ai-reason-label">AI {"\u4e3b\u7ba1\u6d1e\u5bdf"}</div><MarkdownText text={aiInsight} /></div>\n      </div>\n    ) : (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>{"\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf"}</p>)}'

if old_dash_ai in dash:
    dash = dash.replace(old_dash_ai, new_dash_ai)
    print("Dashboard: replaced AI render OK")
else:
    print("Dashboard: AI render pattern NOT found, trying flexible replacement")
    # 更靈活的替換
    # 搜索 aiInsight ? ( 到 : null}
    import re
    pattern = r'\{aiInsight \? \(.+?ai-reason-text.+?\{aiInsight\}.+?\) : !aiLoading \? \(.+?\) : null\}'
    match = re.search(pattern, dash, re.DOTALL)
    if match:
        dash = dash[:match.start()] + new_dash_ai + dash[match.end():]
        print("Dashboard: flexible replacement OK")
    else:
        print("Dashboard: COULD NOT REPLACE - manual check needed")
        # Print context around aiInsight
        idx = dash.find("aiInsight ?")
        if idx >= 0:
            print("  Context: %s" % repr(dash[idx:idx+300]))

# --- SalesPage ---
sales = pvfs.get("src/pages/SalesPage.tsx", "")
if "MarkdownText" not in sales:
    sales = ('import MarkdownText from "../components/MarkdownText";\n'
             'import AILoadingSkeleton from "../components/AILoadingSkeleton";\n'
             + sales)

# Replace AI area in SalesPage
old_sales_ai = '{aiInsight ? (<div className="ai-reason-box"><div className="ai-icon">AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI \u696d\u52d9\u5206\u6790</div><div className="ai-reason-text">{aiInsight}</div></div></div>\n    ) : !aiLoading ? (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf</p>) : null}'

new_sales_ai = '{aiLoading ? (\n      <AILoadingSkeleton />\n    ) : aiInsight ? (<div className="ai-reason-box"><div className="ai-icon">AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI \u696d\u52d9\u5206\u6790</div><MarkdownText text={aiInsight} /></div></div>\n    ) : (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf</p>)}'

if old_sales_ai in sales:
    sales = sales.replace(old_sales_ai, new_sales_ai)
    print("Sales: replaced AI render OK")
else:
    print("Sales: trying flexible replacement")
    match = re.search(r'\{aiInsight \? \(.+?ai-reason-text.+?\{aiInsight\}.+?\) : !aiLoading \? \(.+?\) : null\}', sales, re.DOTALL)
    if match:
        sales = sales[:match.start()] + new_sales_ai + sales[match.end():]
        print("Sales: flexible replacement OK")
    else:
        print("Sales: COULD NOT REPLACE")
        idx = sales.find("aiInsight ?")
        if idx >= 0: print("  Context: %s" % repr(sales[idx:idx+300]))

# --- CategoriesPage ---
cats = pvfs.get("src/pages/CategoriesPage.tsx", "")
if "MarkdownText" not in cats:
    cats = ('import MarkdownText from "../components/MarkdownText";\n'
            'import AILoadingSkeleton from "../components/AILoadingSkeleton";\n'
            + cats)

old_cats_ai = '{aiInsight ? (<div className="ai-reason-box"><div className="ai-icon">AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI \u985e\u5225\u6d1e\u5bdf</div><div className="ai-reason-text">{aiInsight}</div></div></div>\n      ) : !aiLoading ? (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf</p>) : null}'

new_cats_ai = '{aiLoading ? (\n        <AILoadingSkeleton />\n      ) : aiInsight ? (<div className="ai-reason-box"><div className="ai-icon">AI</div><div className="ai-reason-content"><div className="ai-reason-label">AI \u985e\u5225\u6d1e\u5bdf</div><MarkdownText text={aiInsight} /></div></div>\n      ) : (<p style={{color:"var(--text-3)",fontSize:13,textAlign:"center",padding:16}}>\u9ede\u64ca\u4e0a\u65b9\u6309\u9215\u7522\u751f AI \u6d1e\u5bdf</p>)}'

if old_cats_ai in cats:
    cats = cats.replace(old_cats_ai, new_cats_ai)
    print("Categories: replaced AI render OK")
else:
    print("Categories: trying flexible replacement")
    match = re.search(r'\{aiInsight \? \(.+?ai-reason-text.+?\{aiInsight\}.+?\) : !aiLoading \? \(.+?\) : null\}', cats, re.DOTALL)
    if match:
        cats = cats[:match.start()] + new_cats_ai + cats[match.end():]
        print("Categories: flexible replacement OK")
    else:
        print("Categories: COULD NOT REPLACE")
        idx = cats.find("aiInsight ?")
        if idx >= 0: print("  Context: %s" % repr(cats[idx:idx+300]))

# =============================================
# 5. Append CSS
# =============================================
css = pvfs.get("src/App.css", "")
if "ai-loading-skeleton" not in css:
    css += ai_css_additions
    print("CSS: appended AI loading + markdown styles")
else:
    print("CSS: already has AI loading styles")

# =============================================
# 6. Upload all files
# =============================================
files = {
    "src/components/MarkdownText.tsx": markdown_tsx,
    "src/components/AILoadingSkeleton.tsx": ai_loading_tsx,
    "src/pages/DashboardPage.tsx": dash,
    "src/pages/SalesPage.tsx": sales,
    "src/pages/CategoriesPage.tsx": cats,
    "src/App.css": css,
}

print("\n=== Upload %d files ===" % len(files))
for f in sorted(files):
    print("  %s (%d chars)" % (f, len(files[f])))

r = api("PATCH", f"/builder/apps/{APP}/source/files", {"files": files}, token)
print("Upload:", "OK" if r and "_error" not in r else "FAIL: " + str(r))

# Publish
print("\n=== Publish ===")
r = api("POST", f"/builder/apps/{APP}/publish", {
    "published_assets": {"html": "", "bundle_js": "", "css": ""}
}, token)
print("Publish:", "OK" if r and "_error" not in r else "FAIL")

# Compile check
time.sleep(1)
print("\n=== Compile check ===")
c = api("POST", f"/compile/compile/{SLUG}", None, token)
print("Success:", c.get("success"))
for e in c.get("compile_errors", []):
    print("  ERROR:", json.dumps(e, ensure_ascii=False)[:200])

# Verify
time.sleep(1)
app2 = api("GET", f"/builder/apps/{APP}", None, token)
pvfs2 = app2.get("published_vfs", {})
print("\n=== Verify ===")
print("MarkdownText.tsx:", len(pvfs2.get("src/components/MarkdownText.tsx", "")), "chars")
print("AILoadingSkeleton.tsx:", len(pvfs2.get("src/components/AILoadingSkeleton.tsx", "")), "chars")
print("Dashboard has MarkdownText:", "MarkdownText" in pvfs2.get("src/pages/DashboardPage.tsx", ""))
print("Dashboard has AILoadingSkeleton:", "AILoadingSkeleton" in pvfs2.get("src/pages/DashboardPage.tsx", ""))
print("Sales has MarkdownText:", "MarkdownText" in pvfs2.get("src/pages/SalesPage.tsx", ""))
print("Categories has MarkdownText:", "MarkdownText" in pvfs2.get("src/pages/CategoriesPage.tsx", ""))
print("CSS has shimmer:", "shimmer" in pvfs2.get("src/App.css", ""))
print("CSS has md-content:", "md-content" in pvfs2.get("src/App.css", ""))

print("\n===== DONE =====")
