---
name: ai-go-custom-app
description: AI GO Custom App 開發規範。在開發或修改任何 AI GO Custom App 時必須遵守此規範，避免已知陷阱。涵蓋 Shadow DOM CSS、VFS 部署流程、API 架構、前端限制等關鍵規則。
---

# AI GO Custom App 開發規範

> **適用範圍**：所有透過 AI GO 平台 (`ai-go.app`) Builder API 開發的 Custom App
> **最後更新**：2026-05-31
> **平台文件**：https://www.ai-go.app/zh-TW/docs/custom-app-dev

---

## 最高優先規則（違反必出問題）

### 規則 1：CSS 必須使用 `:host, :root` 宣告變數

Custom App 在 **Shadow DOM** 中執行。`:root` 匹配的是外層 `<html>`，無法穿透 Shadow 邊界。

```css
/* ✅ 正確 — Shadow DOM 和獨立頁面都能生效 */
:host, :root {
  --primary: #2563EB;
  --text: #0F172A;
}

/* ❌ 錯誤 — 變數在 Shadow DOM 中不生效，所有 var() 引用都會失敗 */
:root {
  --primary: #2563EB;
}
```

**後果**：如果只用 `:root`，所有 CSS 變數（顏色、間距、圓角等）都會失效，整個 UI 回到瀏覽器預設樣式。JS/TSX 元件正常運作但視覺完全崩壞。

---

### 規則 2：部署方式 — `published_vfs` 是唯一真相

平台從 `published_vfs`（VFS 原始碼）即時編譯並服務前端，**不使用** `published_assets`。

#### ✅ 正確部署流程

```
1. PATCH /builder/apps/{APP}/source/files  → 上傳修改的檔案到 vfs_state
2. POST  /builder/apps/{APP}/publish       → 同步 vfs_state → published_vfs
   payload: { "published_assets": {"html":"", "bundle_js":"", "css":""} }
3. GET   /builder/apps/{APP}               → 驗證 published_vfs 已更新
```

#### ❌ 常見錯誤

```
# 錯誤1：把 compile 結果塞進 published_assets → 平台不讀這些
POST /builder/apps/{APP}/publish
{ "published_assets": {"html": "...", "bundle_js": "...", "css": "..."} }

# 錯誤2：只 compile 不 publish → published_vfs 不會更新
POST /compile/compile/{SLUG}
# 即使成功，前端也不會變，因為 published_vfs 沒有同步
```

#### 驗證方法

```python
# 每次部署後必做的 GET 驗證
app = api("GET", f"/builder/apps/{APP}", None, token)
pvfs = app["published_vfs"]
# 確認目標檔案的內容已更新
assert "你的新程式碼片段" in pvfs["src/App.css"]
```

**關鍵記憶**：成功的 app 的 `published_assets` 全部為空字串（html=0, css=0, bundle_js=0）。平台自行從 `published_vfs` 編譯服務。

---

### 規則 3：路由必須用 `HashRouter`

Shadow DOM 環境下 `BrowserRouter` 無法運作。

```tsx
/* ✅ */
import { HashRouter } from "react-router-dom";
<HashRouter><Routes>...</Routes></HashRouter>

/* ❌ */
import { BrowserRouter } from "react-router-dom";
```

---

### 規則 4：AI/LLM 邏輯必須在 Action（後端）

```
✅ 前端 → callAction("analyze", params) → actions/analyze.py (ctx.secrets.get("OPENAI_API_KEY"))
❌ 前端直接呼叫 OpenAI API
```

---

### 規則 5：Action 沙盒禁止模組 — 必須用 `httpx`

平台 Action 執行在安全沙盒中，**禁止匯入 `ssl`、`os` 等模組**。呼叫外部 API 必須使用 `httpx`（平台預裝）。

```python
# ✅ 正確 — 使用 httpx
import httpx

def _call_ai(ctx, prompt):
    api_key = ctx.secrets.get("OPENAI_API_KEY")
    if not api_key:
        return "- AI 金鑰未設定"
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]},
        timeout=30,
    )
    return resp.json()["choices"][0]["message"]["content"].strip()

# ❌ 錯誤 — ssl 被禁止，會直接報錯「禁止匯入模組: ssl」
import urllib.request
import ssl  # ← 平台會拒絕執行
ssl._create_default_https_context = ssl._create_unverified_context
```

**已知被禁止的模組**：`ssl`、`os`（部分功能）、`subprocess`
**平台預裝可用的模組**：`httpx`、`json`、`re`、`collections`

---

## CSS 規範

### Shadow DOM 限制

1. **`:host, :root`** — 所有 CSS 變數必須用此宣告
2. **避免 `overflow: hidden`** — Shadow DOM 容器需要正確的滾動設定：
   ```css
   /* ✅ 允許滾動 */
   html, body, #root { height: 100%; }

   /* ❌ 整個頁面無法滾動 */
   html, body, #root { height: 100%; overflow: hidden; }
   ```
