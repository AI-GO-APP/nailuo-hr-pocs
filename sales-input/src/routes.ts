import { PenLine, ClipboardList, Users } from "lucide-react";
export interface RouteItem { title: string; path: string; icon?: any; }
export const routes: RouteItem[] = [
  { title: "填寫業務日誌", path: "/", icon: PenLine },
  { title: "我的歷史日誌", path: "/history", icon: ClipboardList },
  { title: "我的客戶", path: "/customers", icon: Users },
];
