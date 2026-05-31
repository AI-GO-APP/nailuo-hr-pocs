import React from "react";
import { HashRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import LogInputPage from "./pages/LogInputPage";
import HistoryPage from "./pages/HistoryPage";
import CustomersPage from "./pages/CustomersPage";

export default function App() {
  return (
    <HashRouter>
      <AppLayout appName="業務工作平台">
        <Routes>
          <Route path="/" element={<LogInputPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/customers" element={<CustomersPage />} />
        </Routes>
      </AppLayout>
    </HashRouter>
  );
}
