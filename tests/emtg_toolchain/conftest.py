"""Shared fixtures for archive-toolchain tests."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def emtg_archive_cold() -> bool:
    """Return whether this archive test must bypass the package build cache."""
    value = os.environ.get("EMTG_ARCHIVE_COLD", "").strip().lower()
    if value in {"", "0", "false", "no"}:
        return False
    if value in {"1", "true", "yes"}:
        return True
    pytest.fail(
        "EMTG_ARCHIVE_COLD must be one of: 1, true, yes, 0, false, no"
    )


@pytest.fixture
def emtg_toolchain_artifact_root(tmp_path_factory) -> Path:
    """Create one retained artifact directory when EMTG_TEST_ARTIFACT_DIR is set."""
    configured = os.environ.get("EMTG_TEST_ARTIFACT_DIR")
    if configured:
        root = Path(configured).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="emtg-toolchain-", dir=root))
    return tmp_path_factory.mktemp("emtg-toolchain-artifacts")
