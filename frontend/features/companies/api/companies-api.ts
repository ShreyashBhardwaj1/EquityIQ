import { apiRequest, getAuthHeaders } from "@/lib/api-client";
import { Company, CompaniesListParams, CompanyCreatePayload } from "../types";

export const companiesApi = {
  list: async (params?: CompaniesListParams): Promise<Company[]> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) searchParams.append(key, String(value));
      });
    }
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return apiRequest(`/companies${query}`, {
      headers: getAuthHeaders(),
    });
  },

  search: async (query: string): Promise<Company[]> => {
    return apiRequest(`/companies/search?query=${encodeURIComponent(query)}`, {
      headers: getAuthHeaders(),
    });
  },

  get: async (id: string): Promise<Company> => {
    return apiRequest(`/companies/${id}`, {
      headers: getAuthHeaders(),
    });
  },

  create: async (data: CompanyCreatePayload): Promise<Company> => {
    return apiRequest("/companies", {
      method: "POST",
      body: JSON.stringify(data),
      headers: getAuthHeaders(),
    });
  },

  delete: async (id: string): Promise<{ detail: string }> => {
    return apiRequest(`/companies/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
  },
};
