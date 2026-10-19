"""Verify the extracted EMTG archive against all tutorial references."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path, PurePosixPath

import Mission
import MissionOptions
import pytest

from emtg_toolchain import cli
from emtg_toolchain.archive import (
    ARCHIVE_ROOT,
    read_archive_text,
    validate_archive,
    validate_checksum,
)
from emtg_toolchain.docker import (
    build_archive_runtime_image,
    remove_image,
    run_archive_runtime,
)
from emtg_toolchain.runtime import parse_runtime_requirements
from emtg_toolchain.release import release_baseline_record
from testatron import ipopt_characterization


pytestmark = [
    pytest.mark.tutorials,
    pytest.mark.docker,
    pytest.mark.ipopt_backend,
    pytest.mark.solver_runtime,
]


def _write_stage_result(directory: Path, result: dict) -> None:
    (directory / "result.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )


def _runtime_stage(
    *,
    image: str,
    case,
    stage: str,
    artifacts: Path,
    repository_root: Path,
    schema_cache: dict[Path, list[str]],
) -> dict:
    """Prepare, execute, and compare one tutorial stage using the archive image."""
    attempt_root = artifacts.parent
    schema_descriptions = None
    try:
        if case.schema_probe:
            if attempt_root not in schema_cache:
                schema_directory = attempt_root / "schema"
                schema_directory.mkdir(exist_ok=True)
                schema_options = ipopt_characterization.prepare_tutorial_schema_probe(
                    case,
                    schema_directory,
                    repository_root=repository_root,
                )
                schema_run = run_archive_runtime(
                    image,
                    schema_directory,
                    schema_options.name,
                    case.timeout_seconds,
                    mount_path="/artifacts",
                )
                (schema_directory / "run.log").write_text(
                    schema_run.stdout + schema_run.stderr, encoding="utf-8"
                )
                if schema_run.returncode:
                    raise ValueError(
                        f"schema probe exited with {schema_run.returncode} for {case.case_id}"
                    )
                schema_files = sorted(schema_directory.glob("*XFfile.csv"))
                if not schema_files:
                    raise ValueError(f"schema probe wrote no XFfile for {case.case_id}")
                schema_cache[attempt_root] = ipopt_characterization.load_xf_descriptions(
                    schema_files[0]
                )
            schema_descriptions = schema_cache[attempt_root]

        options_path = ipopt_characterization.prepare_tutorial_case(
            case,
            stage,
            artifacts,
            repository_root=repository_root,
            schema_descriptions=schema_descriptions,
        )
        options = MissionOptions.MissionOptions(str(options_path))
        mission_name = options.mission_name
        replaying_infeasible_seed = (
            stage == "replay"
            and case.replay_seed_source == "current_infeasible_trial"
        )
        generated_name = (
            f"FAILURE_{mission_name}.emtg"
            if case.expected_output == "failure" or replaying_infeasible_seed
            else f"{mission_name}.emtg"
        )
        started = time.monotonic()
        execution = run_archive_runtime(
            image,
            artifacts,
            options_path.name,
            case.timeout_seconds,
            mount_path="/artifacts",
        )
        duration_seconds = time.monotonic() - started
        log_path = artifacts / "run.log"
        log_path.write_text(execution.stdout + execution.stderr, encoding="utf-8")
        if execution.returncode == 124:
            result = {
                "classification": "timed_out",
                "acceptable": False,
                "detail": f"EMTG timed out after {case.timeout_seconds} seconds",
            }
            _write_stage_result(artifacts, result)
            return result
        if execution.returncode:
            result = {
                "classification": "process_failed",
                "acceptable": False,
                "detail": f"EMTG exited with {execution.returncode}",
            }
            _write_stage_result(artifacts, result)
            return result

        generated_path = artifacts / generated_name
        if not generated_path.is_file() or not generated_path.stat().st_size:
            result = {
                "classification": "parse_failed",
                "acceptable": False,
                "detail": f"expected tutorial output is missing: {generated_name}",
            }
            _write_stage_result(artifacts, result)
            return result

        baseline = Mission.Mission(str(repository_root / case.reference_mission))
        generated = Mission.Mission(str(generated_path))
        feasibility_tolerance = options.snopt_feasibility_tolerance
        if case.taxonomy == "deliberate_infeasible" or replaying_infeasible_seed:
            comparison = ipopt_characterization.compare_deliberate_infeasible(
                baseline, generated, feasibility_tolerance
            )
        elif stage == "replay":
            comparison = ipopt_characterization.compare_replay(baseline, generated)
            comparison["feasibility_tolerance"] = feasibility_tolerance
            comparison["feasible"] = (
                comparison["generated_feasibility_metric"] <= feasibility_tolerance
            )
            comparison["acceptable"] = (
                comparison["acceptable"] and comparison["feasible"]
            )
        else:
            comparison = ipopt_characterization.compare_refinement(
                baseline,
                generated,
                feasibility_tolerance,
                objective_policy=ipopt_characterization.tutorial_objective_policy(case),
                objective_sense=ipopt_characterization.objective_sense(
                    options.objective_type
                ),
            )
            diagnostics = ipopt_characterization.parse_ipopt_log(
                log_path.read_text(errors="replace"),
                initialization_policy=(
                    "infeasible-primal-seed"
                    if case.refinement_seed_source == "current_infeasible_trial"
                    else None
                ),
            )
            if case.refinement_seed_source == "archive":
                comparison["checks"]["near_feasible_initialization"] = (
                    diagnostics["initial_infeasibility"] <= feasibility_tolerance
                )
            else:
                comparison["checks"]["expected_infeasible_initialization"] = (
                    diagnostics["initial_infeasibility"] > feasibility_tolerance
                )
            comparison["checks"]["ipopt_native_success"] = (
                diagnostics["native_exit"] == "Optimal Solution Found."
            )
            comparison["acceptable"] = all(comparison["checks"].values())
            comparison["ipopt"] = diagnostics

        comparison["duration_seconds"] = duration_seconds
        (artifacts / "comparison.json").write_text(
            json.dumps(comparison, indent=2) + "\n", encoding="utf-8"
        )
        result = {
            "classification": "completed",
            "acceptable": comparison["acceptable"],
            "comparison": comparison,
            "output_file": generated_path.name,
        }
        _write_stage_result(artifacts, result)
        ipopt_characterization.write_tutorial_provenance(
            artifacts, case, stage, [generated_path], repository_root
        )
        return result
    except ValueError as error:
        result = {
            "classification": ipopt_characterization.classify_tutorial_preflight_error(
                error
            ),
            "acceptable": False,
            "detail": str(error),
        }
        _write_stage_result(artifacts, result)
        ipopt_characterization.write_tutorial_provenance(
            artifacts, case, stage, [], repository_root
        )
        return result


def test_extracted_archive_passes_all_tutorial_verification(
    repository_root,
    emtg_toolchain_artifact_root,
    emtg_archive_cold,
    request,
):
    """Require all 17 tutorial cases and 33 stages to match reviewed evidence."""
    artifact_root = emtg_toolchain_artifact_root
    release_archive = request.config.getoption("--release-archive")
    if release_archive is None:
        archive = artifact_root / "emtg-ipopt.tar.gz"
        cli.package(
            repository_root,
            archive,
            cold=emtg_archive_cold,
            build_log_path=artifact_root / "source-build.log",
        )
        (artifact_root / "archive-build-mode.txt").write_text(
            f"{'cold' if emtg_archive_cold else 'hot'}\n",
            encoding="ascii",
        )
    else:
        archive = release_archive.expanduser().resolve()
        checksum = archive.with_name(f"{archive.name}.sha256")
        if not archive.is_file():
            raise ValueError(f"release archive does not exist: {archive}")
        if not checksum.is_file():
            raise ValueError(f"release archive checksum does not exist: {checksum}")
        validate_archive(archive)
        validate_checksum(archive, checksum)
        shutil.copy2(checksum, artifact_root / checksum.name)
    requirements = read_archive_text(
        archive, PurePosixPath(ARCHIVE_ROOT, "RUNTIME_REQUIREMENTS.txt")
    )
    image = build_archive_runtime_image(
        archive,
        parse_runtime_requirements(requirements),
        log_path=artifact_root / "runtime-image-build.log",
    )
    (artifact_root / "runtime-image.txt").write_text(f"{image}\n", encoding="utf-8")
    output_root = artifact_root / "evidence"
    schema_cache: dict[Path, list[str]] = {}

    def stage_runner(case, stage, artifacts):
        return _runtime_stage(
            image=image,
            case=case,
            stage=stage,
            artifacts=Path(artifacts),
            repository_root=repository_root,
            schema_cache=schema_cache,
        )

    try:
        cases = ipopt_characterization.TUTORIAL_CASES
        print(
            f"Verifying archive tutorials: {len(cases)} cases, "
            "33 required stages, two attempts per case"
        )
        for index, case in enumerate(cases, start=1):
            started = time.monotonic()
            print(f"[{index}/{len(cases)}] Starting {case.case_id}")
            result = ipopt_characterization.run_repeatable_tutorial_baselining_case(
                case,
                stage_runner,
                output_root=output_root,
                repository_root=repository_root,
            )
            assert result["repeatability"]["stable"], case.case_id
            print(
                f"[{index}/{len(cases)}] Completed {case.case_id} "
                f"in {time.monotonic() - started:.1f}s"
            )
        verification = ipopt_characterization.verify_tutorial_baselining_verification(
            output_root
        )
    finally:
        remove_image(image)

    (artifact_root / "verification.json").write_text(
        json.dumps(verification, indent=2) + "\n", encoding="utf-8"
    )
    if release_archive is not None:
        release_record = release_baseline_record(
            archive=archive,
            requirements=requirements,
            verification=verification,
            verification_reference=(
                ipopt_characterization.DEFAULT_TUTORIAL_BASELINING_VERIFICATION
            ),
            evidence_root=artifact_root,
        )
        (artifact_root / "release-baseline.json").write_text(
            json.dumps(release_record, indent=2) + "\n", encoding="utf-8"
        )
    assert verification["case_count"] == 17
    assert verification["stage_count"] == 33
    assert verification["acceptable"], verification["stages"]
