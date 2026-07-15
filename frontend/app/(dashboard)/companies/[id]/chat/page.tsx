"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { ChatSidebar } from "@/features/chat/components/ChatSidebar";
import { ChatArea } from "@/features/chat/components/ChatArea";

export default function CompanyChatPage() {
  const params = useParams();
  const companyId = params.id as string;
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Note: Since backend currently lacks a GET /chat/conversations endpoint,
  // we are mocking an empty list for the global view to preserve the architecture.
  const mockConversations: any[] = [];

  return (
    <div className="w-full h-full flex overflow-hidden">
      <ChatSidebar 
        conversations={mockConversations}
        activeId={activeConversationId}
        onSelect={setActiveConversationId}
      />
      <ChatArea 
        activeConversationId={activeConversationId}
        onConversationCreated={setActiveConversationId}
        defaultCompanyId={companyId}
      />
    </div>
  );
}
