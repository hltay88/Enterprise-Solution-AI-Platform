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
  created_at: string;
  updated_at: string;
};

export type ProjectInput = {
  project_name: string;
  customer?: string | null;
  industry?: string | null;
  status?: string;
};

export type DocumentSummary = {
  id: string;
  project_id: string;
  filename: string;
  file_type: string;
  storage_path: string;
  uploaded_at: string;
  extracted_text: string | null;
  extracted_preview: string | null;
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
  detail: string | null;
};

export type ClarificationQuestion = {
  id: string;
  project_id: string;
  question: string;
  status: string;
  created_at: string;
};
