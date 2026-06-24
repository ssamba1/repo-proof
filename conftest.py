"""Make the `proof` package importable in tests without installing it, and expose the
fixtures directory + a toolchain-availability helper used to skip integration tests
when an interpreter is not present.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FIXTURES = ROOT / "fixtures"


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def repo_root() -> Path:
    return ROOT
