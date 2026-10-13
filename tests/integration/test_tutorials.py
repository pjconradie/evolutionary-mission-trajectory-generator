"""Verify current tutorial inputs against pinned immutable references."""

import pytest

from testatron import ipopt_characterization


pytestmark = [
	pytest.mark.integration,
    pytest.mark.tutorials,
    pytest.mark.docker,
    pytest.mark.ipopt_backend,
    pytest.mark.solver_runtime,
	pytest.mark.ipopt_verification,
]

REPLAY_CASES = ipopt_characterization.TUTORIAL_CASES
REFINEMENT_CASES = tuple(
    case
    for case in ipopt_characterization.TUTORIAL_CASES
    if "refinement" in case.stages
)


def _assert_declared_comparison_outcome(case, comparison):
    failed_checks = {
        name for name, passed in comparison["checks"].items() if not passed
    }
    assert failed_checks == set(case.expected_refinement_failed_checks)
    assert comparison["acceptable"] is not bool(failed_checks)


@pytest.mark.parametrize("case", REPLAY_CASES, ids=lambda case: case.case_id)
def test_tutorial_replay(case, tutorial_stage_runner):
    if case.expected_schema_lengths is not None:
        source_length, reference_length = case.expected_schema_lengths
        with pytest.raises(
            ValueError,
            match=(
                "Decision variable description lengths differ: "
                f"{source_length} != {reference_length}"
            ),
        ):
            tutorial_stage_runner(case, "replay")
        return

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
    if case.expected_schema_lengths is not None:
        source_length, reference_length = case.expected_schema_lengths
        with pytest.raises(
            ValueError,
            match=(
                "Decision variable description lengths differ: "
                f"{source_length} != {reference_length}"
            ),
        ):
            tutorial_stage_runner(case, "refinement")
        return

    result = tutorial_stage_runner(case, "refinement")

    assert result["tutorial_refinement_compile"] == "passed"
    assert result["tutorial_refinement_run"] == "passed"
    assert result["comparison"]["status"] == "unreviewed"
    _assert_declared_comparison_outcome(case, result["comparison"])
    assert result["result"]["status"] == "unreviewed"
    assert result["result"]["acceptable"] is result["comparison"]["acceptable"]
