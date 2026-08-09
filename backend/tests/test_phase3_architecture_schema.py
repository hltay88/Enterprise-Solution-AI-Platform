"""Sprint 3.2 Task 2 — normalized architecture schema freeze."""

from __future__ import annotations

from pathlib import Path

from app.models import (
    ArchitectureAssumption,
    ArchitectureComponent,
    ArchitectureOption,
    ArchitectureRelationship,
    CapacityNote,
    DesignDecision,
    RequirementTraceability,
    SolutionRisk,
    SolutionScore,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_SQL = REPO_ROOT / "docker" / "postgres" / "init" / "08_phase3_architectures.sql"
SCHEMA_PY = REPO_ROOT / "backend" / "app" / "db" / "schema.py"

EXPECTED_TABLES = (
    "architecture_options",
    "architecture_components",
    "architecture_relationships",
    "design_decisions",
    "architecture_assumptions",
    "solution_risks",
    "solution_scores",
    "capacity_notes",
)


def test_init_sql_defines_sprint_3_2_tables():
    sql = INIT_SQL.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS solution_projects" not in sql
    assert "REFERENCES projects" in sql
    assert "REFERENCES domain_analyses" in sql
    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
    assert "fk_requirement_traceability_architecture_id" in sql
    assert "fk_requirement_traceability_component_id" in sql
    assert "fk_requirement_traceability_decision_id" in sql


def test_ensure_schema_mirrors_architecture_tables():
    source = SCHEMA_PY.read_text(encoding="utf-8")
    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in source
    assert "fk_requirement_traceability_architecture_id" in source


def test_orm_table_names():
    assert ArchitectureOption.__tablename__ == "architecture_options"
    assert ArchitectureComponent.__tablename__ == "architecture_components"
    assert ArchitectureRelationship.__tablename__ == "architecture_relationships"
    assert DesignDecision.__tablename__ == "design_decisions"
    assert ArchitectureAssumption.__tablename__ == "architecture_assumptions"
    assert SolutionRisk.__tablename__ == "solution_risks"
    assert SolutionScore.__tablename__ == "solution_scores"
    assert CapacityNote.__tablename__ == "capacity_notes"


def test_architecture_option_has_domain_and_pack_pins():
    columns = set(ArchitectureOption.__table__.columns.keys())
    for name in (
        "domain_analysis_id",
        "generation_id",
        "candidate_key",
        "pattern_codes",
        "knowledge_pack_version",
        "prompt_version",
        "rkm_id",
        "rkm_version_label",
        "overall_score",
        "payload_json",
    ):
        assert name in columns


def test_capacity_notes_allow_open_question_without_fabricated_result():
    table = CapacityNote.__table__
    assert table.c.result.nullable is True
    assert table.c.open_question.nullable is True
    assert table.c.input_value.nullable is True


def test_traceability_architecture_fks_declared():
    table = RequirementTraceability.__table__
    assert table.c.architecture_id.nullable is True
    assert table.c.component_id.nullable is True
    assert table.c.decision_id.nullable is True
    fk_targets = {
        fk.column.table.name
        for col in (table.c.architecture_id, table.c.component_id, table.c.decision_id)
        for fk in col.foreign_keys
    }
    assert "architecture_options" in fk_targets
    assert "architecture_components" in fk_targets
    assert "design_decisions" in fk_targets


def test_mvp_architecture_models_table_still_documented():
    """ATLAS-034: transitional MVP table remains; new code must not expand it as SoR."""
    mvp = REPO_ROOT / "docker" / "postgres" / "init" / "06_phase3_architecture.sql"
    assert mvp.is_file()
    assert "architecture_models" in mvp.read_text(encoding="utf-8")
