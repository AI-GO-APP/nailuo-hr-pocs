# AI GO Custom App 開發踩坑全紀錄

> **專案**：耐落員工人資假勤（`da7789b4-59bc-422c-8e7b-b6a7b9103146`）
> **記錄日期**：2026-05-31
> **平台文件**：https://www.ai-go.app/zh-TW/docs/custom-app-dev

---

## 總覽

歷次開發共踩 **19 個坑**，依時間序排列。

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
| 15 | `runAction()` 回傳 `{ data, file }` 未解包 | 🔍 | 高 |
| 16 | React Hooks 放在 early return 之後導致白屏 | ⚠️ | 高 |
| 17 | Dropdown `onClick` 被 `mousedown` 外部偵測搶先 | 🔍 | 中 |
| 18 | CSS `min-height` 導致 `overflow` 永遠不觸發 | ⚠️ | 中 |
| 19 | VFS 字串替換殘留舊函數片段致編譯錯誤 | ⚠️ | 中 |

> **統計**：19 個坑中 **13 個 (68%) 是查文件或遵守基本規則就能避免的**。

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

### 6. `runAction` 回傳必須解包
前端所有 `runAction` 結果都用 `const d = r?.data || r;` 再存取。

### 7. VFS 替換後必驗證
替換完立即檢查：函數只出現 1 次、無殘留語法碎片、compile 無錯誤。

---

## 坑 15 — `runAction()` 回傳 `{ data, file }` 而非直接結果 🔍

### 現象
前端呼叫 `runAction("sales_log", { action: "list_logs" })` 後，
`r.logs` 永遠是 `undefined`，HistoryPage / CustomersPage / LogInputPage 全部資料為空。

### 根因
`action.ts` 的 `runAction()` 回傳：
```javascript
return {
  data: result.result || result.data || result,
  file: result.file || undefined,
};
```
`r` = `{ data: { logs: [...] }, file: undefined }`，正確取法是 `r.data.logs`。

### 正確做法
```javascript
// ✅
const d = r?.data || r;
if (d?.logs) setLogs(d.logs);

// ❌ r.logs 不存在
if (r?.logs) setLogs(r.logs);
```

### 教訓
> 每個 App 的 `action.ts` runAction 回傳格式可能不同，**務必先確認回傳結構再寫接收邏輯**。

---

## 坑 16 — React Hooks 放在 early return 之後導致白屏 ⚠️

### 現象
Churn Analysis DashboardPage 打開後全白，無任何錯誤訊息（靜默崩潰）。

### 根因
```javascript
// ❌ useEffect 在 early return 之後 → 違反 Hooks 規則
if (loading) return <Loading />;
if (!data) return <NoData />;

useEffect(() => { /* 這行永遠不該出現在這裡 */ }, []);
```
React Hooks 規則要求：**所有 Hooks 在每次 render 都必須以相同順序被呼叫**。
放在 early return 之後會導致某些 render 時 Hook 不被呼叫。

### 正確做法
```javascript
// ✅ 所有 Hooks 集中在函數頂部
const [data, setData] = useState(null);
useEffect(() => { load(); }, []);
useEffect(() => { /* click outside handler */ }, []);

// early return 放在所有 Hooks 之後
if (loading) return <Loading />;
if (!data) return <NoData />;
```

---

## 坑 17 — Dropdown `onClick` 在 `mousedown` 外部偵測下無效 🔍

### 現象
Autocomplete 下拉選單看得到客戶列表，但點選後不會帶入輸入框。

### 根因
瀏覽器事件執行順序：**`mousedown → blur → mouseup → click`**

`document.addEventListener("mousedown")` 的 click-outside handler
在 `click` 之前執行。input 因 mousedown 失去焦點 → React 重渲染移除 dropdown DOM →
`click` 事件的 target 已不存在。

### 正確做法
```jsx
// ✅ onMouseDown + preventDefault 阻止 blur
<div className="ac-item"
  onMouseDown={e => { e.preventDefault(); selectItem(c); }}
>

// ❌ onClick 在 blur 之後觸發，DOM 可能已移除
<div className="ac-item"
  onClick={() => selectItem(c)}
>
```

### 通則
> 凡是有「點擊外部關閉」邏輯的 dropdown / popover / modal，
> 選項互動一律使用 **`onMouseDown` + `e.preventDefault()`**。

---

## 坑 18 — CSS `min-height: 100vh` 導致 overflow 永遠不觸發 ⚠️

### 現象
Sales Input App 完全無法捲動，側邊也看不到滾軸。

### 根因
```css
/* ❌ min-height 讓容器高度無限延伸，子元素永遠不溢出 */
.app-layout { min-height: 100vh; }
.app-main { min-height: 100vh; }
.app-content { overflow-y: auto; }  /* 不會觸發！ */
```

### 正確做法
```css
/* ✅ 固定高度 + overflow hidden，讓 app-content 成為唯一捲動區 */
html, body, #root { height: 100%; overflow: hidden; }
.app-layout { display: flex; height: 100vh; overflow: hidden; }
.app-main { flex: 1; height: 100vh; overflow: hidden; }
.app-content { flex: 1; overflow-y: auto; }
```

### 關鍵原理
> `overflow-y: auto` 只在內容超過容器「固定高度」時生效。
> `min-height` 允許容器隨內容延伸 → 永遠不溢出 → 滾軸不出現。

---

## 坑 19 — VFS 字串替換殘留舊函數片段致編譯錯誤 ⚠️

### 現象
替換 CompanyAutocomplete 元件後，編譯錯誤 `Unexpected "}"` at line 128。

### 根因
用 brace counting `{` `}` 偵測函數結尾時，JSX 中的 `{expression}` 也被計入，
導致提前認定函數結束，舊函數後半段殘留在程式碼中。

### 正確做法
1. 替換完成後，**驗證目標函數只出現 1 次**
2. 檢查沒有孤立的 `}) {`、`};` 等殘留語法
3. 上傳前先呼叫 **compile API** 確認無錯誤

```python
assert content.count("function CompanyAutocomplete") == 1
r = api("POST", f"/builder/apps/{app_id}/compile")
assert not r.get("errors")
```

### 教訓
> 不要信任 brace counting 來定位 JSX 函數邊界。
> 替換後的驗證步驟不可省略。
