"""Sprint 3.3 Task 5 — product mapping repository."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.vendor_bom import ArchitectureProductMapping
from app.repositories.architecture_product_mapping_repository import (
    ArchitectureProductMappingRepository,
)


def test_replace_candidates_requires_ids():
    repo = ArchitectureProductMappingRepository(MagicMock())
    with pytest.raises(ValueError, match="component_id"):
        repo.replace_candidates_for_architecture(
            project_id=uuid4(),
            architecture_id=uuid4(),
            created_by=None,
            rows=[{"product_id": uuid4()}],
        )


def test_replace_candidates_adds_rows():
    db = MagicMock()
    repo = ArchitectureProductMappingRepository(db)
    project_id = uuid4()
    architecture_id = uuid4()
    component_id = uuid4()
    product_id = uuid4()

    rows = repo.replace_candidates_for_architecture(
        project_id=project_id,
        architecture_id=architecture_id,
        created_by=uuid4(),
        rows=[
            {
                "component_id": component_id,
                "product_id": product_id,
                "fit_score": 4.2,
                "rationale": "capability match",
                "limitations": "",
            },
        ],
        commit=True,
    )
    assert len(rows) == 1
    assert isinstance(rows[0], ArchitectureProductMapping)
    db.execute.assert_called()
    db.add.assert_called()
    db.commit.assert_called_once()
