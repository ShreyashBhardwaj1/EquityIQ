"use client";

import { Citation } from "../types";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { FileText, Link2 } from "lucide-react";

interface CitationCardProps {
  citation: Citation;
  index: number;
}

export function CitationCard({ citation, index }: CitationCardProps) {
  return (
    <HoverCard>
      <HoverCardTrigger asChild>
        <span className="inline-flex items-center justify-center w-4 h-4 ml-1 text-[10px] font-bold text-primary bg-primary/10 rounded-full cursor-pointer hover:bg-primary/20 transition-colors">
          {index}
        </span>
      </HoverCardTrigger>
      <HoverCardContent className="w-80 bg-background/95 backdrop-blur-xl border shadow-lg z-50">
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 font-semibold text-sm">
            <FileText className="w-4 h-4 text-primary" />
            <span className="truncate">{citation.document_name}</span>
          </div>
          <div className="text-xs text-muted-foreground">
            Page {citation.page_number} {citation.section_heading ? `• ${citation.section_heading}` : ""}
          </div>
          <div className="mt-1 text-sm border-l-2 border-primary/50 pl-3 italic text-muted-foreground">
            &quot;{citation.snippet_preview}...&quot;
          </div>
          <div className="mt-2 flex items-center justify-between text-[10px] text-muted-foreground font-mono">
            <span>Score: {(citation.score * 100).toFixed(1)}%</span>
            <span className="flex items-center gap-1">
              <Link2 className="w-3 h-3" />
              Source
            </span>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}
