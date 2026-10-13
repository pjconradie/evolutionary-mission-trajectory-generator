"""Collect repeatable, reviewable IPOPT evidence for immutable tutorials."""

import os
import re
from pathlib import Path

import pytest

from _docker_support import artifact_directory
from testatron import ipopt_characterization


pytestmark = [
    pytest.mark.integration,
    pytest.mark.tutorials,
    pytest.mark.tutorial_baselining,
    pytest.mark.docker,
    pytest.mark.ipopt_backend,
    pytest.mark.solver_runtime,
    pytest.mark.ipopt_verification,
]


def _stage_record(result):
    comparison = result["comparison"]
    return {
        "state": "executed",
        "classification": "completed",
        "return_code": 0,
        "output_file": result["result"]["generated_mission"],
        "immutable_comparison": (
            "matched" if comparison["acceptable"] else "mismatch"
        ),
        "comparison": {"checks": comparison["checks"]},
        "ipopt": comparison.get("ipopt"),
    }


def _schema_drift_record(error):
    match = re.search(r"lengths differ: (\d+) != (\d+)", str(error))
    assert match, f"unexpected schema probe failure: {error}"
    return {
        "state": "schema_drift",
        "classification": "schema_drift",
        "return_code": None,
        "output_file": "",
        "immutable_comparison": "schema_drift",
        "comparison": {"checks": {}},
        "schema_lengths": [int(match.group(1)), int(match.group(2))],
    }


@pytest.mark.parametrize(
    "case", ipopt_characterization.TUTORIAL_CASES, ids=lambda case: case.case_id
)
def test_tutorial_baselining_collects_two_attempt_evidence(
    case, tutorial_stage_runner, tmp_path_factory
):
    output_root = Path(
        os.environ.get(
            "EMTG_TUTORIAL_BASELINING_OUTPUT",
            artifact_directory(tmp_path_factory),
        )
    )
    case_root = output_root / "tutorial-baselining" / case.case_id
    attempts = []
    for attempt in ("attempt-1", "attempt-2"):
        stages = {}
        for stage in case.stages:
            try:
                result = tutorial_stage_runner(
                    case,
                    stage,
                    artifact_root=output_root / "tutorial-baselining",
                    attempt=attempt,
                )
            except ValueError as error:
                stages[stage] = _schema_drift_record(error)
                break
            stages[stage] = _stage_record(result)
        attempts.append(stages)

    result = ipopt_characterization.write_tutorial_baselining_case(
        case, case_root, *attempts
    )

    assert (case_root / "attempt-1" / "result.json").is_file()
    assert (case_root / "attempt-2" / "result.json").is_file()
    assert (case_root / "repeatability.json").is_file()
    for attempt in ("attempt-1", "attempt-2"):
        for stage, stage_result in attempts[0].items():
            if stage_result["state"] == "executed":
                assert (case_root / attempt / stage / "summary.json").is_file()
    assert result["repeatability"]["stable"] or result["repeatability"]["differences"]


def test_tutorial_baselining_matches_reviewed_reference(tmp_path_factory):
    output_root = Path(
        os.environ.get(
            "EMTG_TUTORIAL_BASELINING_OUTPUT",
            artifact_directory(tmp_path_factory),
        )
    )
    report = ipopt_characterization.verify_tutorial_verification(
        output_root, ipopt_characterization.DEFAULT_TUTORIAL_VERIFICATION
    )

    assert report["acceptable"], report["cases"]