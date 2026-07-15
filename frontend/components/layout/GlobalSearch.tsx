"use client";

import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export function GlobalSearch() {
  return (
    <Button
      variant="outline"
      className="relative h-10 w-full justify-start rounded-full bg-background/40 backdrop-blur-md border-white/20 hover:bg-background/60 hover:border-white/30 text-sm font-normal text-muted-foreground shadow-sm transition-all duration-300 sm:pr-12 md:w-64 lg:w-96"
    >
      <Search className="mr-2 h-4 w-4 shrink-0" />
      <span className="hidden lg:inline-flex">Search companies, filings, reports...</span>
      <span className="inline-flex lg:hidden">Search...</span>
      <kbd className="pointer-events-none absolute right-2 top-2.5 hidden h-5 select-none items-center gap-1 rounded-sm border border-white/20 bg-background/50 px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex shadow-sm">
        <span className="text-xs">⌘</span>K
      </kbd>
    </Button>
  );
}
