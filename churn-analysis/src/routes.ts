import { LayoutDashboard, Users, Layers, Database } from "lucide-react";

export interface RouteItem {
  title: string;
  path: string;
  icon?: any;
  children?: RouteItem[];
}

export const routes: RouteItem[] = [
  { title: "風險總覽", path: "/", icon: LayoutDashboard },
  { title: "業務分析", path: "/sales", icon: Users },
  { title: "風險類別", path: "/categories", icon: Layers },
  { title: "資料來源", path: "/datasource", icon: Database },
];
