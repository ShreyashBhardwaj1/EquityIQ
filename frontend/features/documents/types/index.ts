export interface DocumentVersion {
  id: string;
  document_id: string;
  version: number;
  storage_path: string;
  changed_by: string;
  change_reason: string;
  created_at: string;
}

export interface ChunkMetadata {
  workspace_id: string;
  company_id: string;
  document_id: string;
  statement_type?: string;
  document_type: string;
  fiscal_year?: number;
  fiscal_period?: string;
  page_number: number;
  chunk_index: number;
  section_heading?: string;
  source_file: string;
  parser_version: string;
  document_version: number;
  parse_version: number;
  created_at: string;
}

export interface ChunkResponse {
  id: string;
  document_id: string;
  content: string;
  page_number: number;
  chunk_index: number;
  section_heading?: string;
  metadata: ChunkMetadata;
}

export interface Document {
  id: string;
  workspace_id: string;
  company_id: string;
  doc_type: string;
  fiscal_period: string;
  storage_path: string;
  parsing_status: "PENDING" | "PARSING" | "COMPLETED" | "FAILED";
  parsing_confidence: number;
  uploaded_by: string;
  created_at: string;
}

export interface DocumentUploadPayload {
  company_id: string;
  doc_type: string;
  fiscal_period: string;
  file: File;
}

export interface DocumentUpdatePayload {
  document_id: string;
  change_reason: string;
  file: File;
}
