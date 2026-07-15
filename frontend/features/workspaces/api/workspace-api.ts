import { apiRequest, getAuthHeaders } from "@/lib/api-client";
import { Workspace, WorkspaceCreatePayload, WorkspacePatchPayload, SwitchResponse } from "../types";

export const workspaceApi = {
  create: async (payload: WorkspaceCreatePayload): Promise<Workspace> => {
    return apiRequest("/workspaces", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: getAuthHeaders(),
    });
  },

  list: async (): Promise<Workspace[]> => {
    return apiRequest("/workspaces", {
      headers: getAuthHeaders(),
    });
  },

  get: async (id: string): Promise<Workspace> => {
    return apiRequest(`/workspaces/${id}`, {
      headers: getAuthHeaders(),
    });
  },

  patch: async (id: string, payload: WorkspacePatchPayload): Promise<Workspace> => {
    return apiRequest(`/workspaces/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
      headers: getAuthHeaders(),
    });
  },

  delete: async (id: string): Promise<{ detail: string }> => {
    return apiRequest(`/workspaces/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
  },

  switch: async (id: string): Promise<SwitchResponse> => {
    return apiRequest(`/workspaces/${id}/switch`, {
      method: "POST",
      headers: getAuthHeaders(),
    });
  },
};
