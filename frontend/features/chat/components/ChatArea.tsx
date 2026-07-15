"use client";

import { useEffect, useRef, useState } from "react";
import { useChat, useAsk, useConversation } from "../hooks/use-chat";
import { MessageBubble } from "./MessageBubble";
import { PromptComposer } from "./PromptComposer";
import { ChatMessage } from "../types";
import { Bot } from "lucide-react";
import { v4 as uuidv4 } from "uuid";

interface ChatAreaProps {
  activeConversationId: string | null;
  onConversationCreated: (id: string) => void;
  defaultCompanyId?: string;
}

export function ChatArea({ activeConversationId, onConversationCreated, defaultCompanyId }: ChatAreaProps) {
  const { data: conversation, isLoading } = useConversation(activeConversationId);
  const chatMutation = useChat();
  
  // Local state for optimistic updates
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (conversation) {
      setLocalMessages(conversation.messages || []);
    } else {
      setLocalMessages([]);
    }
  }, [conversation, activeConversationId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [localMessages]);

  const handleSend = async (queryText: string, companyId?: string) => {
    const optimisticUserMsg: ChatMessage = {
      id: uuidv4(),
      role: "user",
      content: queryText,
      created_at: new Date().toISOString(),
      citations: [],
    };
    
    setLocalMessages(prev => [...prev, optimisticUserMsg]);

    try {
      const response = await chatMutation.mutateAsync({
        query_text: queryText,
        company_id: companyId || defaultCompanyId,
        conversation_id: activeConversationId,
      });

      const assistantMsg: ChatMessage = {
        id: uuidv4(),
        role: "assistant",
        content: response.answer,
        created_at: new Date().toISOString(),
        citations: response.citations,
      };

      setLocalMessages(prev => [...prev, assistantMsg]);

      if (!activeConversationId) {
        onConversationCreated(response.conversation_id);
      }
    } catch (err) {
      console.error("Chat failed:", err);
      // Remove optimistic message or show error state
    }
  };

  return (
    <div className="flex flex-col h-full flex-1 relative bg-background/50">
      <div className="flex-1 overflow-y-auto" ref={scrollRef}>
        {localMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-6">
              <Bot className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-2xl font-bold mb-2">EquityIQ Intelligence</h3>
            <p className="text-muted-foreground max-w-md">
              Ask about financial performance, risk factors, or management commentary. 
              I will synthesize answers directly from uploaded filings.
            </p>
          </div>
        ) : (
          <div className="flex flex-col max-w-4xl mx-auto w-full px-4 py-8">
            {localMessages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </div>
        )}
      </div>

      <div className="shrink-0">
        <PromptComposer 
          onSend={handleSend} 
          isPending={chatMutation.isPending}
          defaultCompanyId={defaultCompanyId}
        />
      </div>
    </div>
  );
}
