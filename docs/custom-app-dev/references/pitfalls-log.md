# AI GO Custom App 開發踩坑全紀錄

> **專案**：耐落員工人資假勤（`da7789b4-59bc-422c-8e7b-b6a7b9103146`）
> **記錄日期**：2026-05-31
> **平台文件**：https://www.ai-go.app/zh-TW/docs/custom-app-dev

---

## 總覽

本次開發共踩 **14 個坑**，依時間序排列。

- ⚠️ = **查文件即可避免**（開發者自身怠惰）
- 🔍 = **需實測平台行為才能發現**（文件未涵蓋或有歧義）

| # | 問題 | 類型 | 浪費時間 |
|---|------|------|---------|
| 1 | CSS `:root` 在 Shadow DOM 失效 | ⚠️ | 中 |
| 2 | 頁面無法捲動 | ⚠️ | 低 |
| 3 | `BrowserRouter` 路由失效 | ⚠️ | 低 |
| 4 | AI 邏輯放前端而非 Action | ⚠️ | 高 |
| 5 | `ctx.secrets.get()` 雙參數崩潰 | 🔍 | 中 |
| 6 | `ctx.env` 當 dict 使用崩潰 | 🔍 | 高 |
| 7 | `confirm()` 靜默失敗 | ⚠️ | 低 |
| 8 | React 閉包導致上下文遺失 | ⚠️ | 中 |
| 9 | Action 端手動管理 Token 打 proxy | ⚠️ | 高 |
| 10 | `submitRecord("hr_leaves")` → 404 | ⚠️ | 高 |
| 11 | 自建 `leave_requests` table 被否決 | ⚠️ | 中 |
| 12 | Proxy POST 欄位被 Reference 過濾 | 🔍 | 高 |
| 13 | 盲猜 Reference API 路徑 | ⚠️ | 高 |
| 14 | `toISOString()` 日期帶時區被 DB 拒絕 | 🔍 | 低 |

> **統計**：14 個坑中 **10 個 (71%) 是查文件就能避免的**。

---

## 坑 1 — CSS `:root` 在 Shadow DOM 中無效 ⚠️

### 現象
所有 CSS 變數在部署後失效，本地預覽正常。

### 根因
Custom App Runtime 在 Shadow DOM 中執行。`:root` 匹配的是 `<html>`，無法穿透 Shadow 邊界。

### 文件位置
第 11 章「Shadow DOM 與 CSS 樣式規範」

### 正確做法
```css
/* ✅ */
:host, :root { --primary: #2563eb; }

/* ❌ */
:root { --primary: #2563eb; }
```

---

## 坑 2 — 頁面無法捲動 ⚠️

### 現象
內容超出畫面高度時無法向下滾動。

### 根因
Shadow DOM 容器預設不具備捲動能力。

### 文件位置
第 11 章「容器滾動限制」

### 正確做法
```tsx
// AppLayout 最外層
<div style={{ height: "100vh", overflowY: "auto" }}>
```

---

## 坑 3 — `BrowserRouter` 路由失效 ⚠️

### 現象
頁面切換無反應。

### 文件位置
第 3 章核心規則第 1 點

### 正確做法
多頁面用 `HashRouter`，單頁面不用 Router。

---

## 坑 4 — AI 邏輯放在前端 ⚠️

### 現象
用戶指出「AI 回應一定是在 action 呼叫，不能在前端」。

### 根因
沒有先看 reference app（`ca778499`）就直接在前端呼叫 OpenAI API。

### 正確做法
- AI/LLM 邏輯寫在 `actions/*.py`
- 前端透過 `callAction("action_name", params)` 呼叫
- Action 中用 `ctx.secrets.get("OPENAI_API_KEY")` 取金鑰

### 教訓
> **先研究 reference app 的架構再動手。**

---

## 坑 5 — `ctx.secrets.get("KEY", "default")` 崩潰 🔍

### 現象
Action 執行時 `TypeError`。

### 根因
文件第 8 章寫 `ctx.params.get("key", "default")` 有兩個參數，所以以為 `ctx.secrets.get()` 也支援。但 **`ctx.secrets.get()` 僅接受單參數**。

### 正確做法
```python
key = ctx.secrets.get("OPENAI_API_KEY") or ""
```

---

## 坑 6 — `ctx.env.get()` 崩潰：`'str' object has no attribute 'get'` 🔍

### 現象
Action 中呼叫 `ctx.env.get("SOME_KEY")` 直接崩潰。

### 根因
`ctx.env` 在平台中是字串 `"online"`，不是 dict。文件中**未記載** `ctx.env` 的型別。

### 正確做法
**不要使用 `ctx.env`。** 只使用文件第 8 章列出的 ctx 屬性。

### 可用的 ctx 屬性（完整清單）
| 屬性 | 用途 |
|------|------|
| `ctx.params` | 前端傳入的參數 |
| `ctx.db.query()` / `ctx.db.insert()` | DB 操作 |
| `ctx.secrets.get(key)` | 金鑰（單參數） |
| `ctx.response.json(data)` | 回傳 JSON |
| `ctx.http.call()` | 外部 API |
| `ctx.crypto.hash()` | 雜湊 |
| `ctx.csv.export()` | CSV 匯出 |

---

## 坑 7 — `confirm()` 靜默失敗 ⚠️

### 文件位置
第 11 章「JavaScript API 限制」

### 正確做法
用 React state 二階段確認 (`ConfirmDialog` 元件)。

---

## 坑 8 — React 閉包導致對話上下文遺失 ⚠️

### 現象
AI 每次回應都像是第一次對話。

### 根因
`handleSend` 中的 `messages` state 在 async callback 被閉包捕獲為舊值。

