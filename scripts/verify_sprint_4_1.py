#!/usr/bin/env python3
"""Sprint 4.1 smoke checks — import + unit subset.

Full API smoke requires a running Atlas stack with Complete architecture.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV_PY = BACKEND / ".venv" / "bin" / "python"


def main() -> int:
    print("Sprint 4.1 verify — unit subset")
    py = str(VENV_PY if VENV_PY.exists() else sys.executable)
    tests = [
        "tests/test_source_snapshot_gate.py",
        "tests/test_proposal_content_schema.py",
        "tests/test_deliverable_validation.py",
        "tests/test_docx_renderer.py",
    ]
    cmd = [py, "-m", "pytest", "-q", *tests, "--tb=short"]
    result = subprocess.run(cmd, cwd=BACKEND, check=False)
    if result.returncode != 0:
        return result.returncode

    check = subprocess.run(
        [
            py,
            "-c",
            (
                "from app.api.v1_router import v1_router;"
                "paths=sorted({getattr(r,'path','') for r in v1_router.routes});"
                "assert any('deliverables/generate' in p for p in paths);"
                "print('OK: deliverables routes registered')"
            ),
        ],
        cwd=BACKEND,
        check=False,
    )
    if check.returncode != 0:
        return check.returncode
    print("Sprint 4.1 unit verify passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
