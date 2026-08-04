"""Processing job persistence (ATLAS-029)."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.processing_job import ProcessingJob


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, job_id: UUID) -> ProcessingJob | None:
        return self.db.scalars(
            select(ProcessingJob).where(ProcessingJob.id == job_id),
        ).first()

    def latest_for_document(self, document_id: UUID) -> ProcessingJob | None:
        return self.db.scalars(
            select(ProcessingJob)
            .where(ProcessingJob.document_id == document_id)
            .order_by(ProcessingJob.created_at.desc()),
        ).first()

    def create(
        self,
        *,
        project_id: UUID,
        document_id: UUID | None,
        job_type: str = "document_extract",
        status: str = "queued",
    ) -> ProcessingJob:
        job = ProcessingJob(
            project_id=project_id,
            document_id=document_id,
            job_type=job_type,
            status=status,
            progress=0,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_started(self, job: ProcessingJob) -> ProcessingJob:
        job.status = "processing"
        job.progress = 10
        job.started_at = datetime.now(timezone.utc)
        job.error_message = None
        return self.save(job)

    def mark_progress(self, job: ProcessingJob, progress: int) -> ProcessingJob:
        job.progress = max(0, min(100, progress))
        return self.save(job)

    def mark_completed(self, job: ProcessingJob, result: dict | None = None) -> ProcessingJob:
        job.status = "completed"
        job.progress = 100
        job.completed_at = datetime.now(timezone.utc)
        job.result_json = result
        job.error_message = None
        return self.save(job)

    def mark_failed(self, job: ProcessingJob, message: str) -> ProcessingJob:
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = message
        return self.save(job)

    def save(self, job: ProcessingJob) -> ProcessingJob:
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