### 正確做法
```tsx
const messagesRef = useRef<ChatMessage[]>([]);
messagesRef.current = messages; // 每次 render 同步

// 在 async callback 中
const allMsgs = [...messagesRef.current, userMsg];
```

---

## 坑 9 — Action 端手動管理 Token 打 Proxy ⚠️

### 現象
嘗試在 `execute_action.py` 中透過 `ctx.env` 取 Token 打 proxy API 寫入。

### 用戶原話
> 「如果引用已經建立好並發布，你應該不用設定任何 token 也能打 proxy？」

### 正確做法
- **Action 端**：`ctx.db.insert("hr_leaves", data)` 直接寫入
- **前端**：`db.ts` SDK 會自動從 `window.__APP_TOKEN__` 注入認證
- **永遠不要手動管理 Token**

---

## 坑 10 — `submitRecord("hr_leaves")` → 404 ⚠️

### 現象
前端呼叫 `submitRecord("hr_leaves", data)` 回傳 404。

### 根因
文件第 7 章明確區分兩套 SDK：

| SDK | 函式 | 操作對象 | API 路徑 |
|-----|------|---------|---------|
| `api.ts` | `submitRecord` | Custom Table（自建表） | `/data/objects/` |
| `db.ts` | `insert` | Proxy Table（SaaS 既有表） | `/proxy/{appId}/` |

`hr_leaves` 是 proxy table → 必須用 `db.ts` 的 `insert`。

---

## 坑 11 — 自建 `leave_requests` table 被否決 ⚠️

### 現象
因為 proxy POST 失敗，決定另建 custom table 來儲存假單。

### 用戶原話
> 「custom data table leave_requests 是不被允許的。自訂應用 dbe4f2a4 應有正確建立請假紀錄的方法。」

### 教訓
> **遇到問題先看 reference app 怎麼做**，不要自己發明新架構。

---

## 坑 12 — Proxy POST 欄位被 Data Reference 過濾 🔍

### 現象
同樣的 POST body，REF app (`dbe4f2a4`) 成功，MY app (`da7789b4`) 失敗。
SQL 顯示 `holiday_status_id = null`（NOT NULL violation）。

### 根因
MY app 的 Data Reference（`GET /api/v1/refs/apps/{appId}`）中 `columns` 列表**沒有 `holiday_status_id`**。
Proxy 層會自動過濾不在白名單中的欄位。

### 診斷方法
```bash
# 比較兩個 app 的引用欄位
GET /api/v1/refs/apps/{REF_APP}  → columns 有 holiday_status_id ✅
GET /api/v1/refs/apps/{MY_APP}   → columns 沒有 holiday_status_id ❌
```

### 修正方法
```bash
PATCH /api/v1/refs/{refId}
{"columns": ["id","name","state","holiday_type","date_from","date_to",
 "number_of_days","duration_display","notes","employee_id",
 "holiday_status_id","manager_id","department_id","tenant_id",
 "created_at","updated_at","custom_data"],
 "permissions": ["create","read","update"]}
```
修改後必須 `POST .../publish` 才會生效。

---

## 坑 13 — 盲猜 Reference API 路徑 ⚠️

### 現象
花了大量時間暴力窮舉 `/proxy/references`, `/builder/apps/{id}/references`, `/proxy/config` 等路徑，全部 404。

### 根因
文件第 13 章備註提到「此功能等同於 Reference 的 API 建立方式（`/refs/apps/{id}`）」。**但開發者沒有先讀文件。**

### 用戶原話
> 「絕對可以不透過網頁介面，一定有辦法透過連線來完成引用的所有設定，你必須從我給你的連線文件來找。」

### Reference API 完整清單
| 操作 | 方法 | 路徑 |
|------|------|------|
| 列出 App 的所有引用 | GET | `/api/v1/refs/apps/{appId}` |
| 修改引用欄位/權限 | PATCH | `/api/v1/refs/{refId}` |
| 建立新引用 | POST | `/api/v1/refs/apps/{appId}` |

---

## 坑 14 — `toISOString()` 日期帶時區被 DB 拒絕 🔍

### 現象
```
can't subtract offset-naive and offset-aware datetimes
```

### 根因
`new Date("2026-06-20T09:00:00").toISOString()` → `"2026-06-20T01:00:00.000Z"`
DB 的 `date_from` 是 naive datetime，不接受帶 `Z` 的值。

### 正確做法
```typescript
// ✅ 純字串不帶時區
date_from: pl.date_from + "T09:00:00"

// ❌ 會帶時區
date_from: new Date(pl.date_from + "T09:00:00").toISOString()
```

---

## 系統性防範策略

### 1. 開發前必讀文件章節
- 第 3 章（核心規則）
- 第 7 章（`api.ts` vs `db.ts` 差異）
- 第 8 章（`ctx` 物件的可用方法清單）
- 第 11 章（Shadow DOM 全部限制）
- 第 13 章（Custom Table / Reference API）

### 2. 先看 Reference App
遇到「怎麼做 X」時，第一步 `GET /builder/apps/{REF_APP}` 讀已成功運作的 app 原始碼。

### 3. 先測試再部署
每次修改後，先跑 `e2e_test.py` + proxy POST 驗證，確認無誤才請用戶測試。

### 4. 不要臆斷平台行為
`ctx.env` 的型別、`ctx.secrets.get()` 的參數數量、proxy 欄位白名單、DB 日期格式 — 都必須實測確認。

### 5. 區分兩套 SDK
```
api.ts (submitRecord)  → Custom Table  → /data/objects/
db.ts  (insert)        → Proxy Table   → /proxy/{appId}/
```
