"use client";

import { usePathname, useRouter } from "next/navigation";
import { LAYOUT_CONFIG } from "@/config/layout";
import { Button } from "@/components/ui/button";
import { User, Palette, Briefcase, Users, Link2, HardDrive } from "lucide-react";
import { cn } from "@/lib/utils";

const SETTINGS_NAV = [
  { name: "Profile", href: "/settings/profile", icon: User },
  { name: "Appearance", href: "/settings/appearance", icon: Palette },
  { name: "Workspace", href: "/settings/workspace", icon: Briefcase },
  { name: "Team Members", href: "/settings/team", icon: Users },
  { name: "API Connections", href: "/settings/api-connections", icon: Link2 },
  { name: "Storage & Usage", href: "/settings/storage", icon: HardDrive },
];

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div className="w-full h-full flex flex-col md:flex-row" style={{ padding: LAYOUT_CONFIG.content.padding }}>
      
      {/* Sidebar Navigation for Settings */}
      <aside className="w-full md:w-64 shrink-0 pr-0 md:pr-8 mb-8 md:mb-0">
        <h1 className="text-3xl font-bold tracking-tight mb-6">Settings</h1>
        <nav className="flex md:flex-col gap-2 overflow-x-auto pb-4 md:pb-0">
          {SETTINGS_NAV.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Button
                key={item.name}
                variant="ghost"
                className={cn(
                  "justify-start gap-3 whitespace-nowrap",
                  isActive ? "bg-muted font-semibold text-foreground" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                )}
                onClick={() => router.push(item.href)}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Button>
            );
          })}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 max-w-4xl">
        {children}
      </main>

    </div>
  );
}
