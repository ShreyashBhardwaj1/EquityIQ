"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Loader2 } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCompaniesList } from "@/features/companies/hooks/use-companies";

interface PromptComposerProps {
  onSend: (queryText: string, companyId?: string) => void;
  isPending: boolean;
  defaultCompanyId?: string;
}

export function PromptComposer({ onSend, isPending, defaultCompanyId }: PromptComposerProps) {
  const [text, setText] = useState("");
  const [selectedCompanyId, setSelectedCompanyId] = useState<string>(defaultCompanyId || "");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const { data: companies } = useCompaniesList();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (!text.trim() || isPending) return;
    onSend(text.trim(), selectedCompanyId || undefined);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col gap-2 p-4 bg-background/80 backdrop-blur-xl border-t border-border/50">
      <div className="flex w-full gap-2 items-end max-w-4xl mx-auto relative">
        <div className="flex-1 relative flex flex-col bg-background/50 border rounded-xl overflow-hidden focus-within:ring-1 focus-within:ring-primary/50 transition-shadow shadow-sm">
          {!defaultCompanyId && (
            <div className="px-3 pt-2 pb-1 border-b border-border/50 bg-muted/20">
              <Select value={selectedCompanyId} onValueChange={setSelectedCompanyId}>
                <SelectTrigger className="h-7 w-fit border-0 bg-transparent shadow-none hover:bg-muted/50 p-1 text-xs">
                  <SelectValue placeholder="Scope to company (Optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Companies (Global RAG)</SelectItem>
                  {companies?.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          
          <Textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask EquityIQ about financial intelligence, risk factors, or historical data..."
            className="min-h-[56px] w-full resize-none border-0 shadow-none focus-visible:ring-0 p-3 pb-3 bg-transparent text-sm"
            disabled={isPending}
            rows={1}
          />
        </div>
        
        <Button 
          size="icon" 
          className="h-[56px] w-[56px] rounded-xl shrink-0 shadow-sm"
          onClick={handleSend}
          disabled={!text.trim() || isPending}
        >
          {isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
        </Button>
      </div>
      <div className="text-center text-xs text-muted-foreground mt-1">
        EquityIQ can make mistakes. Verify critical financial data against raw documents.
      </div>
    </div>
  );
}
