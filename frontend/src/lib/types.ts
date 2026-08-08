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

export type RkmEvidence = {
  id: string;
  source_type: "document" | "sales_intake" | "workshop" | "clarification_answer" | string;
  document_id: string | null;
  page: number | null;
  excerpt: string | null;
  field_name: string | null;
  note: string | null;
};

export type RkmRequirement = {
  id: string;
  category: string | null;
  subcategory: string | null;
  title: string;
  description: string;
  priority: string;
  status: string;
  confidence: number;
  evidence_ids: string[];
};

export type RkmStakeholder = {
  id: string;
  name: string;
  role: string | null;
  contact: string | null;
  designation: string | null;
  evidence_ids: string[];
};

export type RkmDraft = {
  id: string;
  project_id: string;
  project: {
    project_name: string;
    customer: string | null;
    industry: string | null;
    account_manager: string | null;
    deal_id: string | null;
    deal_name: string | null;
    request_type: string | null;
    required_completion_date: string | null;
    budget_information: string | null;
    winning_probability: number | null;
  };
  business_objectives: RkmRequirement[];
  current_environment: {
    summary: string;
    items: Array<{
      id: string;
      title: string;
      description: string;
      evidence_ids: string[];
    }>;
  };
  functional_requirements: RkmRequirement[];
  non_functional_requirements: RkmRequirement[];
  constraints: RkmRequirement[];
  dependencies: RkmRequirement[];
  risks: RkmRequirement[];
  assumptions: RkmRequirement[];
  stakeholders: RkmStakeholder[];
  clarification_questions: unknown[];
  evidence: RkmEvidence[];
  analysis: {
    confidence_score: number;
    completeness_score: number;
    consistency_score: number;
    evidence_coverage: number;
    reasoning_summary: string;
    prompt_version: string | null;
    model: string | null;
  };
  approval: {
    status: string;
    reviewed_by: string | null;
    approved_by: string | null;
    approved_at: string | null;
    published_at: string | null;
  };
  version: {
    number: string;
    major: number;
    minor: number;
    patch: number;
    created_at: string;
    updated_at: string;
    change_summary: string | null;
  };
};

export type RkmVersionSummary = {
  id: string;
  project_id: string;
  status: string;
  version_label: string;
  is_active_draft: boolean;
  confidence_score: number;
  completeness_score: number;
  created_at: string;
  updated_at: string;
};

export type RkmAnalyzeAccepted = {
  project_id: string;
  job_id: string;
  status: string;
  message: string;
};

export type RkmClarification = {
  id: string;
  question: string;
  priority: string;
  category: string;
  reason: string;
  affected_requirement_ids: string[];
  status: string;
  answer: string | null;
  confidence_impact?: number | null;
};

export type GapItem = {
  code: string;
  section: string;
  severity: string;
  message: string;
  affected_requirement_ids: string[];
};

export type GapAnalysisReport = {
  project_id: string;
  rkm_id: string;
  version_label: string;
  completeness_score: number;
  confidence_score: number;
  consistency_score: number;
  evidence_coverage: number;
  overall_quality: number;
  quality_level: string;
  missing_sections: string[];
  gaps: GapItem[];
  conflicts: Array<{
    code: string;
    message: string;
    affected_requirement_ids: string[];
  }>;
  publish_blockers: Array<{ code: string; message: string }>;
  clarifications: RkmClarification[];
  created_at: string | null;
};

export type ClarificationAnswerResult = {
  project_id: string;
  rkm_id: string;
  version_label: string;
  answered_count: number;
  clarifications: RkmClarification[];
  draft: RkmDraft | null;
};

export type ReviewResult = {
  project_id: string;
  rkm_id: string;
  version_label: string;
  edited_count: number;
  draft: RkmDraft;
};

export type ApproveResult = {
  project_id: string;
  rkm_id: string;
  version_label: string;
  status: string;
  approved_by: string | null;
  approved_at: string | null;
  draft: RkmDraft;
};

export type PublishResult = {
  project_id: string;
  rkm_id: string;
  version_label: string;
  status: string;
  published_at: string;
  draft: RkmDraft;
  publish_blockers: Array<{ code: string; message: string }>;
};

export type VersionDiffItem = {
  section: string;
  change_type: "added" | "removed" | "modified" | string;
  item_id: string | null;
  title: string | null;
  before: string | null;
  after: string | null;
};

export type VersionCompare = {
  project_id: string;
  from_version: string;
  to_version: string;
  from_status: string;
  to_status: string;
  from_reasoning: string;
  to_reasoning: string;
  diffs: VersionDiffItem[];
  summary: {
    added?: number;
    removed?: number;
    modified?: number;
    reasoning_changed?: boolean;
  };
};
