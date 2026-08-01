"""Document API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentSummary(BaseModel):
    id: UUID
    project_id: UUID
    filename: str
    file_type: str
    storage_path: str
    uploaded_at: datetime
    extracted_text: str | None = None
    extracted_preview: str | None = None

    model_config = {"from_attributes": True}
