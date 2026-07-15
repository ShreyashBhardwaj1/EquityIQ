export interface ReportSummary {
  id: string;
  company_id: string;
  workspace_id: string;
  fiscal_period: string;
  title: string;
  status: "PENDING" | "GENERATING" | "COMPLETED" | "FAILED";
  generated_by: string;
  model_name: string;
  report_template_version: string;
  financial_engine_version: string;
  generation_duration: number;
  created_at: string;
  error_message?: string;
}

export interface ReportDetail extends ReportSummary {
  content: string;
  prompt_version: string;
  rag_version: string;
  embedding_version: string;
  celery_task_id?: string;
}

export interface GenerateReportPayload {
  company_id: string;
  fiscal_period: string;
}

// Internal UI states for streaming viewer
export interface StreamingReportState {
  status: "idle" | "queued" | "progress" | "streaming" | "completed" | "failed";
  progressPercentage: number;
  message: string;
  content: string;
}
