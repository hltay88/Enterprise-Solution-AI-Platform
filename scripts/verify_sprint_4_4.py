#!/usr/bin/env python3
"""Sprint 4.4 verify — BOM/package unit subset + route registration."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV_PY = BACKEND / ".venv" / "bin" / "python"


def main() -> int:
    print("Sprint 4.4 verify — unit subset")
    py = str(VENV_PY if VENV_PY.exists() else sys.executable)
    tests = [
        "tests/test_bom_package.py",
        "tests/test_package_schema.py",
        "tests/test_sow_content_schema.py",
        "tests/test_pdf_renderer.py",
        "tests/test_docx_renderer.py",
    ]
    result = subprocess.run(
        [py, "-m", "pytest", "-q", *tests, "--tb=short"],
        cwd=BACKEND,
        check=False,
    )
    if result.returncode != 0:
        return result.returncode

    check = subprocess.run(
        [
            py,
            "-c",
            (
                "from app.api.v1_router import v1_router;"
                "paths=sorted({getattr(r,'path','') for r in v1_router.routes});"
                "assert any('packages/assemble' in p for p in paths);"
                "from app.services.bom_generation_service import BomGenerationService;"
                "from app.services.package_service import PackageService;"
                "from app.services.rendering.xlsx_renderer import render_bom_xlsx;"
                "print('OK: BOM + package routes/services')"
            ),
        ],
        cwd=BACKEND,
        check=False,
    )
    if check.returncode != 0:
        return check.returncode
    print("Sprint 4.4 unit verify passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
