#!/usr/bin/env python3
"""
耐落請假系統（員工端）VFS 注入腳本
====================================
功能：
1. 登入 AI GO 取得 JWT
2. GET 現有 App 取得 vfs_version
3. PATCH 注入所有 VFS 檔案
4. POST 編譯（dev=true）
5. 若編譯失敗，輸出錯誤訊息
"""

import json
import sys
import requests

# ============================================================
# 配置
# ============================================================
BASE_URL = "https://ai-go.app"
APP_ID = "da7789b4-59bc-422c-8e7b-b6a7b9103146"
LOGIN_EMAIL = "admin@tslg.com.tw"
LOGIN_PASSWORD = "password123"

# ============================================================
# VFS 檔案內容
# ============================================================

PACKAGE_JSON = """{
  "name": "nailuo-leave-employee",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "lucide-react": "^0.294.0",
    "react-hot-toast": "^2.4.1"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0"
  }
}"""

# ─────────────────────────────────────────────
# src/main.tsx
# ─────────────────────────────────────────────
MAIN_TSX = r"""import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./App.css";

const rootEl = (window as any).__CUSTOM_APP_ROOT__ || document.getElementById("root");
ReactDOM.createRoot(rootEl!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

# ─────────────────────────────────────────────
# src/App.tsx
# ─────────────────────────────────────────────
APP_TSX = r"""import React from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import AppLayout from "./components/AppLayout";
import ChatPage from "./pages/ChatPage";
import RecordsPage from "./pages/RecordsPage";
import AttendancePage from "./pages/AttendancePage";
import BalancePage from "./pages/BalancePage";
import PolicyPage from "./pages/PolicyPage";
import AgentsPage from "./pages/AgentsPage";
import NotFoundPage from "./pages/NotFoundPage";

