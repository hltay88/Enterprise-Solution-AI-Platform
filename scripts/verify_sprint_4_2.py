#!/usr/bin/env python3
"""Sprint 4.2 verify — presentation unit subset + route registration."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV_PY = BACKEND / ".venv" / "bin" / "python"


def main() -> int:
    print("Sprint 4.2 verify — unit subset")
    py = str(VENV_PY if VENV_PY.exists() else sys.executable)
    tests = [
        "tests/test_presentation_content_schema.py",
        "tests/test_presentation_validation.py",
        "tests/test_pptx_renderer.py",
        "tests/test_source_snapshot_gate.py",
        "tests/test_proposal_content_schema.py",
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
                "from app.ai.factory import get_ai_provider;"
                "import asyncio;"
                "p=get_ai_provider();"
                "assert hasattr(p,'generate_presentation_content');"
                "from app.api.v1_router import v1_router;"
                "paths=sorted({getattr(r,'path','') for r in v1_router.routes});"
                "assert any('deliverables/generate' in p for p in paths);"
                "print('OK: presentation AI + routes')"
            ),
        ],
        cwd=BACKEND,
        check=False,
    )
    if check.returncode != 0:
        return check.returncode
    print("Sprint 4.2 unit verify passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
