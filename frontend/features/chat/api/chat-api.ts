import { apiRequest, getAuthHeaders } from "@/lib/api-client";
import { ChatRequestPayload, ChatResponse, AskResponse, ConversationDetail } from "../types";

export const chatApi = {
  chat: async (payload: ChatRequestPayload): Promise<ChatResponse> => {
    return apiRequest("/chat/chat", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: getAuthHeaders(),
    });
  },

  ask: async (payload: Omit<ChatRequestPayload, "conversation_id">): Promise<AskResponse> => {
    return apiRequest("/chat/ask", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: getAuthHeaders(),
    });
  },

  getConversation: async (id: string): Promise<ConversationDetail> => {
    return apiRequest(`/chat/conversation/${id}`, {
      headers: getAuthHeaders(),
    });
  },

  deleteConversation: async (id: string): Promise<{ status: string; message: string }> => {
    return apiRequest(`/chat/conversation/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
  },
};
