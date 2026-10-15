"""Run selected tutorial cases through repeatable IPOPT baselining."""

import json

import pytest

from _docker_support import artifact_directory
from testatron import ipopt_characterization


pytestmark = [
    pytest.mark.integration,
    pytest.mark.tutorials,
    pytest.mark.docker,
    pytest.mark.ipopt_backend,
    pytest.mark.solver_runtime,
]


def test_tutorial_baselining_cli_writes_fixed_mirrored_layout(
    request,
    repository_root,
    tmp_path_factory,
    tutorial_baselining_stage_runner,
):
    """Run selected tutorial cases twice with case-scoped staged evidence."""
    filters = request.config.getoption("tutorial_baselining_filter")
    cases = ipopt_characterization.discover_tutorial_cases(filters)
    if not cases:
        pytest.fail(
            "No tutorial case matches baselining filter(s): "
            f"{filters or ['<all tutorials>']}"
        )
    output_root = artifact_directory(tmp_path_factory)
    for case in cases:
        result = ipopt_characterization.run_repeatable_tutorial_baselining_case(
            case,
            tutorial_baselining_stage_runner,
            output_root=output_root,
            repository_root=repository_root,
        )
        case_root = output_root / "baselining" / case.case_id
        required_paths = (
            case_root / "attempt-1" / "inventory.json",
            case_root / "attempt-1" / "result.json",
            case_root / "attempt-2" / "inventory.json",
            case_root / "attempt-2" / "result.json",
            case_root / "repeatability.json",
            case_root / "result.json",
        )
        assert all(path.is_file() for path in required_paths)
        assert result["repeatability"]["stable"]
        assert result["classification"] != "unstable"
        for attempt_name in ("attempt-1", "attempt-2"):
            attempt_root = case_root / attempt_name
            assert (attempt_root / "replay" / "result.json").is_file()
            if "refinement" in case.stages:
                assert (attempt_root / "refinement" / "result.json").is_file()
            else:
                assert not (attempt_root / "refinement").exists()
        persisted = json.loads((case_root / "result.json").read_text())
        assert persisted == result
