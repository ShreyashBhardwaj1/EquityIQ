import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reportsApi } from "../api/reports-api";
import { GenerateReportPayload } from "../types";

const QUERY_KEYS = {
  all: ["reports"] as const,
  lists: () => [...QUERY_KEYS.all, "list"] as const,
  list: (companyId: string) => [...QUERY_KEYS.lists(), companyId] as const,
  details: () => [...QUERY_KEYS.all, "detail"] as const,
  detail: (companyId: string, reportId: string) => [...QUERY_KEYS.details(), companyId, reportId] as const,
};

export function useReportsList(companyId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.list(companyId),
    queryFn: () => reportsApi.list(companyId),
    enabled: !!companyId,
  });
}

export function useReportDetail(companyId: string, reportId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.detail(companyId, reportId),
    queryFn: () => reportsApi.get(companyId, reportId),
    enabled: !!companyId && !!reportId,
  });
}

export function useGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: GenerateReportPayload) => reportsApi.generate(data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.list(variables.company_id) });
    },
  });
}
