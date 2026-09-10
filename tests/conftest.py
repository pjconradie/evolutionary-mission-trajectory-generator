"""Shared paths and fixtures for EMTG characterization tests."""

import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PYEMTG_ROOT = REPOSITORY_ROOT / "PyEMTG"
TESTATRON_TESTS_ROOT = REPOSITORY_ROOT / "testatron" / "tests"
OSIRIS_RESULTS_ROOT = (
    REPOSITORY_ROOT
    / "docs"
    / "0_Users"
    / "tutorial"
    / "Tutorial_EMTG_Files"
    / "OSIRIS-REx"
    / "results"
)
OSIRIS_BASELINES = {
    "2022": (
        OSIRIS_RESULTS_ROOT
        / "OSIRIS-REx_11272022_144557"
        / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    ),
    "2024": (
        OSIRIS_RESULTS_ROOT
        / "OSIRIS-REx_412024_11530"
        / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    ),
}

sys.path.insert(0, str(PYEMTG_ROOT))


@pytest.fixture(scope="session")
def repository_root():
    """Return the checked-out EMTG repository root."""
    return REPOSITORY_ROOT


@pytest.fixture(scope="session")
def testatron_truth_files():
    """Return every committed Testatron result used as parser truth data."""
    return sorted(TESTATRON_TESTS_ROOT.glob("**/*.emtg"))


@pytest.fixture(scope="session")
def osiris_baselines():
    """Return the two mandatory OSIRIS-REx solution baselines by vintage."""
    return OSIRIS_BASELINES