const App: React.FC = () => {
  return (
    <HashRouter>
      <Toaster position="top-center" toastOptions={{ duration: 3000 }} />
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/records" element={<RecordsPage />} />
          <Route path="/attendance" element={<AttendancePage />} />
          <Route path="/balance" element={<BalancePage />} />
          <Route path="/policy" element={<PolicyPage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
};

export default App;
"""

# ─────────────────────────────────────────────
# src/App.css
# ─────────────────────────────────────────────
APP_CSS = r""":host, :root {
  --primary: #6366f1;
  --primary-dark: #4f46e5;
  --primary-light: #eef2ff;
  --accent: #8b5cf6;
  --accent-light: #ede9fe;
  --success: #16a34a;
  --success-light: #dcfce7;
  --warning: #ea580c;
  --warning-light: #ffedd5;
  --danger: #dc2626;
  --danger-light: #fee2e2;
  --info: #2563eb;
  --info-light: #dbeafe;
  --text: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --border: #e2e8f0;
  --bg: #f8fafc;
  --bg-card: #ffffff;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 1px 3px rgba(15,23,42,0.06);
  --shadow-md: 0 4px 12px rgba(15,23,42,0.08);
  --gradient: linear-gradient(135deg, #6366f1, #8b5cf6);
  font-family: -apple-system, "PingFang TC", "Microsoft JhengHei", sans-serif;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, "PingFang TC", "Microsoft JhengHei", sans-serif;
  color: var(--text);
  background: var(--bg);
  font-size: 14px;
}

button, input, textarea, select {
  font-family: inherit;
  font-size: inherit;
}

button { cursor: pointer; border: none; background: none; color: inherit; }

/* ========== Layout ========== */
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.app-sidebar {
  width: 240px;
  background: var(--bg-card);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.2s ease;
  overflow: hidden;
}

.app-sidebar.collapsed {
  width: 64px;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
  overflow-y: auto;
}

/* ========== Sidebar ========== */
.sidebar-brand {
  padding: 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-logo {
  width: 36px;
  height: 36px;
  background: var(--gradient);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
  flex-shrink: 0;
}

.sidebar-title { font-weight: 700; font-size: 15px; white-space: nowrap; }
.sidebar-subtitle { font-size: 11px; color: var(--text-muted); white-space: nowrap; }

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
}

.sidebar-section-label {
  font-size: 11px;
  color: var(--text-muted);
  padding: 14px 12px 6px;
  font-weight: 500;
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  margin: 1px 0;
  text-decoration: none;
  transition: background 0.15s;
  white-space: nowrap;
}

.sidebar-nav-item:hover { background: #f1f5f9; }

.sidebar-nav-item.active {
  background: var(--primary-light);
  color: var(--primary);
  font-weight: 600;
}

.sidebar-nav-item .nav-icon { font-size: 16px; flex-shrink: 0; width: 20px; text-align: center; }
.sidebar-nav-item .nav-label { flex: 1; }

.sidebar-badge {
  margin-left: auto;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  background: var(--danger);
  color: white;
  font-weight: 600;
}

.sidebar-user {
  margin: 8px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-avatar {
  width: 32px;
  height: 32px;
  background: var(--gradient);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}

.sidebar-user-name { font-size: 13px; font-weight: 600; white-space: nowrap; }
.sidebar-user-role { font-size: 11px; color: var(--text-muted); white-space: nowrap; }

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  margin: 4px 8px 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-muted);
  transition: background 0.15s;
}

.sidebar-toggle:hover { background: #f1f5f9; }

.app-sidebar.collapsed .sidebar-title,
.app-sidebar.collapsed .sidebar-subtitle,
.app-sidebar.collapsed .sidebar-section-label,
.app-sidebar.collapsed .nav-label,
.app-sidebar.collapsed .sidebar-badge,
.app-sidebar.collapsed .sidebar-user-name,
.app-sidebar.collapsed .sidebar-user-role {
  display: none;
}

.app-sidebar.collapsed .sidebar-nav-item {
  justify-content: center;
  padding: 10px 0;
}

.app-sidebar.collapsed .sidebar-brand {
  justify-content: center;
  padding: 16px 8px;
}

.app-sidebar.collapsed .sidebar-user {
  justify-content: center;
  padding: 8px;
}

/* ========== Header ========== */
.app-header {
  padding: 16px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}

.header-left { display: flex; align-items: center; gap: 12px; }
.header-title { font-size: 18px; font-weight: 700; }
.header-subtitle { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }

/* ========== Common Components ========== */
.page-container {
  padding: 24px;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.kpi-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  margin-bottom: 10px;
}

.kpi-icon.blue { background: var(--info-light); }
.kpi-icon.green { background: var(--success-light); }
.kpi-icon.orange { background: var(--warning-light); }
.kpi-icon.red { background: var(--danger-light); }
.kpi-icon.purple { background: var(--accent-light); }

.kpi-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.kpi-value { font-size: 22px; font-weight: 700; }
.kpi-meta { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

.panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.panel-title { font-size: 15px; font-weight: 700; }
.panel-subtitle { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

/* ========== Table ========== */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.data-table thead th {
  text-align: left;
  padding: 10px 12px;
  font-weight: 500;
  color: var(--text-secondary);
  font-size: 12px;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  white-space: nowrap;
}

.data-table tbody td {
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
}

.data-table tbody tr:hover { background: #fafbfc; }
.data-table tbody tr:last-child td { border: 0; }

/* ========== Status Badge ========== */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.pending { background: var(--warning-light); color: #b45309; }
.status-badge.approved { background: var(--success-light); color: #15803d; }
.status-badge.rejected { background: var(--danger-light); color: #b91c1c; }
.status-badge.cancelled { background: #f1f5f9; color: var(--text-secondary); }
.status-badge.draft { background: var(--info-light); color: #1d4ed8; }

/* ========== Leave Card ========== */
.leave-card {
  background: linear-gradient(135deg, var(--primary-light) 0%, var(--accent-light) 100%);
  border: 1px solid #a5b4fc;
  border-radius: var(--radius);
  padding: 14px 16px;
  margin-top: 8px;
}

.leave-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.leave-card-title { font-weight: 700; font-size: 13px; }

.leave-card-summary {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary-dark);
  margin: 6px 0 10px;
  padding: 8px 12px;
  background: rgba(255,255,255,0.6);
  border-radius: 8px;
}

.leave-card-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 14px;
  font-size: 12px;
}

.leave-card-cell { display: flex; gap: 6px; align-items: baseline; }
.leave-card-cell .cell-label { color: var(--text-muted); font-size: 11px; flex-shrink: 0; }
.leave-card-cell .cell-value { font-weight: 600; }

.leave-card-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.leave-card-actions button {
  flex: 1;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
}

.btn-primary {
  background: var(--primary);
  color: white;
  border: none;
}
.btn-primary:hover { background: var(--primary-dark); }

.btn-ghost {
  background: white;
  color: var(--text-secondary);
  border: 1px solid var(--border);
}
.btn-ghost:hover { background: var(--bg); }

/* ========== Chat ========== */
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.chat-header {
  padding: 14px 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.ai-avatar {
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, #f97316, #dc2626);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.ai-name { font-weight: 700; font-size: 15px; }
.ai-status { font-size: 11px; color: var(--success); display: flex; align-items: center; gap: 4px; }
.ai-dot { width: 6px; height: 6px; background: var(--success); border-radius: 50%; }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 880px;
  margin: 0 auto;
  width: 100%;
}

.chat-msg {
  display: flex;
  gap: 10px;
  max-width: 100%;
  animation: msgSlideIn 0.3s ease;
}

@keyframes msgSlideIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-msg.ai { align-self: flex-start; }
.chat-msg.user { align-self: flex-end; flex-direction: row-reverse; }

.msg-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
}

.chat-msg.ai .msg-avatar { background: linear-gradient(135deg, #f97316, #dc2626); }
.chat-msg.user .msg-avatar { background: var(--gradient); color: white; font-weight: 700; font-size: 13px; }

.msg-bubble {
  padding: 12px 16px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
  min-width: 0;
  max-width: 100%;
}

.msg-bubble p { margin: 0; }
.msg-bubble p + p { margin-top: 6px; }
.msg-bubble ul { margin: 6px 0; padding-left: 18px; }
.msg-bubble li { margin: 2px 0; }

.chat-msg.ai .msg-bubble {
  flex: 1;
  min-width: 0;
  max-width: min(560px, calc(100% - 50px));
  background: var(--bg-card);
  border-top-left-radius: 4px;
  box-shadow: var(--shadow);
}

.chat-msg.user .msg-bubble {
  max-width: min(460px, calc(100% - 50px));
  background: var(--primary);
  color: white;
  border-top-right-radius: 4px;
}

.chat-chips {
  display: flex;
  gap: 8px;
  padding: 12px 24px 0;
  flex-wrap: wrap;
  max-width: 880px;
  margin: 0 auto;
  width: 100%;
  flex-shrink: 0;
}

.chat-chip {
  padding: 7px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 999px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.chat-chip:hover {
  background: var(--primary-light);
  border-color: var(--primary);
  color: var(--primary);
}

.chat-input-area {
  padding: 14px 24px 18px;
  max-width: 880px;
  margin: 0 auto;
  width: 100%;
  flex-shrink: 0;
}

.chat-input-box {
  display: flex;
  gap: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 8px 8px 8px 16px;
  box-shadow: var(--shadow);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.chat-input-box:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.chat-input-field {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  padding: 8px 0;
  background: transparent;
}

.chat-send-btn {
  background: var(--primary);
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.15s;
}

.chat-send-btn:hover { background: var(--primary-dark); }
.chat-send-btn:disabled { background: #cbd5e1; cursor: not-allowed; }

.typing-indicator {
  display: inline-flex;
  gap: 3px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: var(--text-muted);
  border-radius: 50%;
  animation: typingBounce 1.2s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ========== Attendance Hero ========== */
.attendance-hero {
  background: var(--gradient);
  border-radius: 16px;
  padding: 24px 28px;
  color: white;
  margin-bottom: 18px;
}

.att-hero-row { display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
.att-hero-info { flex: 1; min-width: 200px; }
.att-hero-time { font-size: 42px; font-weight: 700; letter-spacing: 1px; }
.att-hero-label { font-size: 12px; opacity: 0.85; }
.att-hero-status { font-size: 13px; opacity: 0.9; margin-top: 4px; }

.att-hero-stats {
  display: flex;
  gap: 28px;
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(255,255,255,0.2);
  flex-wrap: wrap;
}

.att-stat-label { font-size: 11px; opacity: 0.8; }
.att-stat-value { font-size: 20px; font-weight: 700; }

.punch-button {
  padding: 14px 32px;
  background: white;
  color: var(--primary-dark);
  border: none;
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 14px rgba(0,0,0,0.15);
  transition: transform 0.15s;
  cursor: pointer;
}

.punch-button:hover { transform: translateY(-2px); }
.punch-button.out { background: var(--danger-light); color: #991b1b; }

/* ========== Balance Cards ========== */
.balance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.balance-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}

.balance-card-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.balance-card-icon { font-size: 24px; }
.balance-card-name { font-weight: 700; font-size: 14px; }
.balance-card-meta { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.balance-bar {
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
  margin: 10px 0;
}

.balance-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s;
}

.balance-stats { display: flex; justify-content: space-between; font-size: 12px; }
.balance-stats .stat-label { color: var(--text-muted); }
.balance-stats .stat-value { font-weight: 700; }

/* ========== Policy Cards ========== */
.policy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 14px;
}

.policy-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}

.policy-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.policy-icon { font-size: 22px; }
.policy-name { font-weight: 700; font-size: 14px; }
.policy-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 999px;
  margin-left: auto;
  font-weight: 500;
}

.policy-rules {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 10px;
  font-size: 12px;
  margin-top: 8px;
}

.policy-rules .rule-label { color: var(--text-muted); font-size: 11px; }
.policy-rules .rule-value { color: var(--text); font-weight: 600; font-size: 12px; }

.policy-body { font-size: 12px; line-height: 1.7; color: var(--text-secondary); margin-top: 8px; }

/* ========== Agent Cards ========== */
.agent-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  display: grid;
  grid-template-columns: 52px 1fr auto;
  gap: 14px;
  align-items: center;
  margin-bottom: 10px;
  box-shadow: var(--shadow);
}

.agent-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 20px;
  color: white;
}

.agent-name { font-weight: 700; font-size: 15px; }
.agent-role { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }

.agent-tag {
  display: inline-block;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  margin-right: 4px;
}

/* ========== Confirm Dialog ========== */
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15,23,42,0.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.confirm-dialog {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(15,23,42,0.2);
  animation: dialogSlideIn 0.2s ease;
}

@keyframes dialogSlideIn {
  from { opacity: 0; transform: translateY(-10px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.confirm-title { font-size: 16px; font-weight: 700; margin-bottom: 8px; }
.confirm-message { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 20px; }

.confirm-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.confirm-actions button {
  padding: 8px 18px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
}

/* ========== Filter ========== */
.filter-row {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-row select,
.filter-row input[type="search"],
.filter-row input[type="text"] {
  padding: 7px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  background: var(--bg-card);
  color: var(--text);
}

.filter-row select:focus,
.filter-row input:focus {
  outline: none;
  border-color: var(--primary);
}

.filter-btn {
  padding: 7px 14px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
}

.filter-btn:hover { background: var(--bg); }
.filter-btn.active { background: var(--primary-light); border-color: var(--primary); color: var(--primary-dark); }

/* ========== Responsive ========== */
@media (max-width: 1024px) {
  .app-sidebar { width: 64px; }
  .app-sidebar .sidebar-title,
  .app-sidebar .sidebar-subtitle,
  .app-sidebar .sidebar-section-label,
  .app-sidebar .nav-label,
  .app-sidebar .sidebar-badge,
  .app-sidebar .sidebar-user-name,
  .app-sidebar .sidebar-user-role {
    display: none;
  }
  .app-sidebar .sidebar-nav-item { justify-content: center; padding: 10px 0; }
  .app-sidebar .sidebar-brand { justify-content: center; }
  .app-sidebar .sidebar-user { justify-content: center; padding: 8px; }
  .app-sidebar .sidebar-toggle { display: none; }
}

@media (max-width: 768px) {
  .app-sidebar { display: none; }
  .page-container { padding: 16px; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .balance-grid { grid-template-columns: 1fr; }
  .policy-grid { grid-template-columns: 1fr; }
}

/* ========== Not Found ========== */
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  text-align: center;
}

.not-found-code { font-size: 72px; font-weight: 800; color: var(--primary); opacity: 0.3; }
.not-found-text { font-size: 18px; font-weight: 600; margin-top: 8px; }
.not-found-hint { font-size: 14px; color: var(--text-muted); margin-top: 4px; }

.not-found a {
  margin-top: 16px;
  padding: 8px 20px;
  background: var(--primary);
  color: white;
  border-radius: var(--radius-sm);
  text-decoration: none;
  font-weight: 600;
  font-size: 13px;
}

/* ========== Info Box ========== */
.info-box {
  padding: 12px 16px;
  background: var(--primary-light);
  border: 1px solid #a5b4fc;
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--primary-dark);
  line-height: 1.6;
}

.warning-box {
  padding: 12px 16px;
  background: #fef3c7;
  border-left: 3px solid #fbbf24;
  border-radius: 6px;
  font-size: 12px;
  color: #78350f;
  line-height: 1.6;
}
"""

# ─────────────────────────────────────────────
# src/routes.ts
# ─────────────────────────────────────────────
ROUTES_TS = r"""/** 員工端 6 個導航項 */
export interface NavItem {
  path: string;
  label: string;
  icon: string;
  section: string;
  badge?: number;
}

export const navItems: NavItem[] = [
  { path: "/chat", label: "AI 對話請假", icon: "💬", section: "日常工作" },
  { path: "/records", label: "我的請假紀錄", icon: "📋", section: "日常工作", badge: 2 },
  { path: "/attendance", label: "出勤打卡", icon: "🗓️", section: "日常工作" },
  { path: "/balance", label: "我的假期額度", icon: "📊", section: "日常工作" },
  { path: "/policy", label: "請假規範說明", icon: "📖", section: "資源" },
  { path: "/agents", label: "我的代理人", icon: "👥", section: "資源" },
];
"""

# ─────────────────────────────────────────────
# src/constants.ts
# ─────────────────────────────────────────────
CONSTANTS_TS = r"""/** 18 種假別常數 */
export interface LeaveTypeConst {
  code: string;
  name: string;
  icon: string;
  color: string;
  bgColor: string;
  maxDays: string;
  minUnit: string;
  payRule: string;
  docRequired: string;
  description: string;
}

export const LEAVE_TYPES: LeaveTypeConst[] = [
  { code: "annual", name: "特別休假", icon: "🌴", color: "#16a34a", bgColor: "#dcfce7", maxDays: "依年資 3-30 日", minUnit: "0.5 小時", payRule: "薪資照給", docRequired: "不需要", description: "6個月-1年3日/1-2年7日/2-3年10日/3-5年14日/5-10年15日/10年+每年+1日(上限30)" },
  { code: "personal", name: "事假", icon: "📝", color: "#94a3b8", bgColor: "#f1f5f9", maxDays: "14 日", minUnit: "0.5 小時", payRule: "不給薪（業務不扣）", docRequired: "不需要", description: "超過14日須經部門主管核准。休息日、例假日及國定假日不予計入。" },
  { code: "sick", name: "病假（未住院）", icon: "🤒", color: "#ea580c", bgColor: "#ffedd5", maxDays: "30 日", minUnit: "0.5 小時", payRule: "薪資減半", docRequired: "1天以上需診斷書", description: "30日內薪資減半，業務人員不扣薪。住院可延長至1年。" },
  { code: "sick_hospital", name: "病假（住院）", icon: "🏥", color: "#dc2626", bgColor: "#fee2e2", maxDays: "1 年（含未住院）", minUnit: "0.5 日", payRule: "1年內減半/超過不給", docRequired: "住院證明", description: "未住院+住院合計不超過1年，超過1年部分不給薪。" },
  { code: "family_care", name: "家庭照顧假", icon: "👨‍👩‍👧", color: "#7c3aed", bgColor: "#ede9fe", maxDays: "7 日", minUnit: "0.5 小時", payRule: "不給薪（併事假）", docRequired: "不需要", description: "家庭成員預防接種、發生嚴重疾病或其他重大事故。日數併入事假計算。" },
  { code: "comp", name: "補休", icon: "🔄", color: "#0891b2", bgColor: "#cffafe", maxDays: "依加班時數", minUnit: "0.5 小時", payRule: "不另給薪（已計加班費）", docRequired: "不需要", description: "由加班時數轉換而來，須在加班日起6個月內請畢。" },
  { code: "menstrual", name: "生理假", icon: "🩸", color: "#e11d48", bgColor: "#fce7f3", maxDays: "每月 1 日", minUnit: "0.5 日", payRule: "薪資減半（3日內不併病假）", docRequired: "不需要", description: "女性員工適用。全年3日內不併入病假，超過3日併入病假計算。" },
  { code: "marriage", name: "婚假", icon: "💍", color: "#d97706", bgColor: "#fef3c7", maxDays: "8 日", minUnit: "0.5 日", payRule: "薪資照給", docRequired: "結婚證書", description: "結婚登記前10日起3個月內請畢，可分次請休。" },
  { code: "funeral", name: "喪假", icon: "🕊️", color: "#374151", bgColor: "#f3f4f6", maxDays: "3-8 日（依親等）", minUnit: "0.5 日", payRule: "薪資照給", docRequired: "訃聞或死亡證明", description: "父母/養父母/配偶8日，祖父母/子女/配偶父母6日，兄弟姊妹/祖父母之父母3日。100日內請畢。" },
  { code: "maternity", name: "產假", icon: "🤱", color: "#be185d", bgColor: "#fce7f3", maxDays: "8 週", minUnit: "1 日", payRule: "任職≥6月照給/＜6月減半", docRequired: "醫師證明", description: "分娩8週，妊娠3個月以上流產4週，未滿3個月流產1週。" },
  { code: "paternity", name: "陪產（檢）假", icon: "👶", color: "#2563eb", bgColor: "#dbeafe", maxDays: "7 日", minUnit: "0.5 日", payRule: "薪資照給", docRequired: "出生證明", description: "配偶分娩時，可於產前後合計15日內請休。" },
  { code: "parental", name: "育嬰留停", icon: "🍼", color: "#7c3aed", bgColor: "#ede9fe", maxDays: "最長 2 年", minUnit: "1 月", payRule: "留停期間不給薪", docRequired: "戶籍資料", description: "子女滿3歲前可申請。期間享有育嬰留職停薪津貼（勞保）。" },
  { code: "official", name: "公假", icon: "🪖", color: "#0369a1", bgColor: "#e0f2fe", maxDays: "依事由", minUnit: "0.5 日", payRule: "薪資照給", docRequired: "公文或通知書", description: "兵役召集、選舉投票、政府調訓、法院傳喚等。" },
  { code: "work_injury", name: "公傷假", icon: "🤕", color: "#991b1b", bgColor: "#fee2e2", maxDays: "最長 2 年", minUnit: "1 日", payRule: "薪資照給", docRequired: "醫師診斷書+事故報告", description: "因執行職務而致傷害或疾病，經醫師診斷需休養者。" },
  { code: "disaster", name: "天然災害假", icon: "🌪️", color: "#6b7280", bgColor: "#f3f4f6", maxDays: "依公告", minUnit: "0.5 日", payRule: "不給薪（不扣全勤）", docRequired: "不需要", description: "依政府公告停班停課辦理，不影響全勤及考績。" },
  { code: "vaccination", name: "疫苗接種假", icon: "💉", color: "#059669", bgColor: "#d1fae5", maxDays: "依接種次數", minUnit: "0.5 日", payRule: "不給薪（不扣全勤）", docRequired: "接種紀錄卡", description: "依中央流行疫情指揮中心公告之疫苗接種，自接種日起至翌日24時。" },
  { code: "aboriginal", name: "原住民族歲時祭儀假", icon: "🎎", color: "#9333ea", bgColor: "#f3e8ff", maxDays: "1 日", minUnit: "1 日", payRule: "薪資照給", docRequired: "戶籍資料", description: "原住民族員工於歲時祭儀期間，得申請1日放假。" },
  { code: "volunteer", name: "志工假", icon: "🤝", color: "#0d9488", bgColor: "#ccfbf1", maxDays: "依服勤時數", minUnit: "0.5 日", payRule: "薪資照給", docRequired: "志工服務證明", description: "依志願服務法規定，志工服務期間得請志工假。" },
];

/** 狀態顏色對應 */
export const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  pending: { label: "待簽核", className: "pending" },
  approved: { label: "已核准", className: "approved" },
  rejected: { label: "已退回", className: "rejected" },
  cancelled: { label: "已取消", className: "cancelled" },
  draft: { label: "草稿", className: "draft" },
};
"""

# ─────────────────────────────────────────────
# src/types.ts
# ─────────────────────────────────────────────
TYPES_TS = r"""/** 員工 */
export interface Employee {
  id: number;
  name: string;
  department_id?: number;
  gender?: string;
  birthday?: string;
  job_title?: string;
  active?: boolean;
  custom_data?: {
    rank?: string;
    hire_date?: string;
    is_sales?: boolean;
    manager_id?: number;
    job_title?: string;
    role?: string;
    dept_name?: string;
  };
}

/** 假別 */
export interface LeaveType {
  id: number;
  name: string;
  color?: string;
  custom_data?: {
    code?: string;
    icon?: string;
    max_days?: string;
    min_unit?: string;
    pay_rule?: string;
    doc_required?: string;
  };
}

/** 請假單 */
export interface LeaveRecord {
  id: number;
  employee_id: number;
  employee_name?: string;
  leave_type_id: number;
  leave_name?: string;
  date_from: string;
  date_to: string;
  number_of_days: number;
  hours?: number;
  state?: string;
  status?: string;
  reason?: string;
  approval_status?: string;
  approver_id?: number;
  approver_name?: string;
  agent_id?: number;
  agent_name?: string;
  pay_impact?: string;
  doc_status?: string;
  custom_data?: Record<string, unknown>;
}

/** 假期額度 */
export interface LeaveAllocation {
  id: number;
  employee_id: number;
  leave_type_id: number;
  number_of_days?: number;
  used_days?: number;
  remaining_days?: number;
  total_days?: number;
  balance?: number;
  year?: number;
  state?: string;
  custom_data?: Record<string, unknown>;
}

/** 部門 */
export interface Department {
  id: number;
  name: string;
  parent_id?: number;
  manager_id?: number;
}

/** 聊天訊息 */
export interface ChatMessage {
  id: string;
  role: "user" | "ai";
  content: string;
  leaveData?: Partial<LeaveRecord>;
  timestamp: number;
}

/** 打卡紀錄 */
export interface AttendanceRecord {
  id?: number;
  employee_id: number;
  date: string;
  clock_in?: string;
  clock_out?: string;
  hours_worked?: number;
  status?: string;
  note?: string;
}

/** 代理人 */
export interface LeaveAgent {
  id?: number;
  employee_id: number;
  agent_id: number;
  agent_name: string;
  agent_role?: string;
  agent_dept?: string;
  type: "primary" | "secondary";
  start_date?: string;
  end_date?: string;
  status?: string;
}
"""

# ─────────────────────────────────────────────
# src/components/AppLayout.tsx
# ─────────────────────────────────────────────
APP_LAYOUT_TSX = r"""import React, { useState, useEffect, createContext, useContext } from "react";
import { Outlet } from "react-router-dom";
import AppSidebar from "./AppSidebar";
import type { Employee } from "../types";

/** 使用者上下文 */
interface UserContextType {
  currentUser: Employee | null;
  loading: boolean;
}

const UserContext = createContext<UserContextType>({ currentUser: null, loading: true });
export const useCurrentUser = () => useContext(UserContext);

/** 取得 API 基礎路徑 */
const getApiBase = () => (window as any).__API_BASE__ || "/api/v1";
const getAppId = () => (window as any).__APP_ID__ || "";
const getToken = () => (window as any).__APP_TOKEN__ || "";

/** 透過 DB Proxy 查詢員工 */
async function fetchCurrentEmployee(): Promise<Employee | null> {
  const apiBase = getApiBase();
  const appId = getAppId();
  const token = getToken();
  const userEmail = (window as any).__USER_EMAIL__ || "";

  try {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const resp = await fetch(`${apiBase}/proxy/${appId}/hr_employees`, {
      method: "GET",
      headers,
      credentials: "include",
    });

    if (!resp.ok) return null;

    const result = await resp.json();
    const employees: Employee[] = result?.data || result || [];

    if (userEmail) {
      const matched = employees.find(
        (e: any) => e.custom_data?.email === userEmail || e.name === userEmail
      );
      if (matched) return matched;
    }

    return employees.length > 0 ? employees[0] : null;
  } catch {
    return null;
  }
}

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [currentUser, setCurrentUser] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCurrentEmployee().then((emp) => {
      if (emp) {
        setCurrentUser(emp);
      } else {
        /* 使用預設 demo 使用者 */
        setCurrentUser({
          id: 1,
          name: "張文武",
          department_id: 1,
          job_title: "業務專員",
          custom_data: {
            rank: "五職等",
            hire_date: "2022-03-15",
            is_sales: true,
            dept_name: "業務部",
          },
        });
      }
      setLoading(false);
    });
  }, []);

  return (
    <UserContext.Provider value={{ currentUser, loading }}>
      <div className="app-layout">
        <AppSidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(!collapsed)}
          currentUser={currentUser}
        />
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </UserContext.Provider>
  );
};

export default AppLayout;
"""

# ─────────────────────────────────────────────
# src/components/AppSidebar.tsx
# ─────────────────────────────────────────────
APP_SIDEBAR_TSX = r"""import React from "react";
import { NavLink } from "react-router-dom";
import { MessageSquare, ClipboardList, CalendarDays, BarChart3, BookOpen, Users } from "lucide-react";
import { navItems } from "../routes";
import type { Employee } from "../types";

const ICON_MAP: Record<string, React.FC<{size?: number}>> = {
  chat: MessageSquare,
  clipboard: ClipboardList,
  calendar: CalendarDays,
  chart: BarChart3,
  book: BookOpen,
  users: Users,
};

interface Props {
  collapsed: boolean;
  onToggle: () => void;
  currentUser: Employee | null;
}

const AppSidebar: React.FC<Props> = ({ collapsed, onToggle, currentUser }) => {
  const sections = Array.from(new Set(navItems.map((n) => n.section)));
  const userName = currentUser?.name || "使用者";
  const deptName = currentUser?.custom_data?.dept_name || "部門";
  const rank = currentUser?.custom_data?.rank || "";

  return (
    <aside className={`app-sidebar${collapsed ? " collapsed" : ""}`}>
      {/* 品牌 */}
      <div className="sidebar-brand">
        <div className="sidebar-logo">N</div>
        <div>
          <div className="sidebar-title">耐落請假系統</div>
          <div className="sidebar-subtitle">員工自助平台</div>
        </div>
      </div>

      {/* 導航 */}
      <nav className="sidebar-nav">
        {sections.map((sec) => (
          <React.Fragment key={sec}>
            <div className="sidebar-section-label">{sec}</div>
            {navItems
              .filter((n) => n.section === sec)
              .map((item) => {
                const IconComp = ICON_MAP[item.icon];
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `sidebar-nav-item${isActive ? " active" : ""}`
                    }
                  >
                    <span className="nav-icon">
                      {IconComp ? <IconComp size={16} /> : null}
                    </span>
                    <span className="nav-label">{item.label}</span>
                    {item.badge && item.badge > 0 && (
                      <span className="sidebar-badge">{item.badge}</span>
                    )}
                  </NavLink>
                );
              })}
          </React.Fragment>
        ))}
      </nav>

      {/* 使用者卡片 */}
      <div className="sidebar-user">
        <div className="sidebar-avatar">{userName.charAt(0)}</div>
        <div>
          <div className="sidebar-user-name">{userName}</div>
          <div className="sidebar-user-role">
            {deptName}
            {rank ? ` · ${rank}` : ""}
          </div>
        </div>
      </div>

      {/* 收合按鈕 */}
      <button className="sidebar-toggle" onClick={onToggle}>
        {collapsed ? ">" : "<"}
      </button>
    </aside>
  );
};

export default AppSidebar;
"""

# ─────────────────────────────────────────────
# src/components/AppHeader.tsx
# ─────────────────────────────────────────────
APP_HEADER_TSX = r"""import React from "react";

interface Props {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

const AppHeader: React.FC<Props> = ({ title, subtitle, actions }) => {
  return (
    <div className="app-header">
      <div className="header-left">
        <div>
          <div className="header-title">{title}</div>
          {subtitle && <div className="header-subtitle">{subtitle}</div>}
        </div>
      </div>
      {actions && <div>{actions}</div>}
    </div>
  );
};

export default AppHeader;
"""

# ─────────────────────────────────────────────
# src/components/LeaveCard.tsx
# ─────────────────────────────────────────────
LEAVE_CARD_TSX = r"""import React from "react";
import StatusBadge from "./StatusBadge";
import type { LeaveRecord } from "../types";

interface Props {
  leave: Partial<LeaveRecord>;
  onConfirm?: () => void;
  onCancel?: () => void;
  showActions?: boolean;
}

const LeaveCard: React.FC<Props> = ({ leave, onConfirm, onCancel, showActions = false }) => {
  return (
    <div className="leave-card">
      <div className="leave-card-head">
        <div className="leave-card-title">📋 請假單預覽</div>
        {leave.approval_status && (
          <StatusBadge status={leave.approval_status} />
        )}
      </div>

      <div className="leave-card-summary">
        {leave.leave_name || "假別"} — {leave.date_from || ""} ~ {leave.date_to || ""}
        {leave.number_of_days ? ` (${leave.number_of_days} 日)` : ""}
      </div>

      <div className="leave-card-grid">
        <div className="leave-card-cell">
          <span className="cell-label">假別</span>
          <span className="cell-value">{leave.leave_name || "—"}</span>
        </div>
        <div className="leave-card-cell">
          <span className="cell-label">天數</span>
          <span className="cell-value">{leave.number_of_days ?? "—"} 日</span>
        </div>
        <div className="leave-card-cell">
          <span className="cell-label">起始</span>
          <span className="cell-value">{leave.date_from || "—"}</span>
        </div>
        <div className="leave-card-cell">
          <span className="cell-label">結束</span>
          <span className="cell-value">{leave.date_to || "—"}</span>
        </div>
        <div className="leave-card-cell">
          <span className="cell-label">事由</span>
          <span className="cell-value">{leave.reason || "—"}</span>
        </div>
        <div className="leave-card-cell">
          <span className="cell-label">代理人</span>
          <span className="cell-value">{leave.agent_name || "—"}</span>
        </div>
      </div>

      {showActions && (
        <div className="leave-card-actions">
          <button className="btn-primary" onClick={onConfirm}>
            ✅ 確認送出
          </button>
          <button className="btn-ghost" onClick={onCancel}>
            ✏️ 修改
          </button>
        </div>
      )}
    </div>
  );
};

export default LeaveCard;
"""

# ─────────────────────────────────────────────
# src/components/StatusBadge.tsx
# ─────────────────────────────────────────────
STATUS_BADGE_TSX = r"""import React from "react";
import { STATUS_CONFIG } from "../constants";

interface Props {
  status: string;
}

const StatusBadge: React.FC<Props> = ({ status }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG["draft"];
  return (
    <span className={`status-badge ${config.className}`}>
      {config.label}
    </span>
  );
};

export default StatusBadge;
"""

# ─────────────────────────────────────────────
# src/components/ChatBubble.tsx
# ─────────────────────────────────────────────
CHAT_BUBBLE_TSX = r"""import React from "react";
import LeaveCard from "./LeaveCard";
import type { ChatMessage } from "../types";

interface Props {
  message: ChatMessage;
  userInitial?: string;
  onConfirmLeave?: () => void;
  onCancelLeave?: () => void;
}

const ChatBubble: React.FC<Props> = ({ message, userInitial = "我", onConfirmLeave, onCancelLeave }) => {
  const isAi = message.role === "ai";

  return (
    <div className={`chat-msg ${isAi ? "ai" : "user"}`}>
      <div className="msg-avatar">
        {isAi ? "🤖" : userInitial}
      </div>
      <div className="msg-bubble">
        <div dangerouslySetInnerHTML={{ __html: message.content }} />
        {message.leaveData && (
          <LeaveCard
            leave={message.leaveData}
            showActions={!message.leaveData.id}
            onConfirm={onConfirmLeave}
            onCancel={onCancelLeave}
          />
        )}
      </div>
    </div>
  );
};

export default ChatBubble;
"""

# ─────────────────────────────────────────────
# src/components/ConfirmDialog.tsx
# ─────────────────────────────────────────────
CONFIRM_DIALOG_TSX = r"""import React from "react";

interface Props {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmDialog: React.FC<Props> = ({
  open,
  title,
  message,
  confirmText = "確認",
  cancelText = "取消",
  onConfirm,
  onCancel,
}) => {
  if (!open) return null;

  return (
    <div className="confirm-overlay" onClick={onCancel}>
      <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-title">{title}</div>
        <div className="confirm-message">{message}</div>
        <div className="confirm-actions">
          <button className="btn-ghost" onClick={onCancel}>
            {cancelText}
          </button>
          <button className="btn-primary" onClick={onConfirm}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDialog;
"""

# ─────────────────────────────────────────────
# src/pages/_manifest.json
# ─────────────────────────────────────────────
PAGES_MANIFEST = """{
  "pages": [
    { "path": "/chat", "component": "ChatPage", "title": "AI 對話請假" },
    { "path": "/records", "component": "RecordsPage", "title": "我的請假紀錄" },
    { "path": "/attendance", "component": "AttendancePage", "title": "出勤打卡" },
    { "path": "/balance", "component": "BalancePage", "title": "我的假期額度" },
    { "path": "/policy", "component": "PolicyPage", "title": "請假規範說明" },
    { "path": "/agents", "component": "AgentsPage", "title": "我的代理人" }
  ]
}"""

# ─────────────────────────────────────────────
# src/pages/NotFoundPage.tsx
# ─────────────────────────────────────────────
NOT_FOUND_PAGE_TSX = r"""import React from "react";
import { Link } from "react-router-dom";

const NotFoundPage: React.FC = () => {
  return (
    <div className="not-found">
      <div className="not-found-code">404</div>
      <div className="not-found-text">頁面不存在</div>
      <div className="not-found-hint">找不到您要的頁面，請檢查網址是否正確</div>
      <Link to="/chat">🏠 回到首頁</Link>
    </div>
  );
};

export default NotFoundPage;
"""

# ─────────────────────────────────────────────
# src/pages/ChatPage.tsx
# ─────────────────────────────────────────────
CHAT_PAGE_TSX = r"""import React, { useState, useRef, useEffect, useCallback } from "react";
import toast from "react-hot-toast";
import ChatBubble from "../components/ChatBubble";
import ConfirmDialog from "../components/ConfirmDialog";
import { useCurrentUser } from "../components/AppLayout";
import type { ChatMessage, LeaveRecord } from "../types";

/** 取得 API 相關設定 */
const getApiBase = () => (window as any).__API_BASE__ || "/api/v1";
const getAppId = () => (window as any).__APP_ID__ || "";
const getToken = () => (window as any).__APP_TOKEN__ || "";

/** 初始歡迎訊息 */
const WELCOME_MSG: ChatMessage = {
  id: "welcome",
  role: "ai",
  content: `<p>嗨，我是耐落 AI 請假助理 👋</p>
<p>跟我直接說你想請什麼假、什麼時候，我會幫你：</p>
<ul>
  <li>✓ 自動檢查你的假期額度</li>
  <li>✓ 提醒需要的證明文件</li>
  <li>✓ 計算薪資影響</li>
  <li>✓ 找到正確的核決主管</li>
  <li>✓ 一鍵產出請假單</li>
</ul>
<p style="color:var(--text-muted);font-size:12px;">點下方快速範例試試 👇</p>`,
  timestamp: Date.now(),
};

/** 快速範例 */
const QUICK_CHIPS = [
  { icon: "🌴", label: "明天請特休", text: "明天我想請一天特休" },
  { icon: "🤒", label: "想請病假 2 天", text: "我頭很痛，想請病假兩天" },
  { icon: "💍", label: "結婚要請婚假", text: "下個月我要結婚，要怎麼請婚假？" },
  { icon: "👨‍👩‍👧", label: "小孩打疫苗", text: "我女兒明天打疫苗，我想請假照顧她" },
  { icon: "🌪️", label: "颱風天", text: "明天颱風來，可以不上班嗎？" },
  { icon: "✈️", label: "請 20 天特休", text: "我想請特休 20 天環遊世界" },
];

const ChatPage: React.FC = () => {
  const { currentUser } = useCurrentUser();
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MSG]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [pendingLeave, setPendingLeave] = useState<Partial<LeaveRecord> | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  /** 呼叫 AI Server-Side Action */
  const callAiChat = async (userMessage: string): Promise<{ reply: string; leave_data?: Partial<LeaveRecord> }> => {
    const apiBase = getApiBase();
    const appId = getAppId();
    const token = getToken();

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const resp = await fetch(`${apiBase}/actions/${appId}/ai_leave_chat`, {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify({
          message: userMessage,
          employee: currentUser,
          history: messages.slice(-10).map((m) => ({ role: m.role === "ai" ? "assistant" : "user", content: m.content })),
        }),
      });

      if (resp.ok) {
        const data = await resp.json();
        return { reply: data.reply || data.message || "好的，我來幫你處理。", leave_data: data.leave_data };
      }
    } catch {
      /* 呼叫失敗時使用離線模擬回覆 */
    }

    return simulateAiReply(userMessage);
  };

  /** 離線模擬回覆 */
  const simulateAiReply = (userMsg: string): { reply: string; leave_data?: Partial<LeaveRecord> } => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const tomorrowStr = tomorrow.toISOString().split("T")[0];
    const userName = currentUser?.name || "同仁";

    if (userMsg.includes("特休") && userMsg.includes("20")) {
      return {
        reply: `<p>${userName}，你目前特休剩餘 <strong>11 日</strong>，無法一次請 20 天喔！</p><p>建議：</p><ul><li>先請完 11 天特休</li><li>剩餘 9 天可選擇事假（扣薪）</li><li>或分兩次旅行 😊</li></ul>`,
      };
    }

    if (userMsg.includes("颱風")) {
      return {
        reply: `<p>颱風天的處理方式：</p><ul><li>🌪️ 如政府宣布停班停課，公司跟進，<strong>不需另外請假</strong></li><li>📢 HR 會在前一天 18:00 前發通知</li><li>⚠️ 如政府未宣布停班但自行不到班，需請事假</li></ul><p>請留意公司公告，有問題隨時問我！</p>`,
      };
    }

    if (userMsg.includes("病假")) {
      const days = userMsg.includes("兩天") || userMsg.includes("2天") || userMsg.includes("2 天") ? 2 : 1;
      const dateTo = new Date(tomorrow);
      dateTo.setDate(dateTo.getDate() + days - 1);
      return {
        reply: `<p>好的 ${userName}，幫你整理病假申請：</p><ul><li>✅ 額度：病假剩餘 <strong>29 日</strong>，充足</li><li>💰 薪資：你是業務人員，<strong>30 日內不扣薪</strong></li>${days >= 1 ? `<li>📄 證明：${days > 1 ? "超過 1 天需附<strong>診斷書</strong>" : "1 天免附證明"}</li>` : ""}<li>👤 核決主管：<strong>李志明（部門經理）</strong></li></ul><p>請確認以下請假單：</p>`,
        leave_data: {
          leave_type_id: 3,
          leave_name: "病假",
          employee_id: currentUser?.id || 1,
          employee_name: userName,
          date_from: tomorrowStr,
          date_to: dateTo.toISOString().split("T")[0],
          number_of_days: days,
          hours: days * 8,
          reason: userMsg.includes("頭") ? "頭痛身體不適" : "身體不適",
          approver_name: "李志明",
          agent_name: "王小明",
          pay_impact: "不扣薪（業務人員）",
          doc_status: days > 1 ? "需附診斷書" : "免附",
        },
      };
    }

    if (userMsg.includes("婚假") || userMsg.includes("結婚")) {
      const nextMonth = new Date();
      nextMonth.setMonth(nextMonth.getMonth() + 1);
      const nextMonthEnd = new Date(nextMonth);
      nextMonthEnd.setDate(nextMonthEnd.getDate() + 7);
      return {
        reply: `<p>恭喜 ${userName}！🎉 婚假相關資訊：</p><ul><li>🎊 婚假 <strong>8 日</strong>，薪資照給</li><li>📅 請假期間：結婚登記前 10 日起 3 個月內請畢</li><li>📄 需附 <strong>結婚證書</strong></li><li>✂️ 可分次請休</li></ul><p>需要我幫你產一張婚假請假單嗎？請告訴我預計的婚假日期。</p>`,
      };
    }

    if (userMsg.includes("家照") || userMsg.includes("疫苗") || userMsg.includes("照顧")) {
      return {
        reply: `<p>好的 ${userName}，幫你整理家庭照顧假申請：</p><ul><li>✅ 額度：家照假剩餘 <strong>7 日</strong></li><li>💰 薪資：併入事假計算，業務人員 <strong>不扣薪</strong></li><li>📄 證明：不需要</li><li>👤 核決主管：<strong>李志明</strong></li></ul><p>請確認以下請假單：</p>`,
        leave_data: {
          leave_type_id: 5,
          leave_name: "家庭照顧假",
          employee_id: currentUser?.id || 1,
          employee_name: userName,
          date_from: tomorrowStr,
          date_to: tomorrowStr,
          number_of_days: 1,
          hours: 8,
          reason: "子女疫苗接種陪同",
          approver_name: "李志明",
          agent_name: "王小明",
          pay_impact: "不扣薪（業務人員）",
          doc_status: "免附",
        },
      };
    }

    /* 預設：特休 */
    return {
      reply: `<p>好的 ${userName}，幫你整理特休申請：</p><ul><li>✅ 額度：特休剩餘 <strong>11 日</strong></li><li>💰 薪資：<strong>照給</strong></li><li>📄 證明：不需要</li><li>👤 核決主管：<strong>李志明</strong></li></ul><p>請確認以下請假單：</p>`,
      leave_data: {
        leave_type_id: 1,
        leave_name: "特別休假",
        employee_id: currentUser?.id || 1,
        employee_name: userName,
        date_from: tomorrowStr,
        date_to: tomorrowStr,
        number_of_days: 1,
        hours: 8,
        reason: "個人事務",
        approver_name: "李志明",
        agent_name: "王小明",
        pay_impact: "薪資照給",
        doc_status: "免附",
      },
    };
  };

  /** 送出訊息 */
  const handleSend = async () => {
    const text = input.trim();
    if (!text || isTyping) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    const { reply, leave_data } = await callAiChat(text);

    const aiMsg: ChatMessage = {
      id: `ai-${Date.now()}`,
      role: "ai",
      content: reply,
      leaveData: leave_data,
      timestamp: Date.now(),
    };

    if (leave_data) {
      setPendingLeave(leave_data);
    }

    setIsTyping(false);
    setMessages((prev) => [...prev, aiMsg]);
  };

  /** 確認送出請假單 */
  const handleConfirmLeave = () => {
    setShowConfirm(true);
  };

  /** 實際寫入 DB */
  const submitLeave = async () => {
    if (!pendingLeave) return;
    setShowConfirm(false);

    const apiBase = getApiBase();
    const appId = getAppId();
    const token = getToken();

    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const resp = await fetch(`${apiBase}/proxy/${appId}/hr_leaves`, {
        method: "POST",
        headers,
        credentials: "include",
        body: JSON.stringify({
          data: {
            employee_id: pendingLeave.employee_id,
            employee_name: pendingLeave.employee_name,
            leave_type_id: pendingLeave.leave_type_id,
            leave_name: pendingLeave.leave_name,
            date_from: pendingLeave.date_from,
            date_to: pendingLeave.date_to,
            number_of_days: pendingLeave.number_of_days,
            hours: pendingLeave.hours,
            reason: pendingLeave.reason,
            approval_status: "pending",
            approver_name: pendingLeave.approver_name,
            agent_name: pendingLeave.agent_name,
            pay_impact: pendingLeave.pay_impact,
            doc_status: pendingLeave.doc_status,
            state: "submitted",
            status: "pending",
          },
        }),
      });

      const result = await resp.json();

      if (result?.approval_status === "pending" || resp.ok) {
        toast.success(result?.approval_message || "✅ 請假單已送出，等待主管簽核！");
        const confirmMsg: ChatMessage = {
          id: `ai-confirm-${Date.now()}`,
          role: "ai",
          content: `<p>✅ <strong>請假單已送出！</strong></p><ul><li>📋 單號：#${result?.id || "NEW"}</li><li>⏳ 狀態：待主管（${pendingLeave.approver_name}）簽核</li><li>📱 核准後會收到推播通知</li></ul><p>還需要請其他假嗎？</p>`,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, confirmMsg]);
      } else {
        toast.error("送出失敗，請稍後再試");
      }
    } catch {
      toast.success("✅ 請假單已送出（demo 模式）");
      const demoMsg: ChatMessage = {
        id: `ai-demo-${Date.now()}`,
        role: "ai",
        content: `<p>✅ <strong>請假單已送出！</strong>（Demo 模式）</p><ul><li>📋 單號：#DEMO-${Date.now() % 10000}</li><li>⏳ 狀態：待主管（${pendingLeave.approver_name}）簽核</li></ul><p>還需要請其他假嗎？</p>`,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, demoMsg]);
    }

    setPendingLeave(null);
  };

  const handleCancelLeave = () => {
    setPendingLeave(null);
    const cancelMsg: ChatMessage = {
      id: `ai-cancel-${Date.now()}`,
      role: "ai",
      content: "<p>好的，已取消。你可以重新告訴我想請什麼假，我來幫你重新整理 😊</p>",
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, cancelMsg]);
  };

  const userName = currentUser?.name || "使用者";

  return (
    <div className="chat-container">
      {/* 聊天標題 */}
      <div className="chat-header">
        <div className="ai-avatar">🤖</div>
        <div>
          <div className="ai-name">耐落 AI 請假助理</div>
          <div className="ai-status">
            <span className="ai-dot" />
            已連線 · 24/7 服務
          </div>
        </div>
      </div>

      {/* 訊息列表 */}
      <div className="chat-messages">
        {messages.map((msg) => (
          <ChatBubble
            key={msg.id}
            message={msg}
            userInitial={userName.charAt(0)}
            onConfirmLeave={handleConfirmLeave}
            onCancelLeave={handleCancelLeave}
          />
        ))}

        {isTyping && (
          <div className="chat-msg ai">
            <div className="msg-avatar">🤖</div>
            <div className="msg-bubble">
              <div className="typing-indicator">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 快速範例 */}
      {messages.length <= 1 && (
        <div className="chat-chips">
          {QUICK_CHIPS.map((chip, i) => (
            <button
              key={i}
              className="chat-chip"
              onClick={() => {
                setInput(chip.text);
                setTimeout(() => handleSend(), 50);
              }}
              onMouseDown={(e) => {
                e.preventDefault();
                setInput(chip.text);
              }}
              onMouseUp={() => {
                setTimeout(() => {
                  const fakeEvent = { ...chip };
                  setInput(fakeEvent.text);
                  setTimeout(handleSend, 50);
                }, 10);
              }}
            >
              {chip.icon} {chip.label}
            </button>
          ))}
        </div>
      )}

      {/* 輸入區 */}
      <div className="chat-input-area">
        <div className="chat-input-box">
          <input
            className="chat-input-field"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="告訴 AI 你想請什麼假…"
            disabled={isTyping}
          />
          <button
            className="chat-send-btn"
            onClick={handleSend}
            disabled={isTyping || !input.trim()}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>

      {/* 確認對話框 */}
      <ConfirmDialog
        open={showConfirm}
        title="確認送出請假單"
        message={`確定要送出 ${pendingLeave?.leave_name || ""} 請假申請嗎？送出後將由主管（${pendingLeave?.approver_name || ""}）進行簽核。`}
        confirmText="確認送出"
        cancelText="再想想"
        onConfirm={submitLeave}
        onCancel={() => setShowConfirm(false)}
      />
    </div>
  );
};

export default ChatPage;
"""

# ─────────────────────────────────────────────
# src/pages/RecordsPage.tsx
# ─────────────────────────────────────────────
RECORDS_PAGE_TSX = r"""import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AppHeader from "../components/AppHeader";
import StatusBadge from "../components/StatusBadge";
import { useCurrentUser } from "../components/AppLayout";
import type { LeaveRecord } from "../types";

const getApiBase = () => (window as any).__API_BASE__ || "/api/v1";
const getAppId = () => (window as any).__APP_ID__ || "";
const getToken = () => (window as any).__APP_TOKEN__ || "";

/** demo 資料 */
const DEMO_RECORDS: LeaveRecord[] = [
  { id: 1, employee_id: 1, leave_type_id: 3, leave_name: "病假", date_from: "2026-05-28", date_to: "2026-05-29", number_of_days: 2, hours: 16, reason: "感冒高燒", approval_status: "pending", approver_name: "李志明" },
  { id: 2, employee_id: 1, leave_type_id: 5, leave_name: "家庭照顧假", date_from: "2026-05-28", date_to: "2026-05-28", number_of_days: 0.5, hours: 4, reason: "女兒家長會", approval_status: "pending", approver_name: "李志明" },
  { id: 3, employee_id: 1, leave_type_id: 1, leave_name: "特別休假", date_from: "2026-05-30", date_to: "2026-06-01", number_of_days: 3, hours: 24, reason: "家庭旅遊", approval_status: "approved", approver_name: "李志明" },
  { id: 4, employee_id: 1, leave_type_id: 3, leave_name: "病假", date_from: "2026-05-16", date_to: "2026-05-16", number_of_days: 1, hours: 8, reason: "感冒", approval_status: "approved", approver_name: "李志明" },
  { id: 5, employee_id: 1, leave_type_id: 1, leave_name: "特別休假", date_from: "2026-05-06", date_to: "2026-05-06", number_of_days: 1, hours: 8, reason: "個人事務", approval_status: "approved", approver_name: "李志明" },
  { id: 6, employee_id: 1, leave_type_id: 2, leave_name: "事假", date_from: "2026-04-30", date_to: "2026-04-30", number_of_days: 0.5, hours: 4, reason: "個人事務", approval_status: "approved", approver_name: "李志明" },
  { id: 7, employee_id: 1, leave_type_id: 3, leave_name: "病假", date_from: "2026-04-22", date_to: "2026-04-23", number_of_days: 2, hours: 16, reason: "身體不適", approval_status: "rejected", approver_name: "李志明" },
  { id: 8, employee_id: 1, leave_type_id: 1, leave_name: "特別休假", date_from: "2026-04-15", date_to: "2026-04-15", number_of_days: 1, hours: 8, reason: "清明後補休", approval_status: "approved", approver_name: "李志明" },
  { id: 9, employee_id: 1, leave_type_id: 5, leave_name: "家庭照顧假", date_from: "2026-03-29", date_to: "2026-03-29", number_of_days: 1, hours: 8, reason: "媽媽就醫陪同", approval_status: "approved", approver_name: "李志明" },
  { id: 10, employee_id: 1, leave_type_id: 1, leave_name: "特別休假", date_from: "2026-03-15", date_to: "2026-03-15", number_of_days: 1, hours: 8, reason: "到職滿年休", approval_status: "approved", approver_name: "李志明" },
];

const RecordsPage: React.FC = () => {
  const navigate = useNavigate();
  const { currentUser } = useCurrentUser();
  const [records, setRecords] = useState<LeaveRecord[]>(DEMO_RECORDS);
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    const loadRecords = async () => {
      const apiBase = getApiBase();
      const appId = getAppId();
      const token = getToken();
      try {
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const resp = await fetch(`${apiBase}/proxy/${appId}/hr_leaves`, {
          headers,
          credentials: "include",
        });
        if (resp.ok) {
          const result = await resp.json();
          const data = result?.data || result || [];
          if (data.length > 0) {
            const filtered = currentUser
              ? data.filter((r: LeaveRecord) => r.employee_id === currentUser.id)
              : data;
            if (filtered.length > 0) setRecords(filtered);
          }
        }
      } catch {
        /* 使用 demo 資料 */
      }
    };
    loadRecords();
  }, [currentUser]);

  const filtered = records.filter((r) => {
    if (statusFilter !== "all" && r.approval_status !== statusFilter) return false;
    if (typeFilter !== "all" && r.leave_name !== typeFilter) return false;
    return true;
  });

  const totalCount = records.length;
  const pendingCount = records.filter((r) => r.approval_status === "pending").length;
  const approvedCount = records.filter((r) => r.approval_status === "approved").length;
  const rejectedCount = records.filter((r) => r.approval_status === "rejected").length;
  const totalHours = records.reduce((s, r) => s + (r.hours || r.number_of_days * 8), 0);
  const leaveTypes = Array.from(new Set(records.map((r) => r.leave_name).filter(Boolean)));

  return (
    <>
      <AppHeader
        title="📋 我的請假紀錄"
        subtitle={`2026 年度 · 共 ${totalCount} 筆申請`}
        actions={
          <button
            className="btn-primary"
            style={{ padding: "9px 14px", borderRadius: "8px", fontSize: "13px" }}
            onClick={() => navigate("/chat")}
          >
            ＋ 新增請假
          </button>
        }
      />
      <div className="page-container">
        {/* KPI */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-icon blue">📋</div>
            <div className="kpi-label">本年度申請</div>
            <div className="kpi-value">{totalCount} 件</div>
            <div className="kpi-meta">總時數 {totalHours} hr</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon orange">⏳</div>
            <div className="kpi-label">待主管核</div>
            <div className="kpi-value" style={{ color: "var(--warning)" }}>{pendingCount} 件</div>
            <div className="kpi-meta">等待簽核中</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon green">✅</div>
            <div className="kpi-label">已核准</div>
            <div className="kpi-value" style={{ color: "var(--success)" }}>{approvedCount} 件</div>
            <div className="kpi-meta">通過率 {totalCount > 0 ? Math.round((approvedCount / totalCount) * 100) : 0}%</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon red">❌</div>
            <div className="kpi-label">已退回</div>
            <div className="kpi-value">{rejectedCount} 件</div>
            <div className="kpi-meta">{rejectedCount > 0 ? "需補件或修改" : "無退回"}</div>
          </div>
        </div>

        {/* 篩選 + 表格 */}
        <div className="panel">
          <div className="filter-row">
            <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
              <option value="all">所有假別</option>
              {leaveTypes.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="all">所有狀態</option>
              <option value="pending">待簽核</option>
              <option value="approved">已核准</option>
              <option value="rejected">已退回</option>
            </select>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>假別</th>
                <th>期間</th>
                <th>時數</th>
                <th>事由</th>
                <th>核決主管</th>
                <th>狀態</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id}>
                  <td>{r.date_from}</td>
                  <td>{r.leave_name}</td>
                  <td>{r.date_from === r.date_to ? r.date_from.slice(5) : `${r.date_from.slice(5)} ~ ${r.date_to.slice(5)}`}</td>
                  <td>{r.hours || r.number_of_days * 8} hr</td>
                  <td>{r.reason}</td>
                  <td>{r.approver_name || "—"}</td>
                  <td><StatusBadge status={r.approval_status || "draft"} /></td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", color: "var(--text-muted)", padding: "40px" }}>
                    暫無符合條件的紀錄
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
};

export default RecordsPage;
"""

# ─────────────────────────────────────────────
# src/pages/AttendancePage.tsx
# ─────────────────────────────────────────────
ATTENDANCE_PAGE_TSX = r"""import React, { useState, useEffect, useCallback } from "react";
import toast from "react-hot-toast";
import AppHeader from "../components/AppHeader";
import ConfirmDialog from "../components/ConfirmDialog";
import { useCurrentUser } from "../components/AppLayout";

/** demo 打卡紀錄 */
const DEMO_ATTENDANCE = [
  { date: "05/30", weekday: "五", clockIn: "—", clockOut: "—", hours: "—", abnormal: "—", note: "今日", isToday: true },
  { date: "05/29", weekday: "四", clockIn: "09:02", clockOut: "18:15", hours: "8.2", abnormal: "—", note: "" },
  { date: "05/28", weekday: "三", clockIn: "—", clockOut: "—", hours: "—", abnormal: "—", note: "病假" },
  { date: "05/27", weekday: "二", clockIn: "08:55", clockOut: "18:32", hours: "8.6", abnormal: "—", note: "加班 0.5hr" },
  { date: "05/26", weekday: "一", clockIn: "09:08", clockOut: "18:05", hours: "7.9", abnormal: "—", note: "" },
  { date: "05/23", weekday: "五", clockIn: "08:50", clockOut: "17:55", hours: "8.1", abnormal: "—", note: "" },
  { date: "05/22", weekday: "四", clockIn: "09:00", clockOut: "18:00", hours: "8.0", abnormal: "—", note: "" },
];

const AttendancePage: React.FC = () => {
  const { currentUser } = useCurrentUser();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [clockedIn, setClockedIn] = useState(false);
  const [clockInTime, setClockInTime] = useState<string | null>(null);
  const [showPunchConfirm, setShowPunchConfirm] = useState(false);
  const [punchAction, setPunchAction] = useState<"in" | "out">("in");

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = useCallback((d: Date) => {
    return d.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
  }, []);

  const formatDate = useCallback((d: Date) => {
    const weekdays = ["日", "一", "二", "三", "四", "五", "六"];
    return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}（${weekdays[d.getDay()]}）`;
  }, []);

  const getWorkedTime = () => {
    if (!clockInTime) return "0 hr 0 min";
    const [h, m] = clockInTime.split(":").map(Number);
    const now = currentTime;
    let diffMin = (now.getHours() * 60 + now.getMinutes()) - (h * 60 + m);
    if (diffMin < 0) diffMin = 0;
    /* 扣除午休 1 小時 */
    if (now.getHours() >= 13 && h < 13) diffMin -= 60;
    if (diffMin < 0) diffMin = 0;
    const hr = Math.floor(diffMin / 60);
    const min = diffMin % 60;
    return `${hr} hr ${min} min`;
  };

  const handlePunch = (action: "in" | "out") => {
    setPunchAction(action);
    setShowPunchConfirm(true);
  };

  const confirmPunch = () => {
    setShowPunchConfirm(false);
    const timeStr = formatTime(currentTime).slice(0, 5);
    if (punchAction === "in") {
      setClockedIn(true);
      setClockInTime(timeStr);
      toast.success(`✅ 上班打卡成功：${timeStr}`);
    } else {
      setClockedIn(false);
      toast.success(`✅ 下班打卡成功：${timeStr}`);
    }
  };

  return (
    <>
      <AppHeader
        title="🗓️ 出勤打卡"
        subtitle={`${formatDate(currentTime)} · 即時打卡`}
      />
      <div className="page-container">
        {/* 打卡英雄區 */}
        <div className="attendance-hero">
          <div className="att-hero-row">
            <div className="att-hero-info">
              <div className="att-hero-label">今日狀態</div>
              <div className="att-hero-time">{formatTime(currentTime)}</div>
              <div className="att-hero-status">
                {clockedIn
                  ? `已上班 · 上午 ${clockInTime} 打卡 · 工時 ${getWorkedTime()}`
                  : "尚未打卡"}
              </div>
            </div>
            {!clockedIn ? (
              <button className="punch-button" onClick={() => handlePunch("in")}>
                🟢 打上班卡
              </button>
            ) : (
              <button className="punch-button out" onClick={() => handlePunch("out")}>
                🔴 打下班卡
              </button>
            )}
          </div>
          <div className="att-hero-stats">
            <div>
              <div className="att-stat-label">上班打卡</div>
              <div className="att-stat-value">{clockInTime || "—"}</div>
            </div>
            <div>
              <div className="att-stat-label">午休</div>
              <div className="att-stat-value">12:30 - 13:30</div>
            </div>
            <div>
              <div className="att-stat-label">預計下班</div>
              <div className="att-stat-value">18:00</div>
            </div>
            <div>
              <div className="att-stat-label">本月遲到</div>
              <div className="att-stat-value">0 次</div>
            </div>
          </div>
        </div>

        {/* KPI */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-icon blue">📆</div>
            <div className="kpi-label">本月應出勤</div>
            <div className="kpi-value">21 / 22 天</div>
            <div className="kpi-meta">出勤率 95.5%</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon green">⏰</div>
            <div className="kpi-label">本月總工時</div>
            <div className="kpi-value">176.5 hr</div>
            <div className="kpi-meta">加班 8.5 hr</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon orange">⚠️</div>
            <div className="kpi-label">異常打卡</div>
            <div className="kpi-value">1 次</div>
            <div className="kpi-meta">5/15 忘打卡（已補）</div>
          </div>
          <div className="kpi-card">
            <div className="kpi-icon purple">🔄</div>
            <div className="kpi-label">可用補休</div>
            <div className="kpi-value">12 hr</div>
            <div className="kpi-meta">由加班 8.5 hr 換</div>
          </div>
        </div>

        {/* 7 日紀錄 */}
        <div className="panel">
          <div className="panel-header">
            <div>
              <div className="panel-title">📅 最近 7 天打卡紀錄</div>
              <div className="panel-subtitle">5/22 - 5/30</div>
            </div>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>日期</th>
                <th>星期</th>
                <th>上班</th>
                <th>下班</th>
                <th>工時</th>
                <th>異常</th>
                <th>備註</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_ATTENDANCE.map((row, i) => (
                <tr key={i} style={row.isToday ? { background: "#eef2ff" } : undefined}>
                  <td><strong>{row.date}</strong></td>
                  <td>{row.weekday}</td>
                  <td>{row.isToday && clockedIn ? clockInTime : row.clockIn}</td>
                  <td>{row.clockOut}</td>
                  <td>{row.isToday && clockedIn ? "進行中" : row.hours}</td>
                  <td>{row.abnormal}</td>
                  <td>
                    {row.isToday ? (
                      <span className="status-badge draft">今日</span>
                    ) : row.note === "病假" ? (
                      <span className="status-badge pending">{row.note}</span>
                    ) : (
                      row.note || "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <ConfirmDialog
        open={showPunchConfirm}
        title={punchAction === "in" ? "確認打上班卡" : "確認打下班卡"}
        message={
          punchAction === "in"
            ? `確定要在 ${formatTime(currentTime).slice(0, 5)} 打上班卡嗎？`
            : `確定要在 ${formatTime(currentTime).slice(0, 5)} 打下班卡嗎？`
        }
        confirmText="確認打卡"
        onConfirm={confirmPunch}
        onCancel={() => setShowPunchConfirm(false)}
      />
    </>
  );
};

export default AttendancePage;
"""

# ─────────────────────────────────────────────
# src/pages/BalancePage.tsx
# ─────────────────────────────────────────────
BALANCE_PAGE_TSX = r"""import React, { useState, useEffect } from "react";
import AppHeader from "../components/AppHeader";
import { useCurrentUser } from "../components/AppLayout";

const getApiBase = () => (window as any).__API_BASE__ || "/api/v1";
const getAppId = () => (window as any).__APP_ID__ || "";
const getToken = () => (window as any).__APP_TOKEN__ || "";

interface BalanceItem {
  icon: string;
  name: string;
  meta: string;
  total: number;
  used: number;
  unit: string;
  color: string;
  isSpecial?: boolean;
  specialLabel?: string;
}

const DEMO_BALANCES: BalanceItem[] = [
  { icon: "🌴", name: "特別休假", meta: "薪資照給 · 不需證明", total: 14, used: 3, unit: "日", color: "#16a34a" },
  { icon: "📝", name: "事假", meta: "不給薪 · 業務人員不扣", total: 14, used: 3, unit: "日", color: "#94a3b8" },
  { icon: "🤒", name: "病假（未住院）", meta: "30日內薪資減半 · 業務不扣", total: 30, used: 1, unit: "日", color: "#ea580c" },
  { icon: "👨‍👩‍👧", name: "家庭照顧假", meta: "併入事假 · 不給薪", total: 7, used: 0, unit: "日", color: "#7c3aed" },
  { icon: "🔄", name: "補休", meta: "由加班時數轉換", total: 20, used: 8, unit: "小時", color: "#0891b2" },
  { icon: "🩸", name: "生理假", meta: "薪資減半 · 3日內不併病假", total: 12, used: 0, unit: "日", color: "#e11d48" },
];

const SPECIAL_LEAVES: BalanceItem[] = [
  { icon: "💍", name: "婚假", meta: "薪資照給 · 結婚前10日起3個月內請畢", total: 8, used: 0, unit: "日", color: "#d97706", isSpecial: true, specialLabel: "給假 8 日" },
  { icon: "🕊️", name: "喪假", meta: "薪資照給 · 100日內請畢", total: 8, used: 0, unit: "日", color: "#374151", isSpecial: true, specialLabel: "3-8 日（依親等）" },
  { icon: "👶", name: "陪產（檢）假", meta: "薪資照給", total: 7, used: 0, unit: "日", color: "#2563eb", isSpecial: true, specialLabel: "給假 7 日" },
  { icon: "🪖", name: "公假", meta: "薪資照給 · 兵役/選舉/政府調訓", total: 0, used: 0, unit: "日", color: "#0369a1", isSpecial: true, specialLabel: "依事由" },
  { icon: "🤕", name: "公傷假", meta: "薪資照給 · 執行公務致傷", total: 0, used: 0, unit: "日", color: "#991b1b", isSpecial: true, specialLabel: "最長 2 年" },
  { icon: "🌪️", name: "天然災害假", meta: "不給薪 · 依政府公告", total: 0, used: 0, unit: "日", color: "#6b7280", isSpecial: true, specialLabel: "依公告" },
];

const BalancePage: React.FC = () => {
  const { currentUser } = useCurrentUser();
  const [balances, setBalances] = useState(DEMO_BALANCES);
  const userName = currentUser?.name || "張文武";
  const deptName = currentUser?.custom_data?.dept_name || "業務部";
  const rank = currentUser?.custom_data?.rank || "五職等";
  const hireDate = currentUser?.custom_data?.hire_date || "2022-03-15";

  /* 計算年資 */
  const calcSeniority = () => {
    const hire = new Date(hireDate);
    const now = new Date();
    let years = now.getFullYear() - hire.getFullYear();
    let months = now.getMonth() - hire.getMonth();
    if (months < 0) { years--; months += 12; }
    return `${years} 年 ${months} 月`;
  };

  useEffect(() => {
    const loadBalances = async () => {
      const apiBase = getApiBase();
      const appId = getAppId();
      const token = getToken();
      try {
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const resp = await fetch(`${apiBase}/proxy/${appId}/hr_leave_allocations`, {
          headers,
          credentials: "include",
        });
        if (resp.ok) {
          const result = await resp.json();
          const data = result?.data || result || [];
          if (data.length > 0) {
            /* 有真實資料，可進一步對應 */
          }
        }
      } catch {
        /* 使用 demo */
      }
    };
    loadBalances();
  }, []);

  return (
    <>
      <AppHeader
        title="📊 我的假期額度"
        subtitle="2026 年度 · 即時同步"
        actions={<span className="status-badge approved">業務人員 · 不扣薪資格</span>}
      />
      <div className="page-container">
        {/* 員工資訊卡 */}
        <div className="panel" style={{ background: "linear-gradient(135deg, var(--primary-light), var(--accent-light))", borderColor: "#a5b4fc" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
            <div style={{ width: 56, height: 56, background: "var(--gradient)", borderRadius: 14, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28, color: "white" }}>👤</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 17, fontWeight: 700 }}>{userName}</div>
              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>
                {deptName} · {rank} · 到職 {hireDate} · 年資 <strong>{calcSeniority()}</strong>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)" }}>下個年資跳級</div>
              <div style={{ fontSize: 13, fontWeight: 700 }}>2027/03/15 → 特休升至 15 日</div>
            </div>
          </div>
        </div>

        {/* 一般假期 */}
        <div style={{ fontSize: 14, fontWeight: 700, margin: "20px 0 12px", color: "var(--text-secondary)" }}>📅 一般假期額度</div>
        <div className="balance-grid">
          {balances.map((b, i) => {
            const remaining = b.total - b.used;
            const pct = b.total > 0 ? Math.round((b.used / b.total) * 100) : 0;
            return (
              <div key={i} className="balance-card">
                <div className="balance-card-head">
                  <div className="balance-card-icon">{b.icon}</div>
                  <div>
                    <div className="balance-card-name">{b.name}</div>
                    <div className="balance-card-meta">{b.meta}</div>
                  </div>
                </div>
                <div className="balance-bar">
                  <div className="balance-bar-fill" style={{ width: `${pct}%`, background: b.color }} />
                </div>
                <div className="balance-stats">
                  <span className="stat-label">已用 {b.used} {b.unit}</span>
                  <span className="stat-value" style={{ color: b.color }}>剩餘 {remaining} {b.unit}</span>
                </div>
                {b.name === "特別休假" && (
                  <div className="warning-box" style={{ marginTop: 10 }}>
                    ⚠️ 提醒：5 日將於 12/31 過期，記得安排
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* 特殊假別 */}
        <div style={{ fontSize: 14, fontWeight: 700, margin: "24px 0 12px", color: "var(--text-secondary)" }}>💝 特殊假別（依事由申請）</div>
        <div className="balance-grid">
          {SPECIAL_LEAVES.map((b, i) => (
            <div key={i} className="balance-card">
              <div className="balance-card-head">
                <div className="balance-card-icon">{b.icon}</div>
                <div>
                  <div className="balance-card-name">{b.name}</div>
                  <div className="balance-card-meta">{b.meta}</div>
                </div>
              </div>
              <div className="balance-stats" style={{ marginTop: 8 }}>
                <span className="stat-label">給假天數</span>
                <span className="stat-value">{b.specialLabel}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

export default BalancePage;
"""

# ─────────────────────────────────────────────
# src/pages/PolicyPage.tsx
# ─────────────────────────────────────────────
POLICY_PAGE_TSX = r"""import React, { useState, useEffect } from "react";
import AppHeader from "../components/AppHeader";
import { LEAVE_TYPES } from "../constants";

const getApiBase = () => (window as any).__API_BASE__ || "/api/v1";
const getAppId = () => (window as any).__APP_ID__ || "";
const getToken = () => (window as any).__APP_TOKEN__ || "";

const PolicyPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterMode, setFilterMode] = useState<"all" | "paid" | "doc">("all");

  useEffect(() => {
    /* 嘗試從 hr_leave_types 讀取 */
    const loadTypes = async () => {
      const apiBase = getApiBase();
      const appId = getAppId();
      const token = getToken();
      try {
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;
        await fetch(`${apiBase}/proxy/${appId}/hr_leave_types`, {
          headers,
          credentials: "include",
        });
        /* 若成功可替換常數，這裡預設用 LEAVE_TYPES */
      } catch {
        /* 使用常數 */
      }
    };
    loadTypes();
  }, []);

  const filtered = LEAVE_TYPES.filter((lt) => {
    if (searchTerm && !lt.name.includes(searchTerm) && !lt.payRule.includes(searchTerm) && !lt.description.includes(searchTerm)) return false;
    if (filterMode === "paid" && !lt.payRule.includes("照給")) return false;
    if (filterMode === "doc" && lt.docRequired === "不需要") return false;
    return true;
  });

  return (
    <>
      <AppHeader
        title="📖 請假規範說明"
        subtitle="HR-TW-P-001-33 · 適用台灣廠區全體員工"
      />
      <div className="page-container">
        {/* 篩選 */}
        <div className="filter-row">
          <input
            type="search"
            placeholder="🔍 搜尋假別、規定..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1, minWidth: 240 }}
          />
          <button
            className={`filter-btn${filterMode === "all" ? " active" : ""}`}
            onClick={() => setFilterMode("all")}
          >
            全部
          </button>
          <button
            className={`filter-btn${filterMode === "paid" ? " active" : ""}`}
            onClick={() => setFilterMode("paid")}
          >
            薪資照給
          </button>
          <button
            className={`filter-btn${filterMode === "doc" ? " active" : ""}`}
            onClick={() => setFilterMode("doc")}
          >
            需證明文件
          </button>
        </div>

        {/* 假別卡片 */}
        <div className="policy-grid">
          {filtered.map((lt) => {
            const payTag = lt.payRule.includes("照給")
              ? { bg: "#dcfce7", color: "#15803d", text: "照給薪" }
              : lt.payRule.includes("減半")
              ? { bg: "#fef3c7", color: "#b45309", text: "減半薪" }
              : { bg: "#f1f5f9", color: "#475569", text: "不給薪" };

            return (
              <div key={lt.code} className="policy-card">
                <div className="policy-head">
                  <div className="policy-icon">{lt.icon}</div>
                  <div className="policy-name">{lt.name}</div>
                  <span className="policy-tag" style={{ background: payTag.bg, color: payTag.color }}>
                    {payTag.text}
                  </span>
                </div>
                <div className="policy-rules">
                  <span className="rule-label">給假</span>
                  <span className="rule-value">{lt.maxDays}</span>
                  <span className="rule-label">最小</span>
                  <span className="rule-value">{lt.minUnit}</span>
                  <span className="rule-label">證明</span>
                  <span className="rule-value">{lt.docRequired}</span>
                  <span className="rule-label">薪資</span>
                  <span className="rule-value">{lt.payRule}</span>
                </div>
                <div className="policy-body">{lt.description}</div>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div style={{ gridColumn: "1/-1", textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
              找不到符合條件的假別
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default PolicyPage;
"""

# ─────────────────────────────────────────────
# src/pages/AgentsPage.tsx
# ─────────────────────────────────────────────
AGENTS_PAGE_TSX = r"""import React, { useState } from "react";
import AppHeader from "../components/AppHeader";
import { useCurrentUser } from "../components/AppLayout";

interface AgentInfo {
  id: number;
  name: string;
  dept: string;
  role: string;
  type: "primary" | "secondary";
  color: string;
}

const DEMO_AGENTS: AgentInfo[] = [
  { id: 2, name: "王小明", dept: "業務部", role: "業務專員", type: "primary", color: "#6366f1" },
  { id: 3, name: "林美玲", dept: "業務部", role: "業務助理", type: "secondary", color: "#8b5cf6" },
];

const DEMO_DELEGATED: AgentInfo[] = [
  { id: 5, name: "陳大華", dept: "生產部", role: "生產組長", type: "primary", color: "#0891b2" },
];

const AgentsPage: React.FC = () => {
  const { currentUser } = useCurrentUser();
  const [agents] = useState(DEMO_AGENTS);
  const [delegated] = useState(DEMO_DELEGATED);

  const userName = currentUser?.name || "張文武";

  return (
    <>
      <AppHeader
        title="👥 我的代理人"
        subtitle="管理您的職務代理人設定"
      />
      <div className="page-container">
        {/* 代理人說明 */}
        <div className="info-box" style={{ marginBottom: 20 }}>
          💡 <strong>代理人功能：</strong>當您請假時，代理人會代為處理您的業務與簽核工作。建議設定主、副代理人各一位，確保業務不中斷。
        </div>

        {/* 我的代理人 */}
        <div style={{ fontSize: 14, fontWeight: 700, margin: "0 0 12px", color: "var(--text-secondary)" }}>
          🎯 我的代理人（{userName} 請假時由以下人員代理）
        </div>
        {agents.map((agent) => (
          <div key={agent.id} className="agent-card">
            <div className="agent-avatar" style={{ background: `linear-gradient(135deg, ${agent.color}, ${agent.color}dd)` }}>
              {agent.name.charAt(0)}
            </div>
            <div>
              <div className="agent-name">{agent.name}</div>
              <div className="agent-role">{agent.dept} · {agent.role}</div>
              <div style={{ marginTop: 6 }}>
                <span
                  className="agent-tag"
                  style={{
                    background: agent.type === "primary" ? "var(--primary-light)" : "var(--accent-light)",
                    color: agent.type === "primary" ? "var(--primary)" : "var(--accent)",
                  }}
                >
                  {agent.type === "primary" ? "主代理人" : "副代理人"}
                </span>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <span className="status-badge approved">生效中</span>
            </div>
          </div>
        ))}

        {/* 我代理的同事 */}
        <div style={{ fontSize: 14, fontWeight: 700, margin: "28px 0 12px", color: "var(--text-secondary)" }}>
          🤝 我代理的同事（以下同事請假時由 {userName} 代理）
        </div>
        {delegated.map((agent) => (
          <div key={agent.id} className="agent-card">
            <div className="agent-avatar" style={{ background: `linear-gradient(135deg, ${agent.color}, ${agent.color}dd)` }}>
              {agent.name.charAt(0)}
            </div>
            <div>
              <div className="agent-name">{agent.name}</div>
              <div className="agent-role">{agent.dept} · {agent.role}</div>
              <div style={{ marginTop: 6 }}>
                <span className="agent-tag" style={{ background: "#e0f2fe", color: "#0369a1" }}>
                  主代理人（對方設定）
                </span>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <span className="status-badge approved">生效中</span>
            </div>
          </div>
        ))}

        {delegated.length === 0 && (
          <div className="panel" style={{ textAlign: "center", color: "var(--text-muted)", padding: 30 }}>
            目前沒有代理其他同事
          </div>
        )}

        {/* 設定提醒 */}
        <div className="warning-box" style={{ marginTop: 20 }}>
          ⚠️ <strong>提醒：</strong>代理人的變更需要經過部門主管核准。如需修改代理人設定，請至 HR 系統提出申請或聯繫人資部門。
        </div>
      </div>
    </>
  );
};

export default AgentsPage;
"""

# ─────────────────────────────────────────────
# actions/manifest.json
# ─────────────────────────────────────────────
ACTIONS_MANIFEST = """{
  "actions": [
    {
      "id": "ai_leave_chat",
      "name": "AI 請假對話",
      "description": "透過 LLM 協助員工完成請假申請",
      "entry": "ai_leave_chat.py",
      "method": "POST"
    }
  ]
}"""

# ─────────────────────────────────────────────
# actions/ai_leave_chat.py
# ─────────────────────────────────────────────
AI_LEAVE_CHAT_PY = r'''"""
AI 請假對話 Server-Side Action
透過 OpenAI Chat API 與員工進行對話式請假
"""
import json
from datetime import datetime, timedelta


SYSTEM_PROMPT = """你是耐落集團（NYLOK）的 AI 請假助理，專門協助員工處理請假相關事務。

## 你的職責
1. 理解員工的請假需求
2. 檢查假別規則與額度
3. 提醒需要的證明文件
4. 計算薪資影響
5. 產出結構化的請假單資料

## 請假規則（HR-TW-P-001-33 台灣廠區）
- 特別休假：依年資 3-30 日，薪資照給，不需證明
- 事假：全年 14 日，不給薪（業務人員不扣），不需證明
- 病假（未住院）：30 日，薪資減半（業務不扣），1天以上需診斷書
- 病假（住院）：含未住院合計 1 年，需住院證明
- 家庭照顧假：7 日，併入事假，不需證明
- 補休：依加班時數，6 個月內請畢
- 生理假：每月 1 日，薪資減半，3日內不併病假
- 婚假：8 日，薪資照給，需結婚證書
- 喪假：3-8 日依親等，薪資照給，需訃聞
- 產假：8 週，任職≥6月照給
- 陪產假：7 日，薪資照給，需出生證明
- 公假：依事由，薪資照給，需公文
- 公傷假：最長 2 年，薪資照給，需診斷書+事故報告
- 天然災害假：依公告，不給薪不扣全勤
- 疫苗接種假：依接種次數，不給薪不扣全勤
- 原住民族假：1 日，薪資照給，需戶籍資料
- 志工假：依服勤時數，薪資照給，需志工服務證明

## 不扣薪資格
業務人員（is_sales=true）：事假/病假 30 日內不扣薪

## 回覆格式
請以 JSON 格式回覆：
{
  "reply": "你的回覆內容（HTML 格式）",
  "leave_data": {
    "leave_type_id": 假別ID,
    "leave_name": "假別名稱",
    "date_from": "YYYY-MM-DD",
    "date_to": "YYYY-MM-DD",
    "number_of_days": 天數,
    "hours": 時數,
    "reason": "請假事由",
    "pay_impact": "薪資影響",
    "doc_status": "證明文件狀態"
  }
}

如果員工只是詢問（非申請），leave_data 可以為 null。
回覆內容請用 HTML 標籤格式化（<p>, <ul>, <li>, <strong> 等）。
"""


async def handler(ctx):
    """處理 AI 請假對話"""
    body = ctx.request.json()
    message = body.get("message", "")
    employee = body.get("employee", {})
    history = body.get("history", [])

    # 嘗試使用 OpenAI API
    api_key = None
    try:
        api_key = ctx.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass

    if api_key:
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # 加入員工資訊
            emp_info = f"員工：{employee.get('name', '未知')}，部門：{employee.get('custom_data', {}).get('dept_name', '未知')}，職等：{employee.get('custom_data', {}).get('rank', '未知')}，業務人員：{'是' if employee.get('custom_data', {}).get('is_sales') else '否'}，到職日：{employee.get('custom_data', {}).get('hire_date', '未知')}"
            messages.append({"role": "system", "content": f"當前員工資訊：{emp_info}\n今天日期：{datetime.now().strftime('%Y-%m-%d')}"})

            # 加入歷史對話
            for h in history[-6:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

            messages.append({"role": "user", "content": message})

            response = await ctx.http.call(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                body=json.dumps({
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1500,
                    "response_format": {"type": "json_object"},
                }),
            )

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            return {
                "reply": parsed.get("reply", "好的，我來幫你處理。"),
                "leave_data": parsed.get("leave_data"),
            }
        except Exception as e:
            # OpenAI 呼叫失敗，回退到規則式回覆
            pass

    # 規則式回覆（離線模式）
    return generate_rule_based_reply(message, employee)


def generate_rule_based_reply(message, employee):
    """基於規則的回覆生成"""
    name = employee.get("name", "同仁")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    if "特休" in message and ("20" in message or "二十" in message):
        return {
            "reply": f"<p>{name}，你目前特休剩餘 <strong>11 日</strong>，無法一次請 20 天。</p><p>建議分次請休或搭配事假。</p>",
            "leave_data": None,
        }

    if "颱風" in message:
        return {
            "reply": "<p>颱風天處理方式：</p><ul><li>🌪️ 政府宣布停班停課，公司跟進</li><li>📢 HR 會提前通知</li></ul>",
            "leave_data": None,
        }

    if "病假" in message:
        days = 2 if ("兩天" in message or "2天" in message or "2 天" in message) else 1
        return {
            "reply": f"<p>好的 {name}，已為你準備病假申請。</p>",
            "leave_data": {
                "leave_type_id": 3,
                "leave_name": "病假",
                "date_from": tomorrow,
                "date_to": tomorrow,
                "number_of_days": days,
                "hours": days * 8,
                "reason": "身體不適",
                "pay_impact": "業務人員不扣薪",
                "doc_status": "需附診斷書" if days > 1 else "免附",
            },
        }

    # 預設特休回覆
    return {
        "reply": f"<p>好的 {name}，已為你準備特休申請。</p>",
        "leave_data": {
            "leave_type_id": 1,
            "leave_name": "特別休假",
            "date_from": tomorrow,
            "date_to": tomorrow,
            "number_of_days": 1,
            "hours": 8,
            "reason": "個人事務",
            "pay_impact": "薪資照給",
            "doc_status": "免附",
        },
    }
'''

# ============================================================
# 組裝 VFS
# ============================================================

def build_vfs() -> dict:
    """組裝所有 VFS 檔案"""
    return {
        "package.json": PACKAGE_JSON,
        "src/main.tsx": MAIN_TSX,
        "src/App.tsx": APP_TSX,
        "src/App.css": APP_CSS,
        "src/routes.ts": ROUTES_TS,
        "src/constants.ts": CONSTANTS_TS,
        "src/types.ts": TYPES_TS,
        "src/components/AppLayout.tsx": APP_LAYOUT_TSX,
        "src/components/AppSidebar.tsx": APP_SIDEBAR_TSX,
        "src/components/AppHeader.tsx": APP_HEADER_TSX,
        "src/components/LeaveCard.tsx": LEAVE_CARD_TSX,
        "src/components/StatusBadge.tsx": STATUS_BADGE_TSX,
        "src/components/ChatBubble.tsx": CHAT_BUBBLE_TSX,
        "src/components/ConfirmDialog.tsx": CONFIRM_DIALOG_TSX,
        "src/pages/_manifest.json": PAGES_MANIFEST,
        "src/pages/NotFoundPage.tsx": NOT_FOUND_PAGE_TSX,
        "src/pages/ChatPage.tsx": CHAT_PAGE_TSX,
        "src/pages/RecordsPage.tsx": RECORDS_PAGE_TSX,
        "src/pages/AttendancePage.tsx": ATTENDANCE_PAGE_TSX,
        "src/pages/BalancePage.tsx": BALANCE_PAGE_TSX,
        "src/pages/PolicyPage.tsx": POLICY_PAGE_TSX,
        "src/pages/AgentsPage.tsx": AGENTS_PAGE_TSX,
        "actions/manifest.json": ACTIONS_MANIFEST,
        "actions/ai_leave_chat.py": AI_LEAVE_CHAT_PY,
    }


# ============================================================
# 主流程
# ============================================================

def main():
    session = requests.Session()

    # ─── 1. 登入 ────────────────────────────
    print("🔐 登入 AI GO...")
    login_resp = session.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
    )

    if login_resp.status_code != 200:
        print(f"❌ 登入失敗: {login_resp.status_code}")
        print(login_resp.text[:500])
        sys.exit(1)

    login_data = login_resp.json()
    token = login_data.get("token") or login_data.get("access_token") or ""

    # 嘗試從 cookies 或回應中取得 token
    if not token:
        for key in ["jwt", "session", "auth_token"]:
            token = login_data.get(key, "")
            if token:
                break

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print(f"   ✅ 登入成功（token: {token[:20]}...）" if token else "   ✅ 登入成功（使用 session cookie）")

    # ─── 2. 取得現有 App 的 vfs_version ────
    print(f"\n📦 取得 App 資訊 ({APP_ID[:8]}...)...")
    app_resp = session.get(
        f"{BASE_URL}/api/v1/builder/apps/{APP_ID}",
        headers=headers,
    )

    if app_resp.status_code != 200:
        print(f"❌ 取得 App 失敗: {app_resp.status_code}")
        print(app_resp.text[:500])
        sys.exit(1)

    app_data = app_resp.json()
    vfs_version = app_data.get("vfs_version", 0)
    print(f"   ✅ 當前 vfs_version: {vfs_version}")

    # ─── 3. 建構 VFS 並 PATCH ──────────────
    # 使用正確的端點：PATCH /api/v1/builder/apps/{id}/source/files
    # Body 格式：{"files": {"path": "content"}, "expected_version": N}
    vfs = build_vfs()
    slug = app_data.get("slug", "")

    print(f"\n📝 注入 VFS ({len(vfs)} 個檔案)...")
    for f in sorted(vfs.keys()):
        print(f"   📄 {f} ({len(vfs[f])} bytes)")

    patch_body = {
        "files": vfs,
        "expected_version": vfs_version,
    }

    patch_resp = session.patch(
        f"{BASE_URL}/api/v1/builder/apps/{APP_ID}/source/files",
        headers=headers,
        json=patch_body,
    )

    if patch_resp.status_code not in (200, 201, 204):
        print(f"\n❌ PATCH 失敗: {patch_resp.status_code}")
        print(patch_resp.text[:1000])
        # 若 PATCH 失敗，嘗試 PUT 全量覆寫
        print("\n🔄 嘗試 PUT 全量覆寫...")
        existing_vfs = app_data.get("vfs_state", {})
        merged_vfs = {**existing_vfs, **vfs}
        put_resp = session.put(
            f"{BASE_URL}/api/v1/builder/apps/{APP_ID}/source",
            headers=headers,
            json={"files": merged_vfs, "expected_version": vfs_version},
        )
        if put_resp.status_code not in (200, 201, 204):
            print(f"❌ PUT 也失敗: {put_resp.status_code}")
            print(put_resp.text[:1000])
            sys.exit(1)
        patch_resp = put_resp

    print("   ✅ VFS 注入成功！")

    # 更新 vfs_version
    try:
        patch_data = patch_resp.json()
        new_version = patch_data.get("vfs_version", vfs_version + 1)
    except Exception:
        new_version = vfs_version + 1
    print(f"   📌 新 vfs_version: {new_version}")

    # ─── 4. 編譯 ───────────────────────────
    # 正確端點：POST /api/v1/compile/compile/{slug}?dev=true
    print(f"\n🔨 編譯中 (dev=true, slug={slug})...")
    compile_resp = session.post(
        f"{BASE_URL}/api/v1/compile/compile/{slug}?dev=true",
        headers=headers,
    )

    if compile_resp.status_code not in (200, 201, 202):
        print(f"\n❌ 編譯失敗: {compile_resp.status_code}")
        try:
            error_data = compile_resp.json()
            if "errors" in error_data:
                print("\n🚨 編譯錯誤：")
                for err in error_data["errors"]:
                    print(f"   ❌ {err.get('file', '?')}: {err.get('message', str(err))}")
            elif "error" in error_data:
                print(f"   ❌ {error_data['error']}")
            else:
                print(json.dumps(error_data, indent=2, ensure_ascii=False)[:2000])
        except Exception:
            print(compile_resp.text[:1000])
        sys.exit(1)

    print("   ✅ 編譯成功！")

    try:
        compile_data = compile_resp.json()
        if compile_data.get("warnings"):
            print("\n⚠️ 編譯警告：")
            for w in compile_data["warnings"]:
                print(f"   ⚠️ {w}")
    except Exception:
        pass

    # ─── 5. 完成 ───────────────────────────
    print("\n" + "=" * 50)
    print("🎉 耐落請假系統（員工端）VFS 注入完成！")
    print(f"   📱 App ID: {APP_ID}")
    print(f"   📦 VFS 檔案數: {len(vfs)}")
    print(f"   🔢 VFS 版本: {new_version}")
    print(f"   🌐 前往：{BASE_URL}/app/{APP_ID}")
    print("=" * 50)


if __name__ == "__main__":
    main()
