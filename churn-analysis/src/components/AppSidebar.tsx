import React, { useState, useEffect } from "react";
import { routes, RouteItem } from "../routes";
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
        <div className="brand-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3l1.9 5.8L19 10.7l-4.1 3 1.6 5.3-4.5-3.3-4.5 3.3 1.6-5.3-4.1-3 5.1-1.9z"/></svg>
        </div>
        <div className="brand-name">{appName}</div>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-group-label">{"\u5ba2\u6236\u6d41\u5931\u98a8\u96aa\u5206\u6790"}</div>
        {routes.map((item, i) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <button key={i} className={`sidebar-item ${isActive ? "active" : ""}`} onClick={() => navigate(item.path)}>
              {Icon && <Icon size={16} />}
              <span>{item.title}</span>
              {i === 0 && <span className="new-tag">NEW</span>}
            </button>
          );
        })}
      </nav>
      <div className="user-card">
        <div className="user-avatar">{avatar}</div>
        <div className="user-info">
          <div className="user-name">{userName || "\u4f7f\u7528\u8005"}</div>
          <div className="user-role">{userEmail}</div>
        </div>
      </div>
    </aside>
  );
}
