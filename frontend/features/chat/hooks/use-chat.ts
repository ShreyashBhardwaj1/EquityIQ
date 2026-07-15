import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { chatApi } from "../api/chat-api";
import { ChatRequestPayload } from "../types";

const QUERY_KEYS = {
  all: ["chat"] as const,
  conversations: () => [...QUERY_KEYS.all, "conversations"] as const,
  detail: (id: string) => [...QUERY_KEYS.all, "conversation", id] as const,
};

export function useConversation(id: string | null) {
  return useQuery({
    queryKey: QUERY_KEYS.detail(id as string),
    queryFn: () => chatApi.getConversation(id as string),
    enabled: !!id,
  });
}

export function useChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ChatRequestPayload) => chatApi.chat(data),
    onSuccess: (data, variables) => {
      // Invalidate the specific conversation to refetch latest history, 
      // or invalidate the list of conversations if it was a new one.
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.detail(data.conversation_id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.conversations() });
    },
  });
}

export function useAsk() {
  return useMutation({
    mutationFn: (data: Omit<ChatRequestPayload, "conversation_id">) => chatApi.ask(data),
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => chatApi.deleteConversation(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.conversations() });
      queryClient.removeQueries({ queryKey: QUERY_KEYS.detail(id) });
    },
  });
}
