"""Contracts for the unreviewed IPOPT characterization runner."""

import copy
import json
import math
import subprocess
from pathlib import Path

import pytest

from testatron import ipopt_characterization


pytestmark = pytest.mark.unit


def test_discovery_matches_legacy_testatron_inventory(repository_root):
    tests_root = repository_root / "testatron" / "tests"
    legacy_cases = []
    folders = [child for child in tests_root.iterdir() if child.is_dir()]
    for folder in folders + [tests_root]:
        legacy_cases.extend(folder.glob("*.emtgopt"))

    discovered = ipopt_characterization.discover_cases(tests_root)

    assert set(discovered) == set(legacy_cases)
    assert len(discovered) == 137


def test_prepare_case_preserves_optimization_policy(
    repository_root, tmp_path, monkeypatch
):
    source = (
        repository_root
        / "testatron"
        / "tests"
        / "output_options"
        / "outputoptions_frameICRF.emtgopt"
    )
    public_hardware_root = Path(
        "/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/Config_Files/hardware_models"
    )
    monkeypatch.setattr(
        ipopt_characterization, "PUBLIC_HARDWARE_ROOT", public_hardware_root
    )
    _, MissionOptions = ipopt_characterization._load_pyemtg()
    original = MissionOptions.MissionOptions(str(source))
    prepared_path = ipopt_characterization.prepare_case(source, tmp_path)
    prepared = MissionOptions.MissionOptions(str(prepared_path))

    preserved = (
        "run_inner_loop",
        "seed_MBH",
        "MBH_RNG_seed",
        "MBH_max_trials",
        "MBH_max_run_time",
        "snopt_feasibility_tolerance",
        "snopt_optimality_tolerance",
    )
    for attribute in preserved:
        assert getattr(prepared, attribute) == getattr(original, attribute)
    original_trial = [
        (description.replace(": ", ":").strip(), float(value))
        for description, value in original.trialX
    ]
    prepared_trial = [
        (description.replace(": ", ":").strip(), float(value))
        for description, value in prepared.trialX
    ]
    assert prepared_trial == original_trial
    assert prepared.NLP_solver_type == 2
    assert prepared.background_mode == 1
    assert Path(prepared.forced_working_directory) == tmp_path
    assert Path(prepared.HardwarePath) == public_hardware_root
    assert prepared.LaunchVehicleLibraryFile == ipopt_characterization.PUBLIC_NLSII_LIBRARY
    assert prepared.LaunchVehicleKey == original.LaunchVehicleKey
    assert prepared.ThrottleTableFile == ipopt_characterization.INERT_THROTTLE_TABLE
    compatibility = json.loads((tmp_path / "compatibility.json").read_text())
    assert compatibility["status"] == "unreviewed"
    assert [mapping["option"] for mapping in compatibility["mappings"]] == [
        "LaunchVehicleLibraryFile",
        "ThrottleTableFile",
    ]
    assert "does not use throttle-table" in compatibility["mappings"][1]["reason"]
    assert len(prepared.Journeys) == len(original.Journeys)


def test_prepare_case_maps_august_nlsii_library(repository_root, tmp_path):
    source = (
        repository_root
        / "testatron"
        / "tests"
        / "state_representation_tests"
        / "FreePointArrival_IncomingBplaneRpTA_testatron.emtgopt"
    )
    _, MissionOptions = ipopt_characterization._load_pyemtg()
    original = MissionOptions.MissionOptions(str(source))

    prepared_path = ipopt_characterization.prepare_case(source, tmp_path)
    prepared = MissionOptions.MissionOptions(str(prepared_path))

    assert prepared.LaunchVehicleLibraryFile == ipopt_characterization.PUBLIC_NLSII_LIBRARY
    assert prepared.LaunchVehicleKey == original.LaunchVehicleKey
    compatibility = json.loads((tmp_path / "compatibility.json").read_text())
    assert compatibility["mappings"][0]["source"] == "NLSII_August2018.emtg_launchvehicleopt"


def test_prepare_track_acs_replay_injects_aligned_truth_seed(
    repository_root, tmp_path
):
    source = (
        repository_root
        / "testatron/tests/spacecraft_options/"
        "spacecraftoptions_Chem_TrackACSProp.emtgopt"
    )
    baseline = source.with_suffix(".emtg")
    Mission, MissionOptions = ipopt_characterization._load_pyemtg()
    truth = Mission.Mission(str(baseline))

    prepared_path = ipopt_characterization.prepare_replay(
        source, baseline, tmp_path
    )
    prepared = MissionOptions.MissionOptions(str(prepared_path))
    prepared.AssembleMasterDecisionVector()

    assert prepared.run_inner_loop == 0
    assert len(prepared.trialX) == len(truth.DecisionVector)
    assert [
        ipopt_characterization._normalized_description(entry[0])
        for entry in prepared.trialX
    ] == [
        ipopt_characterization._normalized_description(description)
        for description in truth.Xdescriptions
    ]
    assert [float(entry[1]) for entry in prepared.trialX] == truth.DecisionVector
    assert json.loads((tmp_path / "compatibility.json").read_text())[
        "status"
    ] == "unreviewed"


