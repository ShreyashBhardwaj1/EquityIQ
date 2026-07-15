"use client";

import { ChatMessage } from "../types";
import { CitationCard } from "./CitationCard";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeSanitize from "rehype-sanitize";
import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  // The backend might inject citation markers like [1], [2].
  // We can render them by parsing, or we can just list citations at the bottom.
  // For a clean UI, we'll render the markdown, and append citations at the bottom if present.

  return (
    <div className={cn("flex w-full gap-4 py-6", isUser ? "bg-transparent" : "bg-muted/30 border-y border-border/50")}>
      <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-background border shadow-sm">
        {isUser ? <User className="w-4 h-4 text-primary" /> : <Bot className="w-4 h-4 text-emerald-500" />}
      </div>
      <div className="flex flex-col flex-1 min-w-0">
        <div className="font-semibold text-sm mb-1">
          {isUser ? "You" : "EquityIQ"}
        </div>
        <div className="prose prose-sm md:prose-base dark:prose-invert prose-headings:font-bold prose-a:text-primary max-w-none break-words">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeSanitize]}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-4 pt-3 border-t border-border/50 flex flex-wrap gap-2 items-center">
            <span className="text-xs font-semibold text-muted-foreground mr-2">Sources:</span>
            {message.citations.map((cit, idx) => (
              <CitationCard key={cit.id} citation={cit} index={idx + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
