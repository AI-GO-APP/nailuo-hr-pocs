import React, { useState, useEffect } from "react";
import { routes } from "../routes";
import { useNavigate, useLocation } from "react-router-dom";

interface Props { collapsed?: boolean; appName: string; }

const getApiBase = () => (window as any).__API_BASE__ || "/api/v1";
const getToken = () => (window as any).__APP_TOKEN__ || "";

export default function AppSidebar({ collapsed, appName }: Props) {
  const navigate = useNavigate();
  const location = useLocation();
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    fetch(`${getApiBase()}/auth/me`, { headers, credentials: "include" })
      .then(r => r.ok ? r.json() : null)
      .then(me => {
        if (me) {
          setUserName(me.name || me.display_name || me.email?.split("@")[0] || "");
          setUserEmail(me.email || "");
        }
      })
      .catch(() => {});
  }, []);

  const avatar = userName ? userName[0] : "U";

  return (
    <aside className={`app-sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-brand">
        <div className="brand-logo green">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </div>
        <div>
          <div className="brand-name">{appName}</div>
          <div className="brand-sub">業務工作平台</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-group-label">日常工作</div>
        {routes.map((item, i) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <button key={i} className={`sidebar-item ${isActive ? "active" : ""}`} onClick={() => navigate(item.path)}>
              {Icon && <Icon size={16} />}
              <span>{item.title}</span>
            </button>
          );
        })}
      </nav>
      <div className="user-card">
        <div className="user-avatar">{avatar}</div>
        <div className="user-info">
          <div className="user-name">{userName || "使用者"}</div>
          <div className="user-role">{userEmail}</div>
        </div>
      </div>
    </aside>
  );
}
