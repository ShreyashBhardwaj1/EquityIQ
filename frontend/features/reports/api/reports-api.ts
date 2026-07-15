import { apiRequest, getAuthHeaders } from "@/lib/api-client";
import { ReportSummary, ReportDetail, GenerateReportPayload } from "../types";

export const reportsApi = {
  list: async (companyId: string): Promise<ReportSummary[]> => {
    return apiRequest(`/companies/${companyId}/reports`, {
      headers: getAuthHeaders(),
    });
  },

  get: async (companyId: string, reportId: string): Promise<ReportDetail> => {
    return apiRequest(`/companies/${companyId}/reports/${reportId}`, {
      headers: getAuthHeaders(),
    });
  },

  generate: async (payload: GenerateReportPayload): Promise<ReportSummary> => {
    return apiRequest(`/companies/${payload.company_id}/reports/generate`, {
      method: "POST",
      body: JSON.stringify({ fiscal_period: payload.fiscal_period }),
      headers: getAuthHeaders(),
    });
  },

  // Note: Streaming is handled via EventSource in use-report-stream.ts, not here.
  // Note: Downloading is a direct browser navigation or fetch blob approach.
};
