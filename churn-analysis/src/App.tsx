import { HashRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import AppLayout from "./components/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import SalesPage from "./pages/SalesPage";
import CategoriesPage from "./pages/CategoriesPage";
import DataSourcePage from "./pages/DataSourcePage";
import NotFoundPage from "./pages/NotFoundPage";

export default function App() {
  return (
    <>
      <Toaster position="top-right" />
      <HashRouter>
        <AppLayout appName="客戶流失風險分析">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/sales" element={<SalesPage />} />
            <Route path="/categories" element={<CategoriesPage />} />
            <Route path="/datasource" element={<DataSourcePage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AppLayout>
      </HashRouter>
    </>
  );
}
