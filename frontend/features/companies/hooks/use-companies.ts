import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { companiesApi } from "../api/companies-api";
import { CompaniesListParams, CompanyCreatePayload } from "../types";

const QUERY_KEYS = {
  all: ["companies"] as const,
  lists: () => [...QUERY_KEYS.all, "list"] as const,
  list: (params: CompaniesListParams) => [...QUERY_KEYS.lists(), params] as const,
  searches: () => [...QUERY_KEYS.all, "search"] as const,
  search: (query: string) => [...QUERY_KEYS.searches(), query] as const,
  details: () => [...QUERY_KEYS.all, "detail"] as const,
  detail: (id: string) => [...QUERY_KEYS.details(), id] as const,
};

export function useCompaniesList(params: CompaniesListParams = {}) {
  return useQuery({
    queryKey: QUERY_KEYS.list(params),
    queryFn: () => companiesApi.list(params),
  });
}

export function useCompaniesSearch(query: string) {
  return useQuery({
    queryKey: QUERY_KEYS.search(query),
    queryFn: () => companiesApi.search(query),
    enabled: query.length > 0,
  });
}

export function useCompany(id: string) {
  return useQuery({
    queryKey: QUERY_KEYS.detail(id),
    queryFn: () => companiesApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCompany() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CompanyCreatePayload) => companiesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.all });
    },
  });
}

export function useDeleteCompany() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => companiesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.all });
    },
  });
}
