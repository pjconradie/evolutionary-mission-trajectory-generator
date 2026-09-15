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

sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(PYEMTG_ROOT))


def pytest_addoption(parser):
    """Add mutually exclusive test-category selectors."""
    group = parser.getgroup("test categories")
    group.addoption("--unit", action="store_true", help="run only unit tests")
    group.addoption(
        "--integration", action="store_true", help="run only integration tests"
    )
    group.addoption(
        "--regression", action="store_true", help="run only regression tests"
    )
    group.addoption(
        "--clean-bootstrap", action="store_true", help="run only clean-bootstrap tests"
    )
    group.addoption(
        "--tutorials", action="store_true", help="run only tutorial verification tests"
    )


def pytest_collection_modifyitems(config, items):
    """Filter categories and keep clean bootstrap tests explicitly opt-in."""
    selected_categories = [
        category
        for category, selected in (
            ("unit", config.getoption("--unit")),
            ("integration", config.getoption("--integration")),
            ("regression", config.getoption("--regression")),
            ("clean_bootstrap", config.getoption("--clean-bootstrap")),
            ("tutorials", config.getoption("--tutorials")),
        )
        if selected
    ]
    if len(selected_categories) > 1:
        raise pytest.UsageError(
            "--unit, --integration, --regression, --clean-bootstrap, and --tutorials "
            "are mutually exclusive"
        )

    category = selected_categories[0] if selected_categories else None
    clean_bootstrap_requested = (
        category == "clean_bootstrap"
        or "clean_bootstrap" in config.option.markexpr
    )
    tutorials_requested = category == "tutorials" or "tutorials" in config.option.markexpr
    selected = []
    deselected = []
    for item in items:
        category_matches = category is None or category in item.keywords
        bootstrap_matches = (
            clean_bootstrap_requested or "clean_bootstrap" not in item.keywords
        )
        tutorials_match = tutorials_requested or "tutorials" not in item.keywords
        matches = category_matches and bootstrap_matches and tutorials_match
        (selected if matches else deselected).append(item)

    items[:] = selected
    config.hook.pytest_deselected(items=deselected)


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
