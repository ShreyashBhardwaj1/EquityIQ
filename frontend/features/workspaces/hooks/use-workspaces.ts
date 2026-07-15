import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { workspaceApi } from "../api/workspace-api";
import { WorkspaceCreatePayload, WorkspacePatchPayload } from "../types";

const QUERY_KEYS = {
  all: ["workspaces"] as const,
  list: () => [...QUERY_KEYS.all, "list"] as const,
  detail: (id: string) => [...QUERY_KEYS.all, "detail", id] as const,
};

export function useWorkspacesList() {
  return useQuery({
    queryKey: QUERY_KEYS.list(),
    queryFn: () => workspaceApi.list(),
  });
}

export function useWorkspace(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.detail(id),
    queryFn: () => workspaceApi.get(id),
    enabled: !!id,
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkspaceCreatePayload) => workspaceApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list() });
    },
  });
}

export function useUpdateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkspacePatchPayload }) => workspaceApi.patch(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list() });
    },
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workspaceApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list() });
    },
  });
}

export function useSwitchWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workspaceApi.switch(id),
    onSuccess: () => {
      // Invalidate everything to refresh data context
      queryClient.invalidateQueries(); 
    },
  });
}
