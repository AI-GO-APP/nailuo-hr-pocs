import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import AppSidebar from "./AppSidebar";

interface Props { children: React.ReactNode; appName: string; }

const ROUTE_NAMES: Record<string, string> = {
  "/": "\u98a8\u96aa\u7e3d\u89bd",
  "/sales": "\u696d\u52d9\u5206\u6790",
  "/categories": "\u98a8\u96aa\u985e\u5225\u5206\u6790",
  "/datasource": "\u8cc7\u6599\u4f86\u6e90",
};

export default function AppLayout({ children, appName }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const [syncMin, setSyncMin] = useState(0);
  const location = useLocation();
  const currentPage = ROUTE_NAMES[location.pathname] || "";

  useEffect(() => {
    const check = () => { if (window.innerWidth < 768) setCollapsed(true); };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  useEffect(() => {
    setSyncMin(0);
    const iv = setInterval(() => setSyncMin(m => m + 1), 60000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="app-layout">
      <AppSidebar collapsed={collapsed} appName={appName} />
      <div className="app-main">
        <div className="app-topbar">
          <button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
          </button>
          <div className="breadcrumb">
            <span>{"\u5ba2\u6236\u6d41\u5931\u98a8\u96aa\u5206\u6790"}</span>
            <span className="sep">{"\u203a"}</span>
            <span className="current">{currentPage}</span>
          </div>
          <div className="topbar-spacer" />
          <div className="sync-badge">
            <div className="sync-dot" />
            {"\u5df2\u540c\u6b65"} {syncMin > 0 ? `${syncMin} \u5206\u9418\u524d` : "\u525b\u525b"}
          </div>
        </div>
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}
