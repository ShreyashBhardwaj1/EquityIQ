"use client";

import { Button } from "@/components/ui/button";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import { useDeleteConversation } from "../hooks/use-chat";

// Mocking useConversationsList since backend didn't explicitly have it in chat.py,
// but we need it for sidebar. If it's missing from backend, we will just simulate an empty list or
// fetch it if a GET /chat/conversations endpoint is added later.
// For now, we will just use the current active conversation if any, or placeholder.

interface ChatSidebarProps {
  conversations: { id: string; title: string; updated_at: string }[];
  activeId: string | null;
  onSelect: (id: string | null) => void;
}

export function ChatSidebar({ conversations, activeId, onSelect }: ChatSidebarProps) {
  const deleteMutation = useDeleteConversation();

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteMutation.mutateAsync(id);
    if (activeId === id) {
      onSelect(null);
    }
  };

  return (
    <div className="w-64 border-r border-border/50 bg-background/30 backdrop-blur-sm flex flex-col h-full hidden md:flex">
      <div className="p-4 border-b border-border/50">
        <Button 
          variant="outline" 
          className="w-full justify-start gap-2 bg-background/50 hover:bg-muted"
          onClick={() => onSelect(null)}
        >
          <Plus className="w-4 h-4" />
          New Intelligence Chat
        </Button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {conversations.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center p-4 mt-10">
            No recent conversations.
          </div>
        ) : (
          conversations.map((conv) => (
            <div 
              key={conv.id}
              className={`group flex items-center justify-between px-3 py-2 text-sm rounded-md cursor-pointer transition-colors ${
                activeId === conv.id ? "bg-muted/80 text-foreground font-medium" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              }`}
              onClick={() => onSelect(conv.id)}
            >
              <div className="flex items-center gap-2 overflow-hidden">
                <MessageSquare className="w-4 h-4 shrink-0" />
                <span className="truncate">{conv.title}</span>
              </div>
              <Button 
                variant="ghost" 
                size="icon" 
                className="w-6 h-6 opacity-0 group-hover:opacity-100 shrink-0"
                onClick={(e) => handleDelete(e, conv.id)}
              >
                <Trash2 className="w-3 h-3 text-muted-foreground hover:text-destructive" />
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
