import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./App.css";

const rootEl = (window as any).__CUSTOM_APP_ROOT__ || document.getElementById("root");
if (rootEl) {
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
