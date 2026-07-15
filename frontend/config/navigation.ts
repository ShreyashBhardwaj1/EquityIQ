import {
  LayoutDashboard,
  Building2,
  FileText,
  Settings,
  LineChart,
} from "lucide-react";

export interface NavigationItem {
  name: string;
  href: string;
  icon: React.ElementType;
}

export const MAIN_NAVIGATION: NavigationItem[] = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Companies",
    href: "/companies",
    icon: Building2,
  },
  {
    name: "Financials",
    href: "/financials",
    icon: LineChart,
  },
  {
    name: "Reports",
    href: "/reports",
    icon: FileText,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
];