3. **`confirm()` / `alert()` 不可用** — 用 React state 實作確認對話框
4. **字體建議**：使用 `-apple-system, BlinkMacSystemFont, "PingFang TC", "Microsoft JhengHei", "Noto Sans TC", sans-serif`

### CSS 變數命名慣例（參考成功 app）

```css
:host, :root {
  --primary: #2563EB;
  --primary-dark: #1D4ED8;
  --primary-light: #DBEAFE;
  --danger: #DC2626;
  --danger-light: #FEE2E2;
  --warning: #EA580C;
  --success: #16A34A;
  --text: #0F172A;
  --text-2: #475569;      /* 或 --text-secondary */
  --text-3: #94A3B8;      /* 或 --text-muted */
  --border: #E2E8F0;
  --bg: #F8FAFC;
  --bg-card: #FFFFFF;
  --radius: 12px;
}
```

---

## API 架構

### 兩套 SDK 不可混用

| SDK | 函式 | 操作對象 | API 路徑 |
|-----|------|---------|---------|
| `api.ts` | `submitRecord()` | Custom Table（自建表） | `/data/objects/` |
| `db.ts` | `insert()` / `query()` | Proxy Table（SaaS 既有表） | `/proxy/{appId}/` |

### Action 的 `ctx` 物件可用屬性

| 屬性 | 用途 | 注意 |
|------|------|------|
| `ctx.params` | 前端傳入的參數（dict） | `.get("key", "default")` 支援雙參數 |
| `ctx.db.query()` / `ctx.db.insert()` | DB 操作 | — |
| `ctx.secrets.get(key)` | 取金鑰 | **只支援單參數**，不支援 default |
| `ctx.response.json(data)` | 回傳 JSON | — |
| `ctx.http.call()` | 外部 HTTP 請求 | — |
| ~~`ctx.env`~~ | **不可用** | 是字串 `"online"`，不是 dict |
| ~~`import ssl`~~ | **被禁止** | 使用 `httpx` 取代 |
| ~~`import os`~~ | **被禁止** | `os.environ` 不可用，用 `ctx.secrets` |

### Reference API

| 操作 | 方法 | 路徑 |
|------|------|------|
| 列出 App 的所有引用 | GET | `/api/v1/refs/apps/{appId}` |
| 修改引用欄位/權限 | PATCH | `/api/v1/refs/{refId}` |
| 建立新引用 | POST | `/api/v1/refs/apps/{appId}` |

**注意**：Proxy POST 會根據 Reference 的 `columns` 白名單過濾欄位。如果 INSERT 失敗（如 NOT NULL violation），先檢查 Reference 設定。

---

## VFS 檔案結構（標準 React Custom App）

```
_template_meta.json          # 模板中繼資料
package.json                 # 依賴宣告
actions/
  manifest.json              # Action 清單
  analyze_churn.py           # 後端 Action
src/
  main.tsx                   # 入口點（import "./App.css"）
  App.tsx                    # 路由設定（HashRouter）
  App.css                    # 全域樣式（:host, :root）
  action.ts                  # runAction SDK
  api.ts                     # Custom Table SDK
  db.ts                      # Proxy Table SDK
  routes.ts                  # 路由定義
  components/
    AppLayout.tsx             # 主版面配置
    AppSidebar.tsx            # 側邊欄
  pages/
    DashboardPage.tsx         # 頁面元件
    _manifest.json            # 頁面清單
```

### main.tsx 標準寫法

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./App.css";

const rootEl = (window as any).__CUSTOM_APP_ROOT__ || document.getElementById("root");
ReactDOM.createRoot(rootEl!).render(
  <React.StrictMode><App /></React.StrictMode>
);
```

---

## Compile API（僅供驗證）

```
POST /compile/compile/{SLUG}
```

- 用來**驗證語法錯誤**，不用來部署
- 返回 `success`、`compile_errors`、`html`、`bundle_js`、`css`
- **重要**：compile 使用的是 `published_vfs`，不是 `vfs_state`
- 所以必須先 publish（同步 VFS）再 compile

---

## 開發 Checklist

### 每次修改前
- [ ] 確認 CSS 使用 `:host, :root`（不是 `:root`）
- [ ] 確認路由使用 `HashRouter`
- [ ] 確認 AI 邏輯在 Action 中（不在前端）
- [ ] 確認 Action 中使用 `httpx`（不是 `urllib.request + ssl`）
- [ ] 確認 Action 中使用 `ctx.secrets.get()`（不是 `os.environ`）

### 每次部署後
- [ ] `GET /builder/apps/{APP}` 驗證 `published_vfs` 已更新
- [ ] 確認 `published_assets` 為空（html=0, css=0, bundle_js=0）
- [ ] 可選：`POST /compile/compile/{SLUG}` 驗證無編譯錯誤
- [ ] 瀏覽器 Ctrl+Shift+R 強制重整確認

### 遇到問題時
1. **先看成功的 reference app**（`GET /builder/apps/{REF_APP}`）
2. **先讀平台文件**（第 3、7、8、11、13 章）
3. **不要臆斷平台行為** — 實測確認
