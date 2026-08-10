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
  role?: string;
  tenant_id?: string | null;
  tenant_name?: string | null;
};

export type AuditLogEntry = {
  id: string;
  project_id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  summary: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

/** @deprecated Sprint 3.2+ uses ArchitectureOption / ArchitectureGenerateResult */
export type ArchitectureRecommendation = {
  id: string;
  project_id: string;
  rkm_id: string | null;
  rkm_version_label: string | null;
  status: string;
  version_label: string;
  summary: string;
  high_level_architecture: string[];
  logical_architecture: string[];
  physical_architecture: string[];
  technology_stack: Array<{
    layer: string;
    category: string;
    rationale: string;
  }>;
  solution_components: Array<{
    name: string;
    purpose: string;
    maps_to_requirements: string[];
  }>;
  design_assumptions: string[];
  technical_risks: string[];
  architecture_decisions: Array<{
    decision: string;
    rationale: string;
    impact: string;
  }>;
  alternatives: Array<{
    name: string;
    summary: string;
    tradeoffs: string;
  }>;
  reasoning_summary: string;
  model: string | null;
  prompt_version: string | null;
  created_at: string;
  updated_at: string;
};

export type ArchitectureOptionSummary = {
  id: string;
  project_id: string;
  generation_id: string;
  candidate_key: string;
  title: string;
  summary: string;
  status: string;
  confidence: number;
  overall_score: number | null;
  pattern_codes: string[];
  version_label: string;
  rkm_version_label: string | null;
  domain_analysis_id: string | null;
  reviewed_at?: string | null;
  approved_at?: string | null;
  created_at: string;
};

export type ArchitectureComponent = {
  id: string;
  name: string;
  purpose: string;
  component_kind: string;
  sort_order: number;
  maps_to_requirements: string[];
};

export type ArchitectureDecision = {
  id: string;
  decision: string;
  rationale: string;
  impact: string;
};

export type ArchitectureAssumption = {
  id: string;
  architecture_id?: string | null;
  statement: string;
  reason: string;
  affected_component_ids: string[];
  validation_required: boolean;
  status: string;
};

export type ArchitectureRisk = {
  id: string;
  architecture_id?: string | null;
  description: string;
  category: string;
  cause: string;
  impact: string;
  probability: string;
  severity: string;
  mitigation: string;
  owner: string | null;
  related_requirement_ids: string[];
};

export type ArchitectureScore = {
  id: string;
  dimension: string;
  weight: number;
  score: number;
  explanation: string;
};

export type CapacityNote = {
  id: string;
  label: string;
  input_value: string | null;
  unit: string | null;
  method: string | null;
  assumption: string | null;
  result: string | null;
  confidence: number;
  related_requirement_ids: string[];
  open_question: string | null;
};

export type ArchitectureOption = {
  id: string;
  project_id: string;
  rkm_id: string | null;
  rkm_version_label: string | null;
  domain_analysis_id: string | null;
  generation_id: string;
  candidate_key: string;
  title: string;
  summary: string;
  reasoning_summary: string;
  status: string;
  confidence: number;
  overall_score: number | null;
  pattern_codes: string[];
  version_label: string;
  model: string | null;
  prompt_version: string | null;
  knowledge_pack_version: string | null;
  high_level_architecture: string[];
  logical_architecture: string[];
  physical_architecture: string[];
  technology_stack: Array<{
    layer?: string;
    category?: string;
    rationale?: string;
    [key: string]: unknown;
  }>;
  components: ArchitectureComponent[];
  relationships: Array<{
    id: string;
    from_component_id: string;
    to_component_id: string;
    relationship_kind: string;
    description: string;
  }>;
  decisions: ArchitectureDecision[];
  assumptions: ArchitectureAssumption[];
  risks: ArchitectureRisk[];
  scores: ArchitectureScore[];
  capacity_notes: CapacityNote[];
  advantages: string[];
  disadvantages: string[];
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  review_note?: string | null;
  approved_at?: string | null;
  approved_by?: string | null;
  approval_note?: string | null;
  created_at: string;
  updated_at: string;
  payload?: Record<string, unknown>;
};

export type ArchitectureGenerateResult = {
  generation_id: string;
  version_label: string;
  architectures: ArchitectureOption[];
};

export type ArchitectureProductMapping = {
  id: string;
  project_id: string;
  architecture_id: string;
  component_id: string;
  product_id: string;
  fit_score: number | null;
  rationale: string;
  status: "candidate" | "selected" | "rejected" | string;
  preference_kind: string;
  limitations?: string;
  vendor?: string;
  product_model?: string;
  category?: string;
  created_at: string;
  updated_at: string;
};

export type ArchitectureProductMapResult = {
  architecture_id: string;
  unmatched_component_ids: string[];
  mappings: ArchitectureProductMapping[];
};

export type ArchitectureReviewResult = {
  id: string;
  project_id: string;
  status: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  review_note: string | null;
  approved_at: string | null;
  approved_by: string | null;
  approval_note: string | null;
  uncovered_critical_count: number | null;
};

export type BomItem = {
  id: string;
  bom_import_id: string;
  line_number: number;
  vendor: string;
  product_model: string;
  description: string;
  quantity: number | null;
  unit: string | null;
  category: string;
  sku: string | null;
  mapped_product_id: string | null;
  notes: string | null;
  created_at: string;
};

export type BomImport = {
  id: string;
  project_id: string;
  architecture_id: string | null;
  source: string;
  source_filename: string | null;
  notes: string | null;
  item_count: number;
  created_at: string;
  items: BomItem[];
};

export type BomValidationIssue = {
  code: string;
  severity: string;
  message: string;
  bom_item_id: string | null;
  line_number: number | null;
  related_component_id: string | null;
  requires_human_validation: boolean;
};

export type BomValidationResult = {
  id: string;
  bom_import_id: string;
  project_id: string;
  status: string;
  summary: string;
  issues: BomValidationIssue[];
  created_at: string;
};

export type VendorCatalogue = {
  id: string;
  name: string;
  source: string;
  version_label: string;
  product_count: number;
  created_at: string;
};

export type NamedCount = {
  key: string;
  count: number;
};

export type VendorCatalogueAnalytics = {
  catalogue_id: string | null;
  catalogue_name: string | null;
  product_count: number;
  stale_count: number;
  stale_ratio: number;
  average_confidence: number | null;
  by_vendor: NamedCount[];
  by_category: NamedCount[];
  by_lifecycle: NamedCount[];
  by_region: NamedCount[];
  warnings: string[];
};

export type VendorMappingAnalytics = {
  project_id: string;
  architecture_id: string | null;
  mapping_count: number;
  by_status: NamedCount[];
  by_preference_kind: NamedCount[];
  by_vendor: NamedCount[];
  by_lifecycle: NamedCount[];
  fit_score_buckets: NamedCount[];
  component_count: number;
  mapped_component_count: number;
  unmatched_component_count: number;
  unmatched_component_ids: string[];
  coverage_ratio: number;
  stale_mapped_count: number;
  average_fit_score: number | null;
  selected_count: number;
  candidate_count: number;
  rejected_count: number;
  warnings: string[];
};

export type VendorAnalyticsBundle = {
  catalogue: VendorCatalogueAnalytics;
  mappings: VendorMappingAnalytics;
};

export type DomainDependency = {
  id: string | null;
  depends_on_domain_code: string;
  dependency_kind: "required" | "recommended";
  reason: string;
};

export type DomainOpenQuestion = {
  id: string | null;
  domain_id: string | null;
  domain_code: string | null;
  question: string;
  affects_selection: boolean;
  related_requirement_ids: string[];
};

export type SolutionDomain = {
  id: string;
  domain_code: string;
  name: string;
  reason: string;
  confidence: number;
  mandatory_or_optional: "mandatory" | "optional";
  selection_source: "requirement" | "dependency" | "optional_alternative";
  sort_order: number;
  supporting_requirements: string[];
  dependencies: DomainDependency[];
  open_questions: DomainOpenQuestion[];
};

export type DomainTraceabilityRow = {
  id: string;
  project_id: string;
  analysis_id: string;
  requirement_id: string;
  domain_id: string | null;
  domain_code: string | null;
  architecture_id: string | null;
  component_id: string | null;
  decision_id: string | null;
  evidence: string | null;
  status:
    | "covered"
    | "partially_covered"
    | "not_covered"
    | "conflict"
    | "optional";
  created_at: string | null;
  updated_at: string | null;
};

export type DomainAnalysis = {
  id: string;
  project_id: string;
  rkm_id: string | null;
  rkm_version_label: string | null;
  status: string;
  version_label: string;
  summary: string;
  reasoning_summary: string;
  model: string | null;
  prompt_version: string | null;
  knowledge_pack_version: string | null;
  domains: SolutionDomain[];
  open_questions: DomainOpenQuestion[];
  traceability: DomainTraceabilityRow[];
  created_at: string;
  updated_at: string;
  payload?: Record<string, unknown>;
};

export type LoginData = {
  access_token: string;
  token_type: string;
  user: UserPublic;
  tenant_id?: string | null;
  tenants?: TenantSummary[];
};

export type TenantSummary = {
  id: string;
  name: string;
  slug: string;
  status: string;
  role?: string | null;
};

export type TenantMember = {
  membership_id: string;
  user_id: string;
  email: string;
  name: string;
  role: string;
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

export type SourceSnapshot = {
  id: string;
  project_id: string;
  rkm_id: string | null;
  rkm_version_label: string | null;
  architecture_id: string | null;
  architecture_version_label: string | null;
  bom_validated: boolean;
  created_at: string | null;
};

export type GeneratedDocument = {
  id: string;
  project_id: string;
  document_type: string;
  title: string;
  status: string;
  source_snapshot_id: string;
  current_version_id: string | null;
  version_label: string | null;
  bom_validated?: boolean | null;
  created_at: string | null;
  approved_at: string | null;
};

export type DeliverableSection = {
  id: string;
  section_type: string;
  title: string;
  sequence: number;
  status: string;
  confidence: number;
  assumptions: string[];
  content_items: Array<{
    id: string;
    content_type: string;
    text: string;
    review_required: boolean;
    confidence: number;
    structured_data?: Record<string, unknown>;
    source_refs: Array<{ id: string; ref_kind: string; ref_id: string | null; label: string }>;
  }>;
};

export type ExportJob = {
  id: string;
  status: string;
  format: string;
  checksum_sha256: string | null;
  page_count: number | null;
  error: string | null;
  download_name: string | null;
  storage_path: string | null;
};

export type DeliverableValidation = {
  ok: boolean;
  issues: Array<{ code: string; message: string; section_type?: string | null; severity: string }>;
};

export type ConsistencyReport = {
  ok: boolean;
  findings: Array<{
    severity: string;
    message: string;
    document_ids: string[];
    review_required: boolean;
    code: string;
  }>;
};

export type PackageMember = {
  id: string;
  package_id: string;
  document_id: string;
  document_version_id: string;
  document_type: string;
  role: string;
  title?: string | null;
  document_status?: string | null;
  checksum_sha256?: string | null;
};

export type DocumentPackage = {
  id: string;
  project_id: string;
  title: string;
  status: string;
  version_label?: string | null;
  source_snapshot_id: string;
  bom_import_id?: string | null;
  architecture_id?: string | null;
  members: PackageMember[];
  export_storage_path?: string | null;
  export_checksum_sha256?: string | null;
  exported_at?: string | null;
  created_at?: string | null;
};

export type PackageValidation = {
  ok: boolean;
  findings: Array<{
    code: string;
    message: string;
    severity: string;
    document_type?: string | null;
  }>;
};

export type PackageExport = {
  package_id: string;
  status: string;
  storage_path?: string | null;
  checksum_sha256?: string | null;
  download_name?: string | null;
  error?: string | null;
  exported_at?: string | null;
};

/** Sprint 5.1 Enterprise Knowledge Engine */
export type KnowledgeItemSummary = {
  id: string;
  tenant_id: string | null;
  project_id: string | null;
  title: string;
  description: string | null;
  knowledge_type: string;
  domain_code: string;
  owner_user_id: string | null;
  sensitivity: string;
  current_version_id: string | null;
  status: string | null;
  version_label: string | null;
  version_number: number | null;
  created_at: string;
  updated_at: string;
};

export type KnowledgeSource = {
  id: string;
  original_filename: string;
  file_type: string;
  mime_type: string | null;
  storage_path: string;
  size_bytes: number;
  checksum_sha256: string;
  page_count: number | null;
  extract_warnings: unknown[];
  section_hints: unknown[];
  created_at: string;
};

export type KnowledgeVersion = {
  id: string;
  knowledge_item_id: string;
  version_number: number;
  version_label: string;
  status: string;
  content_text: string | null;
  content_location: string | null;
  change_summary: string | null;
  metadata: Record<string, unknown>;
  tags: string[];
  source_document_name: string | null;
  created_by: string | null;
  reviewed_by: string | null;
  approved_by: string | null;
  published_by: string | null;
  reviewed_at: string | null;
  approved_at: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  sources: KnowledgeSource[];
};

export type KnowledgeItemDetail = KnowledgeItemSummary & {
  current_version: KnowledgeVersion | null;
  versions: KnowledgeVersion[];
};

export type TaxonomyDomain = {
  code: string;
  name: string;
  aliases: string[];
  active: boolean;
};

export type KnowledgeType = {
  code: string;
  name: string;
};

export type RetrievalCitation = {
  knowledge_id: string;
  knowledge_version_id: string;
  chunk_id: string;
  title: string;
  version_label: string;
  status: string;
  domain_code?: string | null;
  knowledge_type?: string | null;
  page_number?: number | null;
  section_label?: string | null;
  source_document_name?: string | null;
  excerpt?: string;
};

export type RetrievalHit = {
  rank: number;
  chunk_id: string;
  content: string;
  vector_score?: number | null;
  keyword_score?: number | null;
  fused_score?: number | null;
  citation: RetrievalCitation;
};

export type RetrievalSearchResult = {
  run_id: string;
  query: string;
  insufficient_evidence: boolean;
  review_required?: boolean;
  context_text?: string;
  message?: string | null;
  embedding_provider: string;
  embedding_model: string;
  latency_ms: number;
  hits: RetrievalHit[];
  citations?: RetrievalCitation[];
};

export type AgentSummary = {
  id: string;
  name: string;
  domain_code: string;
  description: string;
  enabled: boolean;
  runnable: boolean;
  version: string;
};

export type AgentCitation = {
  source_kind: string;
  title: string;
  knowledge_id?: string | null;
  knowledge_version_id?: string | null;
  chunk_id?: string | null;
  domain_code?: string | null;
  excerpt?: string;
  ref_label?: string | null;
};

export type SpecialistFinding = {
  code: string;
  statement: string;
  severity: string;
  evidence?: string[];
};

export type SpecialistOutput = {
  agent_id: string;
  domain_code: string;
  status: string;
  summary: string;
  findings: SpecialistFinding[];
  assumptions: string[];
  risks: string[];
  recommendations: string[];
  conflicts: string[];
  confidence: number;
  citations: AgentCitation[];
  tools_used: string[];
};

export type OrchestratorConflict = {
  code: string;
  summary: string;
  agents: string[];
  severity: string;
};

export type AgentToolCall = {
  id: string;
  agent_id?: string | null;
  tool_name: string;
  ok: boolean;
  error?: string | null;
  latency_ms?: number | null;
  created_at: string;
};

export type AgentRunSummary = {
  id: string;
  project_id: string;
  status: string;
  goal?: string | null;
  focus_domains: string[];
  overall_confidence?: number | null;
  conflict_count: number;
  created_at: string;
  completed_at?: string | null;
};

export type AgentRunDetail = AgentRunSummary & {
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  specialists: SpecialistOutput[];
  conflicts: OrchestratorConflict[];
  tool_calls: AgentToolCall[];
  error?: string | null;
  review_required: boolean;
};

export type CommentItem = {
  id: string;
  project_id: string;
  user_id?: string | null;
  parent_id?: string | null;
  body: string;
  resource_type?: string | null;
  resource_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type ReviewRequest = {
  id: string;
  project_id: string;
  resource_type: string;
  resource_id?: string | null;
  requested_by?: string | null;
  assignee_id?: string | null;
  status: string;
  message: string;
  resolution_note?: string | null;
  created_at: string;
  completed_at?: string | null;
};

export type ApprovalRequest = {
  id: string;
  project_id: string;
  resource_type: string;
  resource_id?: string | null;
  requested_by?: string | null;
  assignee_id?: string | null;
  status: string;
  message: string;
  resolution_note?: string | null;
  resolved_by?: string | null;
  created_at: string;
  resolved_at?: string | null;
};

export type ActivityItem = {
  kind: string;
  id: string;
  project_id?: string | null;
  summary: string;
  actor_user_id?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  created_at: string;
  metadata?: Record<string, unknown>;
};

export type AuditEvent = {
  id: string;
  project_id?: string | null;
  user_id?: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  summary: string;
  metadata?: Record<string, unknown>;
  created_at: string;
};

export type UsageSummary = {
  total: number;
  success_count: number;
  failure_count: number;
  by_event_type: Record<string, number>;
  avg_latency_ms?: number | null;
};
