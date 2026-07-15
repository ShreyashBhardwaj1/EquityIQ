export interface Citation {
  id: string;
  chunk_id: string | null;
  document_id: string;
  document_name: string;
  page_number: number;
  section_heading: string | null;
  snippet_preview: string;
  score: number;
  rank: number;
  semantic_score: number | null;
  keyword_score: number | null;
  hybrid_score: number;
  retrieval_method: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  citations: Citation[];
}

export interface ConversationDetail {
  id: string;
  workspace_id: string;
  user_id: string;
  title: string;
  summary: string | null;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface ChatRequestPayload {
  query_text: string;
  company_id?: string | null;
  conversation_id?: string | null;
}

export interface ChatResponse {
  answer: string;
  confidence_score: number;
  grounding_score: number;
  citations: Citation[];
  conversation_id: string;
  metadata: Record<string, any>;
}

export interface AskResponse {
  answer: string;
  confidence_score: number;
  grounding_score: number;
  citations: Citation[];
  metadata: Record<string, any>;
}
