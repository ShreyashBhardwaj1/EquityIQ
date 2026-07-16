"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Pin, Building, FileText, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MAIN_NAVIGATION } from "@/config/navigation";
import { Logo } from "@/components/ui/logo";
import { LAYOUT_CONFIG } from "@/config/layout";
import { WorkspaceSelector } from "./WorkspaceSelector";

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      aria-label="Main Navigation"
      className={cn(
        "hidden md:flex h-screen flex-col border-r border-white/10 bg-background/50 backdrop-blur-xl transition-all duration-300 shadow-[2px_0_15px_rgb(0,0,0,0.03)]",
        className
      )}
      style={{ width: LAYOUT_CONFIG.sidebar.width }}
    >
      {/* Header / Logo */}
      <div 
        className="flex h-16 shrink-0 items-center px-6 border-b border-border/60"
        style={{ height: LAYOUT_CONFIG.topbar.height }}
      >
        <Link href="/dashboard" className="flex items-center gap-2">
          <Logo textClassName="text-foreground" iconClassName="shadow-none bg-primary" />
        </Link>
      </div>

      {/* Workspace Switcher */}
      <div className="px-4 py-4 border-b border-border/60">
        <WorkspaceSelector />
      </div>

      {/* Navigation Links */}
      <ScrollArea className="flex-1 px-3 py-4">
        <nav className="flex flex-col gap-1">
          {MAIN_NAVIGATION.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Button
                key={item.href}
                variant="ghost"
                className={cn(
                  "relative justify-start h-10 px-3 w-full transition-colors group overflow-hidden",
                  isActive
                    ? "text-primary font-medium"
                    : "text-muted-foreground hover:text-foreground"
                )}
                asChild
              >
                <Link href={item.href}>
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 bg-primary/10 border-l-2 border-primary"
                      initial={false}
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                  )}
                  <item.icon className={cn("mr-3 h-4 w-4 relative z-10 transition-transform group-hover:scale-110", isActive ? "text-primary" : "")} />
                  <span className="relative z-10">{item.name}</span>
                </Link>
              </Button>
            );
          })}
        </nav>
      </ScrollArea>

      {/* Mock Lower Sections */}
      <ScrollArea className="flex-1 px-4 py-4 border-t border-white/5">
        <div className="space-y-6">
          <div className="space-y-2">
            <h4 className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2 px-2">Pinned Items</h4>
            <div className="flex flex-col gap-1">
              <Button variant="ghost" className="h-8 justify-start px-2 text-xs text-muted-foreground hover:text-foreground"><Pin className="mr-2 h-3 w-3" /> Q3 Earnings Call</Button>
              <Button variant="ghost" className="h-8 justify-start px-2 text-xs text-muted-foreground hover:text-foreground"><Pin className="mr-2 h-3 w-3" /> Tech Sector Analysis</Button>
            </div>
          </div>
          <div className="space-y-2">
            <h4 className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2 px-2">Recent Companies</h4>
            <div className="flex flex-col gap-1">
              <Button variant="ghost" className="h-8 justify-between px-2 text-xs text-muted-foreground hover:text-foreground">
                <span className="flex items-center"><Building className="mr-2 h-3 w-3" /> Apple Inc.</span>
                <ChevronRight className="h-3 w-3 opacity-50" />
              </Button>
              <Button variant="ghost" className="h-8 justify-between px-2 text-xs text-muted-foreground hover:text-foreground">
                <span className="flex items-center"><Building className="mr-2 h-3 w-3" /> Tesla</span>
                <ChevronRight className="h-3 w-3 opacity-50" />
              </Button>
            </div>
          </div>
        </div>
      </ScrollArea>
    </aside>
  );
}
