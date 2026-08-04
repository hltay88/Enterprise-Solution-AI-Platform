/** ATLAS-014 API envelope types */

export type ApiErrorBody = {
  code: string;
  message: string;
};

export type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  message: string | null;
  error?: ApiErrorBody | null;
};

export type HealthData = {
  status: string;
  database: string;
};

export type UserPublic = {
  id: string;
  name: string;
  email: string;
};

export type LoginData = {
  access_token: string;
  token_type: string;
  user: UserPublic;
};

export type ProjectSummary = {
  id: string;
  project_name: string;
  customer: string | null;
  industry: string | null;
  status: string;
  account_manager: string | null;
  deal_id: string | null;
  deal_name: string | null;
  pic_name: string | null;
  pic_contact: string | null;
  pic_designation: string | null;
  budget_information: string | null;
  request_type: string | null;
  required_completion_date: string | null;
  requirement_details: string | null;
  winning_probability: number | null;
  created_at: string;
  updated_at: string;
};

export type ProjectInput = {
  project_name: string;
  customer: string;
  industry?: string | null;
  status?: string;
  account_manager?: string | null;
  deal_id: string;
  deal_name: string;
  pic_name: string;
  pic_contact?: string | null;
  pic_designation?: string | null;
  budget_information?: string | null;
  request_type: string;
  required_completion_date?: string | null;
  requirement_details: string;
  winning_probability?: number | null;
};

export const REQUEST_TYPES = [
  "Technical Clarification",
  "Proposal",
  "Initial Discovery",
  "POC",
  "BOM",
  "SOW",
] as const;

export type DocumentSummary = {
  id: string;
  project_id: string;
  filename: string;
  file_type: string;
  storage_path: string;
  uploaded_at: string;
  extracted_text: string | null;
  extracted_preview: string | null;
  content_sha256?: string | null;
  file_size_bytes?: number | null;
  mime_type?: string | null;
  status?: string;
  page_count?: number | null;
  language?: string | null;
  ocr_used?: boolean;
  needs_manual_review?: boolean;
  error_message?: string | null;
  processing_job_id?: string | null;
  duplicate_of?: string | null;
  metadata?: Record<string, string | null>;
};

export type JobStatus = {
  id: string;
  project_id: string;
  document_id: string | null;
  job_type: string;
  status: string;
  progress: number;
  error_message: string | null;
  result_json: Record<string, unknown> | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type DocumentUploadItem = {
  document: DocumentSummary;
  job: JobStatus | null;
  duplicate: boolean;
};

export type DocumentUploadBatchResult = {
  project_id: string;
  items: DocumentUploadItem[];
  accepted_count: number;
  duplicate_count: number;
};

export type AnalysisResult = {
  id: string;
  project_id: string;
  business_objectives: string | null;
  functional_requirements: string | null;
  non_functional_requirements: string | null;
  assumptions: string | null;
  risks: string | null;
  analysis_json: Record<string, unknown> | null;
  created_at: string;
};

export type AiStatus = {
  provider: string;
  configured: boolean;
  model: string;
  key_prefix: string | null;
  key_length: number;
  reachable: boolean;
  fallback_enabled: boolean;
  gemini_configured?: boolean;
  openai_configured?: boolean;
  detail: string | null;
};

export type ClarificationQuestion = {
  id: string;
  project_id: string;
  question: string;
  status: string;
  created_at: string;
};
