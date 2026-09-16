"""Verify current tutorial inputs against pinned immutable references."""

import pytest

from testatron import ipopt_characterization


pytestmark = [
    pytest.mark.tutorials,
    pytest.mark.docker,
    pytest.mark.ipopt_backend,
    pytest.mark.solver_runtime,
]

REPLAY_CASES = ipopt_characterization.TUTORIAL_CASES
REFINEMENT_CASES = tuple(
    case
    for case in ipopt_characterization.TUTORIAL_CASES
    if "refinement" in case.stages
)


@pytest.mark.parametrize("case", REPLAY_CASES, ids=lambda case: case.case_id)
def test_tutorial_replay(case, tutorial_stage_runner):
    result = tutorial_stage_runner(case, "replay")

    assert result["tutorial_replay_compile"] == "passed"
    assert result["tutorial_replay_run"] == "passed"
    assert result["tutorial_replay_no_ipopt"] == "passed"
    assert result["comparison"]["status"] == "unreviewed"
    assert result["comparison"]["acceptable"]
    assert all(result["comparison"]["checks"].values())
    assert result["result"]["status"] == "unreviewed"
    assert result["result"]["acceptable"]


@pytest.mark.parametrize("case", REFINEMENT_CASES, ids=lambda case: case.case_id)
def test_tutorial_ipopt_refinement(case, tutorial_stage_runner):
    result = tutorial_stage_runner(case, "refinement")

    assert result["tutorial_refinement_compile"] == "passed"
    assert result["tutorial_refinement_run"] == "passed"
    assert result["comparison"]["status"] == "unreviewed"
    assert result["comparison"]["acceptable"]
    assert all(result["comparison"]["checks"].values())
    assert result["result"]["status"] == "unreviewed"
    assert result["result"]["acceptable"]
