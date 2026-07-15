"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { MAIN_NAVIGATION } from "@/config/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Logo } from "@/components/ui/logo";
import { WorkspaceSelector } from "./WorkspaceSelector";

export function MobileSidebar() {
  const pathname = usePathname();

  return (
    <SheetContent side="left" className="w-[280px] p-0 bg-surface-1">
      <div className="flex h-16 items-center px-6 border-b border-border/60">
        <Link href="/dashboard" className="flex items-center gap-2">
          <Logo textClassName="text-foreground" iconClassName="shadow-none bg-primary" />
        </Link>
      </div>
      
      <div className="px-4 py-4 border-b border-border/60">
        <WorkspaceSelector />
      </div>

      <div className="flex flex-col gap-1 p-4">
        {MAIN_NAVIGATION.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Button
              key={item.href}
              variant={isActive ? "secondary" : "ghost"}
              className={cn(
                "justify-start h-11 w-full text-base",
                isActive
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground"
              )}
              asChild
            >
              <Link href={item.href}>
                <item.icon className={cn("mr-3 h-5 w-5", isActive ? "text-primary" : "")} />
                {item.name}
              </Link>
            </Button>
          );
        })}
      </div>
    </SheetContent>
  );
}
