import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetTrigger } from "@/components/ui/sheet";
import { MobileSidebar } from "./MobileSidebar";
import { BreadcrumbNav } from "./BreadcrumbNav";
import { GlobalSearch } from "./GlobalSearch";
import { NotificationBell } from "./NotificationBell";
import { UserProfile } from "./UserProfile";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { LAYOUT_CONFIG } from "@/config/layout";

export function Topbar() {
  return (
    <header 
      className="sticky top-0 z-40 flex w-full border-b border-border/60 bg-surface-1/95 backdrop-blur supports-[backdrop-filter]:bg-surface-1/60 items-center gap-4 px-4 sm:px-6 shadow-sm"
      style={{ height: LAYOUT_CONFIG.topbar.height }}
    >
      <div className="flex items-center gap-4 md:hidden">
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="shrink-0">
              <Menu className="h-5 w-5" />
              <span className="sr-only">Toggle navigation menu</span>
            </Button>
          </SheetTrigger>
          <MobileSidebar />
        </Sheet>
      </div>
      
      <div className="flex flex-1 items-center gap-4 md:gap-8">
        <BreadcrumbNav />
      </div>
      
      <div className="flex items-center gap-2 sm:gap-4">
        <GlobalSearch />
        <ThemeToggle />
        <NotificationBell />
        <div className="hidden md:flex h-6 w-px bg-border mx-1" />
        <UserProfile />
      </div>
    </header>
  );
}
