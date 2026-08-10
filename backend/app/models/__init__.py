"""ORM models mapped to Sprint 1 / Phase 2 Postgres schema."""

from app.models.architecture_model import ArchitectureModel
from app.models.architecture_option import (
    ArchitectureAssumption,
    ArchitectureComponent,
    ArchitectureOption,
    ArchitectureRelationship,
    CapacityNote,
    DesignDecision,
    SolutionRisk,
    SolutionScore,
)
from app.models.audit_log import AuditLog
from app.models.clarification_question import ClarificationQuestion
from app.models.document_chunk import DocumentChunk
from app.models.document_metadata import DocumentMetadata
from app.models.document_page import DocumentPage
from app.models.domain_analysis import (
    DomainAnalysis,
    DomainDependency,
    DomainOpenQuestion,
    DomainRequirementLink,
    RequirementTraceability,
    SolutionDomain,
)
from app.models.processing_job import ProcessingJob
from app.models.project import Project
from app.models.requirement_analysis import RequirementAnalysis
from app.models.requirement_document import RequirementDocument
from app.models.requirement_evidence import RequirementEvidence, RequirementEvidenceLink
from app.models.requirement_item import RequirementItem
from app.models.requirement_model import RequirementModel
from app.models.user import User
from app.models.deliverable import (
    ContentItem,
    DocumentApproval,
    DocumentPackage,
    DocumentPackageMember,
    DocumentSection,
    DocumentSourceRef,
    DocumentTemplate,
    DocumentVersion,
    ExportJob,
    GeneratedDocument,
    GenerationRun,
    SourceSnapshot,
    TemplateVersion,
)
from app.models.vendor_bom import (
    ArchitectureProductMapping,
    BomImport,
    BomItem,
    BomValidationResult,
    ProductCapability,
    VendorCatalogue,
    VendorProduct,
)
from app.models.knowledge import (
    KnowledgeAuditEvent,
    KnowledgeChunk,
    KnowledgeItem,
    KnowledgeSource,
    KnowledgeVersion,
    RetrievalResult,
    RetrievalRun,
    TaxonomyDomain,
)

__all__ = [
    "User",
    "Project",
    "RequirementDocument",
    "RequirementAnalysis",
    "ClarificationQuestion",
    "ProcessingJob",
    "DocumentPage",
    "DocumentChunk",
    "DocumentMetadata",
    "RequirementModel",
    "RequirementItem",
    "RequirementEvidence",
    "RequirementEvidenceLink",
    "AuditLog",
    "ArchitectureModel",
    "ArchitectureOption",
    "ArchitectureComponent",
    "ArchitectureRelationship",
    "DesignDecision",
    "ArchitectureAssumption",
    "SolutionRisk",
    "SolutionScore",
    "CapacityNote",
    "DomainAnalysis",
    "SolutionDomain",
    "DomainRequirementLink",
    "DomainDependency",
    "DomainOpenQuestion",
    "RequirementTraceability",
    "VendorCatalogue",
    "VendorProduct",
    "ProductCapability",
    "ArchitectureProductMapping",
    "BomImport",
    "BomItem",
    "BomValidationResult",
    "DocumentTemplate",
    "TemplateVersion",
    "SourceSnapshot",
    "GenerationRun",
    "GeneratedDocument",
    "DocumentVersion",
    "DocumentSection",
    "ContentItem",
    "DocumentSourceRef",
    "DocumentApproval",
    "ExportJob",
    "DocumentPackage",
    "DocumentPackageMember",
    "TaxonomyDomain",
    "KnowledgeItem",
    "KnowledgeVersion",
    "KnowledgeSource",
    "KnowledgeAuditEvent",
    "KnowledgeChunk",
    "RetrievalRun",
    "RetrievalResult",
]