def test_track_acs_replay_comparison_is_pandas_independent(repository_root):
    mission_path = (
        repository_root
        / "testatron/tests/spacecraft_options/"
        "spacecraftoptions_Chem_TrackACSProp.emtg"
    )
    Mission, _ = ipopt_characterization._load_pyemtg()
    baseline = Mission.Mission(str(mission_path))

    comparison = ipopt_characterization.compare_replay(baseline, baseline)

    assert comparison["status"] == "unreviewed"
    assert comparison["acceptable"]
    assert all(comparison["checks"].values())

    misaligned = copy.deepcopy(baseline)
    misaligned.Xdescriptions[0] = "j0p0: wrong variable"
    comparison = ipopt_characterization.compare_replay(baseline, misaligned)
    assert not comparison["acceptable"]
    assert not comparison["checks"]["decision_descriptions"]


def test_prepare_osiris_2024_replay_injects_aligned_nasa_seed(tmp_path):
    Mission, MissionOptions = ipopt_characterization._load_pyemtg()
    baseline_path = (
        ipopt_characterization.OSIRIS_2024_PACKAGE
        / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    )
    baseline = Mission.Mission(str(baseline_path))

    prepared_path = ipopt_characterization.prepare_osiris_2024_replay(
        tmp_path,
        execution_repository_root="/repo",
        execution_directory="/artifacts",
    )
    prepared = MissionOptions.MissionOptions(str(prepared_path))
    prepared.AssembleMasterDecisionVector()

    assert prepared.run_inner_loop == 0
    assert prepared.NLP_solver_type == 2
    assert prepared.universe_folder == (
        "/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS_universe"
    )
    assert prepared.HardwarePath == (
        "/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/"
        "OSIRIS-REx/hardware_models"
    )
    assert prepared.forced_working_directory == "/artifacts"
    assert all(
        journey.central_body_gravity_file == "DoesNotExist.grv"
        for journey in prepared.Journeys
    )
    assert [entry[0] for entry in prepared.trialX] == baseline.Xdescriptions
    assert [float(entry[1]) for entry in prepared.trialX] == baseline.DecisionVector
    assert json.loads((tmp_path / "compatibility.json").read_text())["status"] == (
        "unreviewed"
    )


def test_prepare_and_compare_track_acs_refinement(repository_root, tmp_path):
    source = (
        repository_root
        / "testatron/tests/spacecraft_options/"
        "spacecraftoptions_Chem_TrackACSProp.emtgopt"
    )
    baseline_path = source.with_suffix(".emtg")
    Mission, MissionOptions = ipopt_characterization._load_pyemtg()
    baseline = Mission.Mission(str(baseline_path))

    prepared_path = ipopt_characterization.prepare_refinement(
        source, baseline_path, tmp_path
    )
    prepared = MissionOptions.MissionOptions(str(prepared_path))
    comparison = ipopt_characterization.compare_refinement(
        baseline, baseline, 1.0e-5
    )

    assert prepared.run_inner_loop == 3
    assert prepared.NLP_solver_type == 2
    assert prepared.enable_NLP_chaperone == 1
    assert prepared.quiet_NLP == 0
    assert comparison["status"] == "unreviewed"
    assert comparison["acceptable"]
    assert all(comparison["checks"].values())

    regressed = copy.deepcopy(baseline)
    regressed.objective_value = -0.19376880315047795
    comparison = ipopt_characterization.compare_refinement(
        baseline, regressed, 1.0e-5
    )
    assert not comparison["acceptable"]
    assert not comparison["checks"]["objective_non_regression"]

    nonfinite = copy.deepcopy(baseline)
    nonfinite.ConstraintVector[0] = math.nan
    comparison = ipopt_characterization.compare_refinement(
        baseline, nonfinite, 1.0e-5
    )
    assert not comparison["acceptable"]
    assert not comparison["checks"]["finite_constraint_vector"]

    out_of_bounds = copy.deepcopy(baseline)
    out_of_bounds.Xupperbounds[0] = out_of_bounds.DecisionVector[0] - 1.0
    comparison = ipopt_characterization.compare_refinement(
        baseline, out_of_bounds, 1.0e-5
    )
    assert not comparison["acceptable"]
    assert not comparison["checks"]["decision_vector_in_bounds"]


def test_parse_ipopt_refinement_log():
    log_text = """
EMTG IPOPT initialization policy: near-feasible-primal-seed
iter    objective    inf_pr   inf_du
   0 -4.0888621e-01 8.19e-06 1.00e+00
Number of Iterations....: 8
Constraint violation....: 1.0e-07  2.0e-07
EXIT: Optimal Solution Found.
"""

    diagnostics = ipopt_characterization.parse_ipopt_log(log_text)

    assert diagnostics == {
        "initialization_policy": "near-feasible-primal-seed",
        "initial_infeasibility": 8.19e-06,
        "iterations": 8,
        "terminal_constraint_violation": 2.0e-07,
        "native_exit": "Optimal Solution Found.",
    }

    with pytest.raises(ValueError, match="missing required refinement diagnostics"):
        ipopt_characterization.parse_ipopt_log(
            log_text.replace(
                "EMTG IPOPT initialization policy: near-feasible-primal-seed\n",
                "",
            )
        )


