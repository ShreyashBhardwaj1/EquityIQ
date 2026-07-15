import { apiRequest, getAuthHeaders } from "@/lib/api-client";
import { Document, DocumentVersion, ChunkResponse, DocumentUploadPayload, DocumentUpdatePayload } from "../types";

export const documentsApi = {
  list: async (companyId?: string, limit: number = 20, offset: number = 0): Promise<Document[]> => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (companyId) {
      params.append("company_id", companyId);
    }
    return apiRequest(`/documents?${params.toString()}`, {
      headers: getAuthHeaders(),
    });
  },

  get: async (id: string): Promise<Document> => {
    return apiRequest(`/documents/${id}`, {
      headers: getAuthHeaders(),
    });
  },

  upload: async (payload: DocumentUploadPayload): Promise<Document> => {
    const formData = new FormData();
    formData.append("company_id", payload.company_id);
    formData.append("doc_type", payload.doc_type);
    formData.append("fiscal_period", payload.fiscal_period);
    formData.append("file", payload.file);

    return apiRequest("/documents", {
      method: "POST",
      body: formData,
      headers: getAuthHeaders(),
    });
  },

  update: async (payload: DocumentUpdatePayload): Promise<Document> => {
    const formData = new FormData();
    formData.append("change_reason", payload.change_reason);
    formData.append("file", payload.file);

    return apiRequest(`/documents/${payload.document_id}`, {
      method: "PATCH",
      body: formData,
      headers: getAuthHeaders(),
    });
  },

  delete: async (id: string): Promise<void> => {
    return apiRequest(`/documents/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
  },

  versions: async (id: string): Promise<DocumentVersion[]> => {
    return apiRequest(`/documents/${id}/versions`, {
      headers: getAuthHeaders(),
    });
  },

  parse: async (id: string): Promise<{ status: string; message: string }> => {
    return apiRequest(`/documents/${id}/parse`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
  },

  reprocess: async (id: string): Promise<{ status: string; message: string }> => {
    return apiRequest(`/documents/${id}/reprocess`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
  },

  chunks: async (id: string, limit: number = 100, offset: number = 0): Promise<ChunkResponse[]> => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    return apiRequest(`/documents/${id}/chunks?${params.toString()}`, {
      headers: getAuthHeaders(),
    });
  },
};
