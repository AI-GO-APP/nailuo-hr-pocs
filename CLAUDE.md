# AI GO Custom App 開發規範（本專案強制約束）

> ⚠️ **本檔案為 AI 助手自動載入的強制規範。**
> 所有針對本專案的 AI GO Custom App 開發修改，必須遵守以下規則。
> 完整踩坑紀錄請見 [docs/ai-go-custom-app-pitfalls.md](./docs/ai-go-custom-app-pitfalls.md)

---

## 開發前必讀

- **平台官方文件**：https://www.ai-go.app/zh-TW/docs/custom-app-dev
- **Reference App**（已正確運作的 HR 應用）：`dbe4f2a4-5bb9-4dfb-a836-130d52197656`
- 遇到不確定的做法時，**先讀文件、再看 reference app**，絕對不要靠猜測。

---

## 絕對禁止事項

1. **禁止使用 `BrowserRouter`** — Shadow DOM 中必須用 `HashRouter`
2. **禁止在 CSS 中只用 `:root {}`** — 必須用 `:host, :root {}` 雙選擇器
3. **禁止使用 `confirm()` / `alert()` / `prompt()`** — Shadow DOM 中會靜默失敗，改用 React 元件
4. **禁止在前端直接呼叫外部 LLM API** — AI 邏輯必須放在 `actions/*.py` 的 Server-Side Action
5. **禁止使用 `ctx.env`** — 它是 `str("online")`，不是 dict
6. **禁止用 `ctx.secrets.get("KEY", "default")` 雙參數** — 只接受 `ctx.secrets.get("KEY")` 單參數
7. **禁止自建 Custom Table 來替代 Proxy Table 的寫入** — 正確做法是修復 Data Reference 欄位

---

## SDK 使用規則

```
api.ts  →  submitRecord / listRecords  →  Custom Table（你自己建的表）  →  /data/objects/
db.ts   →  insert / query / update     →  Proxy Table（SaaS 既有表）    →  /proxy/{appId}/
```

- `hr_leaves`, `hr_employees`, `hr_leave_types` 等 → **一律用 `db.ts`**
- `chat_messages`, `attendance_records` 等自建表 → **一律用 `api.ts`**
- **永遠不要混用。**

### db.ts insert() 的已知 Bug

`db.ts` 的 `insert()` 可能沒有用 `{"data": {...}}` 包裝 payload，導致 proxy 端回傳 400。
若 `insert()` 失敗，改用直接 `fetch`：

```typescript
async function proxyInsert(table: string, data: Record<string, any>) {
  const apiBase = (window as any).__API_BASE__ || "/api/v1";
  const appId = (window as any).__APP_ID__ || "";
  const tkn = (window as any).__APP_TOKEN__ || "";
  const resp = await fetch(`${apiBase}/proxy/${appId}/${table}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(tkn ? { Authorization: `Bearer ${tkn}` } : {}),
    },
    credentials: "include",
    body: JSON.stringify({ data }),
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `Proxy Error (${resp.status})`);
  }
  return resp.json();
}
```

---

## Shadow DOM 規範

- CSS 變數：`:host, :root { --var: value; }`
- Layout 根容器：`height: 100vh; overflow-y: auto;`
- 路由：`HashRouter`（多頁面）或直接渲染（單頁面）
- 詳見文件第 11 章

---

## Data Reference（Proxy 欄位白名單）

- 查看引用：`GET /api/v1/refs/apps/{appId}`
- 修改引用：`PATCH /api/v1/refs/{refId}` + `{"columns": [...], "permissions": [...]}`
- 修改後必須 `POST /api/v1/builder/apps/{appId}/publish` 發布才生效
- **新增 proxy table 欄位前，務必確認該欄位在 Reference 的 columns 白名單中**

### 本 App 的 hr_leaves 必要欄位

```json
["id", "name", "state", "holiday_type", "date_from", "date_to",
 "number_of_days", "duration_display", "notes", "employee_id",
 "holiday_status_id", "manager_id", "department_id", "tenant_id",
 "created_at", "updated_at", "custom_data"]
```

---

## 日期格式

- 寫入 proxy table 時，日期使用**純字串不帶時區**：`"2026-06-20T09:00:00"`
- **禁止使用 `new Date().toISOString()`**（會產生 `Z` 時區後綴，DB 拒絕）
- 正確做法：`pl.date_from + "T09:00:00"`

---

## Server-Side Action 規範

- 函式簽章：`def execute(ctx):`
- 可用的 ctx 方法（**僅限以下**）：
  - `ctx.params` — 前端參數
  - `ctx.db.query(table, **kwargs)` / `ctx.db.insert(table, data)` — DB 操作
  - `ctx.secrets.get(key)` — 取得金鑰（**單參數**）
  - `ctx.response.json(data)` — 回傳 JSON
  - `ctx.http.call(service, endpoint)` — 外部 API
  - `ctx.crypto.hash(alg, data)` — 雜湊
  - `ctx.csv.export(rows)` — CSV 匯出
- **不要使用 `ctx.env`**（是 string 不是 dict）
- 白名單模組：json, math, re, datetime, httpx 等

---

## React 注意事項

- async callback 中讀取最新 state → **使用 `useRef` 同步追蹤**
- 不依賴 `confirm()` → 使用 React state 二階段確認
- Runtime 提供的模組（不需安裝）：`react`, `react-dom`, `lucide-react`, `react-router-dom`, `react-hot-toast`

---

## 開發循環

```
1. PATCH 修改 VFS 檔案
2. POST 編譯（dev=true）→ 檢查 success
3. 編譯失敗 → 修改 → 回到 1
4. 編譯成功 → E2E 測試腳本驗證
5. 測試通過 → POST 發布
6. 請用戶測試
```

**絕對不要跳過步驟 4 直接請用戶測試。**