def test_run_case_records_timeout(repository_root, tmp_path, monkeypatch):
    source = (
        repository_root
        / "testatron"
        / "tests"
        / "output_options"
        / "outputoptions_frameICRF.emtgopt"
    )

    def prepare(source_options, case_directory, pyemtg_root):
        prepared = case_directory / source_options.name
        prepared.write_text("NLP_solver_type 2\n")
        return prepared

    def time_out(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(ipopt_characterization, "prepare_case", prepare)
    monkeypatch.setattr(ipopt_characterization.subprocess, "run", time_out)

    result = ipopt_characterization.run_case(source, "EMTGv9", tmp_path, 1.0)

    assert result.classification == "timed_out"
    result_file = tmp_path / "cases" / result.case_id / "result.json"
    assert json.loads(result_file.read_text())["status"] == "unreviewed"


def test_run_case_records_process_failure(repository_root, tmp_path, monkeypatch):
    source = (
        repository_root
        / "testatron"
        / "tests"
        / "output_options"
        / "outputoptions_frameICRF.emtgopt"
    )

    def prepare(source_options, case_directory, pyemtg_root):
        prepared = case_directory / source_options.name
        prepared.write_text("NLP_solver_type 2\n")
        return prepared

    monkeypatch.setattr(ipopt_characterization, "prepare_case", prepare)
    monkeypatch.setattr(
        ipopt_characterization.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 7),
    )

    result = ipopt_characterization.run_case(source, "EMTGv9", tmp_path, 1.0)

    assert result.classification == "process_failed"
    assert result.return_code == 7


def test_run_case_records_missing_dependency(repository_root, tmp_path, monkeypatch):
    source = (
        repository_root
        / "testatron"
        / "tests"
        / "output_options"
        / "outputoptions_frameICRF.emtgopt"
    )

    def prepare(source_options, case_directory, pyemtg_root):
        prepared = case_directory / source_options.name
        prepared.write_text("NLP_solver_type 2\n")
        return prepared

    def missing_dependency(*args, **kwargs):
        kwargs["stdout"].write(
            "EMTG failed with error:\nCannot find missing.emtg_launchvehicleopt\n"
        )
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr(ipopt_characterization, "prepare_case", prepare)
    monkeypatch.setattr(ipopt_characterization.subprocess, "run", missing_dependency)

    result = ipopt_characterization.run_case(source, "EMTGv9", tmp_path, 1.0)

    assert result.classification == "dependency_blocked"
    assert result.detail == "Cannot find missing.emtg_launchvehicleopt"


def test_run_case_records_inline_missing_dependency(repository_root, tmp_path, monkeypatch):
    source = (
        repository_root
        / "testatron"
        / "tests"
        / "output_options"
        / "outputoptions_frameICRF.emtgopt"
    )

    def prepare(source_options, case_directory, pyemtg_root):
        prepared = case_directory / source_options.name
        prepared.write_text("NLP_solver_type 2\n")
        return prepared

    def missing_dependency(*args, **kwargs):
        kwargs["stdout"].write(
            "Error Cannot find throttle table file: missing.ThrottleTable\n"
        )
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr(ipopt_characterization, "prepare_case", prepare)
    monkeypatch.setattr(ipopt_characterization.subprocess, "run", missing_dependency)

    result = ipopt_characterization.run_case(source, "EMTGv9", tmp_path, 1.0)

    assert result.classification == "dependency_blocked"
    assert result.detail == "Cannot find throttle table file: missing.ThrottleTable"


def test_run_case_records_missing_launch_vehicle(repository_root, tmp_path, monkeypatch):
    source = (
        repository_root
        / "testatron"
        / "tests"
        / "output_options"
        / "outputoptions_frameICRF.emtgopt"
    )

    def prepare(source_options, case_directory, pyemtg_root):
        prepared = case_directory / source_options.name
        prepared.write_text("NLP_solver_type 2\n")
        return prepared

    def missing_launch_vehicle(*args, **kwargs):
        kwargs["stdout"].write(
            "LaunchVehicleOptionsLibrary::Launch vehicle 'example' not found.\n"
        )
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr(ipopt_characterization, "prepare_case", prepare)
    monkeypatch.setattr(
        ipopt_characterization.subprocess, "run", missing_launch_vehicle
    )

    result = ipopt_characterization.run_case(source, "EMTGv9", tmp_path, 1.0)

    assert result.classification == "dependency_blocked"
    assert "Launch vehicle 'example' not found" in result.detail


def test_manifests_are_explicitly_unreviewed(tmp_path):
    results = [
        ipopt_characterization.CaseResult(
            case_id="output_options/example",
            source_options="example.emtgopt",
            classification="reviewable",
        )
    ]

    ipopt_characterization.write_manifests(tmp_path, results)

    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["status"] == "unreviewed"
    assert manifest["case_count"] == 1
    assert manifest["classifications"]["reviewable"] == 1
    assert "accepted" not in (tmp_path / "manifest.json").read_text().lower()