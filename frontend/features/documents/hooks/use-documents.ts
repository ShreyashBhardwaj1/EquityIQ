import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "../api/documents-api";
import { DocumentUploadPayload, DocumentUpdatePayload } from "../types";

const QUERY_KEYS = {
  all: ["documents"] as const,
  lists: () => [...QUERY_KEYS.all, "list"] as const,
  list: (companyId?: string, limit?: number, offset?: number) => [...QUERY_KEYS.lists(), { companyId, limit, offset }] as const,
  details: () => [...QUERY_KEYS.all, "detail"] as const,
  detail: (id: string) => [...QUERY_KEYS.details(), id] as const,
  versions: (id: string) => [...QUERY_KEYS.detail(id), "versions"] as const,
  chunks: (id: string) => [...QUERY_KEYS.detail(id), "chunks"] as const,
};

export function useDocumentsList(companyId?: string, limit: number = 20, offset: number = 0) {
  return useQuery({
    queryKey: QUERY_KEYS.list(companyId, limit, offset),
    queryFn: () => documentsApi.list(companyId, limit, offset),
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.detail(id),
    queryFn: () => documentsApi.get(id),
    enabled: !!id,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DocumentUploadPayload) => documentsApi.upload(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.lists() });
    },
  });
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DocumentUpdatePayload) => documentsApi.update(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.lists() });
    },
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.lists() });
    },
  });
}

export function useParseDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentsApi.parse(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.detail(id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.lists() });
    },
  });
}

export function useDocumentVersions(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.versions(id),
    queryFn: () => documentsApi.versions(id),
    enabled: !!id,
  });
}

export function useDocumentChunks(id: string, limit: number = 100, offset: number = 0) {
  return useQuery({
    queryKey: QUERY_KEYS.chunks(id),
    queryFn: () => documentsApi.chunks(id, limit, offset),
    enabled: !!id,
  });
}
