"""Sprint 3.1 Task 2 — domain / traceability schema freeze."""

from __future__ import annotations

from pathlib import Path

from app.models import (
    DomainAnalysis,
    DomainDependency,
    DomainOpenQuestion,
    DomainRequirementLink,
    RequirementTraceability,
    SolutionDomain,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_SQL = REPO_ROOT / "docker" / "postgres" / "init" / "07_phase3_domains.sql"
SCHEMA_PY = REPO_ROOT / "backend" / "app" / "db" / "schema.py"

EXPECTED_TABLES = (
    "domain_analyses",
    "solution_domains",
    "domain_requirement_links",
    "domain_dependencies",
    "domain_open_questions",
    "requirement_traceability",
)


def test_init_sql_defines_sprint_3_1_tables():
    sql = INIT_SQL.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS solution_projects" not in sql
    assert "REFERENCES projects" in sql
    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


def test_ensure_schema_mirrors_domain_tables():
    source = SCHEMA_PY.read_text(encoding="utf-8")
    for table in EXPECTED_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {table}" in source


def test_orm_table_names():
    assert DomainAnalysis.__tablename__ == "domain_analyses"
    assert SolutionDomain.__tablename__ == "solution_domains"
    assert DomainRequirementLink.__tablename__ == "domain_requirement_links"
    assert DomainDependency.__tablename__ == "domain_dependencies"
    assert DomainOpenQuestion.__tablename__ == "domain_open_questions"
    assert RequirementTraceability.__tablename__ == "requirement_traceability"


def test_domain_analysis_has_audit_metadata_columns():
    columns = set(DomainAnalysis.__table__.columns.keys())
    for name in (
        "rkm_id",
        "rkm_version_label",
        "knowledge_pack_version",
        "prompt_version",
        "model",
        "payload_json",
        "created_by",
    ):
        assert name in columns


def test_traceability_keeps_later_stage_columns_nullable():
    table = RequirementTraceability.__table__
    assert table.c.architecture_id.nullable is True
    assert table.c.component_id.nullable is True
    assert table.c.decision_id.nullable is True
    assert table.c.domain_id.nullable is True
    assert str(table.c.requirement_id.type) in {"TEXT", "Text"}


def test_requirement_link_uses_text_requirement_id():
    col = DomainRequirementLink.__table__.c.requirement_id
    assert str(col.type) in {"TEXT", "Text"}
    assert col.nullable is False


def test_solution_domain_unique_analysis_code_constraint():
    names = {c.name for c in SolutionDomain.__table__.constraints if c.name}
    assert "uq_solution_domains_analysis_code" in names
