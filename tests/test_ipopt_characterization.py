"""Contracts for the unreviewed IPOPT characterization runner."""

import copy
import csv
import json
import math
import re
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from testatron import ipopt_characterization


pytestmark = pytest.mark.unit


def test_tutorial_registry_is_complete_unique_and_pinned(repository_root):
    cases = ipopt_characterization.TUTORIAL_CASES

    assert len(cases) == 17
    assert len(ipopt_characterization.TUTORIAL_CASES_BY_ID) == 17
    assert len({case.source_options for case in cases}) == 17
    assert sum(case.taxonomy == "authoritative" for case in cases) == 2
    assert sum(case.taxonomy == "deliberate_infeasible" for case in cases) == 1
    assert sum(case.schema_probe for case in cases) == 3
    assert sum("refinement" in case.stages for case in cases) == 16
    for case in cases:
        assert (repository_root / case.source_options).is_file()
        assert (repository_root / case.reference_package).is_dir()
        assert (repository_root / case.reference_mission).is_file()
        assert (repository_root / case.seed_alignment_source).is_file()
        assert (repository_root / case.universe_root).is_dir()
        assert (repository_root / case.hardware_root).is_dir()
        assert (repository_root / case.ephemeris_root).is_dir()

    assert ipopt_characterization.EXCLUDED_TUTORIAL_VINTAGES == (
        "OSIRIS-REx_11272022_144557",
        "LowSIRIS-REx_11252022_153645",
    )


def test_tutorial_registry_pins_force_models_semantics():
    cases = ipopt_characterization.TUTORIAL_CASES_BY_ID
    baseline = cases["Force_Models/LowSIRIS-REx"]
    deliberate = cases["Force_Models/LowSIRIS-REx_forcemodel"]
    recovery = cases["Force_Models/LowSIRIS-REx_forcemodel_nlp"]

    assert baseline.schema_probe
    assert baseline.reference_package.endswith("LowSIRIS-REx_11292022_93643")
    assert deliberate.taxonomy == "deliberate_infeasible"
    assert deliberate.expected_output == "failure"
    assert deliberate.stages == ("replay",)
    assert deliberate.replay_seed_source == "current_infeasible_trial"
    assert recovery.replay_seed_source == "current_infeasible_trial"
    assert recovery.refinement_seed_source == "current_infeasible_trial"
    assert recovery.reference_mission.endswith(
        "LowSIRIS-REx_forcemodel_nlp_Sun(EB)_Sun(BE).emtg"
    )


def test_tutorial_provenance_is_portable_hashed_and_unreviewed(tmp_path):
    repository_root = tmp_path / "repository"
    source_root = repository_root / "sources"
    universe_root = repository_root / "universe"
    hardware_root = repository_root / "hardware"
    source_root.mkdir(parents=True)
    universe_root.mkdir()
    hardware_root.mkdir()
    for name in ("case.emtgopt", "reference.emtg", "XFfile.csv", "seed.emtgopt"):
        (source_root / name).write_text(name, encoding="ascii")
    (universe_root / "body.emtg_universe").write_text("universe", encoding="ascii")
    for name in ipopt_characterization.TUTORIAL_SHARED_EPHEMERIS_FILES:
        (universe_root / name).write_text(name, encoding="ascii")
    (hardware_root / "vehicle.emtg_spacecraftopt").write_text(
        "hardware", encoding="ascii"
    )
    case = replace(
        ipopt_characterization.TUTORIAL_CASES[0],
        source_options="sources/case.emtgopt",
        reference_package="sources",
        reference_mission="sources/reference.emtg",
        seed_alignment_source="sources/XFfile.csv",
        refinement_seed_options="sources/seed.emtgopt",
        universe_root="universe",
        hardware_root="hardware",
        ephemeris_root="universe",
    )

    provenance = ipopt_characterization.write_tutorial_provenance(
        tmp_path,
        case,
        "replay",
        [tmp_path / "generated.emtg"],
        repository_root,
    )

    assert provenance["status"] == "unreviewed"
    assert provenance["generated"] == ["generated.emtg"]
    records = list(provenance["sources"].values()) + provenance["dependencies"]
    assert records
    for record in records:
        assert not Path(record["path"]).is_absolute()
        assert "\\" not in record["path"]
        assert record["sha256"] == ipopt_characterization._sha256(
            repository_root / record["path"]
        )
    assert json.loads((tmp_path / "provenance.json").read_text()) == provenance


def test_tutorial_hardware_rejects_missing_nested_dependency(tmp_path):
    repository_root = tmp_path / "repository"
    hardware_root = repository_root / "hardware"
    hardware_root.mkdir(parents=True)
    (hardware_root / "vehicle.emtg_spacecraftopt").write_text(
        r"C:\models\missing.ThrottleTable", encoding="ascii"
    )
    case = replace(
        ipopt_characterization.TUTORIAL_CASES[0], hardware_root="hardware"
    )

    with pytest.raises(FileNotFoundError, match="missing.ThrottleTable"):
        ipopt_characterization.prepare_tutorial_hardware(
            case, tmp_path / "artifacts", repository_root
        )


def test_prepare_tutorial_schema_probe_is_evaluate_only(repository_root, tmp_path):
    case = ipopt_characterization.TUTORIAL_CASES_BY_ID["OSIRIS-REx/OSIRIS-REx"]
    _, MissionOptions = ipopt_characterization._load_pyemtg()

    prepared_path = ipopt_characterization.prepare_tutorial_schema_probe(
        case, tmp_path, repository_root=repository_root
    )
    prepared = MissionOptions.MissionOptions(str(prepared_path))

    assert prepared.run_inner_loop == 0
    assert prepared.universe_folder == "/artifacts/universe"
    assert prepared.HardwarePath == "/artifacts/hardware_models"
    assert prepared.forced_working_directory == "/artifacts"
    assert (tmp_path / "hardware_models").is_dir()
    assert (tmp_path / "universe/ephemeris_files/de430.bsp").is_file()


def test_prepare_tutorial_schema_probe_rejects_unregistered_probe(tmp_path):
    case = next(
        case for case in ipopt_characterization.TUTORIAL_CASES if not case.schema_probe
    )

    with pytest.raises(ValueError, match="does not need a schema probe"):
        ipopt_characterization.prepare_tutorial_schema_probe(case, tmp_path)


def test_validate_decision_alignment_reports_first_mismatch():
    with pytest.raises(ValueError, match=r"mismatch at index 1"):
        ipopt_characterization.validate_decision_alignment(
            ["first: value", "second: source", "third: value"],
            ["first:value", "second: reference", "third:value"],
        )

    with pytest.raises(ValueError, match=r"lengths differ: 1 != 2"):
        ipopt_characterization.validate_decision_alignment(["first"], ["first", "second"])

    with pytest.raises(ValueError, match="must be nonempty"):
        ipopt_characterization.validate_decision_alignment([], [])


def test_prepare_force_model_recovery_uses_sibling_seed_and_keeps_model(
    repository_root, tmp_path
):
    case = ipopt_characterization.TUTORIAL_CASES_BY_ID[
        "Force_Models/LowSIRIS-REx_forcemodel_nlp"
    ]
    _, MissionOptions = ipopt_characterization._load_pyemtg()
    sibling = MissionOptions.MissionOptions(
        str(repository_root / case.refinement_seed_options)
    )
    sibling.AssembleMasterDecisionVector()

    prepared_path = ipopt_characterization.prepare_tutorial_case(
        case, "refinement", tmp_path, repository_root=repository_root
    )
    prepared = MissionOptions.MissionOptions(str(prepared_path))
    prepared.AssembleMasterDecisionVector()

    assert prepared_path.name == "LowSIRIS-REx_forcemodel_nlp.emtgopt"
    assert prepared.mission_name == "LowSIRIS-REx_forcemodel_nlp"
    assert prepared.run_inner_loop == 3
    assert prepared.universe_folder == "/artifacts/universe"
    assert prepared.HardwarePath == "/artifacts/hardware_models"
    staged_hardware = tmp_path / "hardware_models"
    assert staged_hardware.is_dir()
    assert (tmp_path / "universe/ephemeris_files/de430.bsp").is_file()
    for hardware_file in (path for path in staged_hardware.rglob("*") if path.is_file()):
        assert not re.search(
            r"[A-Za-z]:[\\/]", hardware_file.read_text(encoding="utf-8")
        )
    assert [
        (ipopt_characterization._normalized_description(description), float(value))
        for description, value in prepared.trialX
    ] == [
        (ipopt_characterization._normalized_description(description), float(value))
        for description, value in sibling.trialX
    ]


def test_discovery_matches_legacy_testatron_inventory(repository_root):
    tests_root = repository_root / "testatron" / "tests"
    legacy_cases = []
    folders = [child for child in tests_root.iterdir() if child.is_dir()]
    for folder in folders + [tests_root]:
        legacy_cases.extend(folder.glob("*.emtgopt"))

    discovered = ipopt_characterization.discover_cases(tests_root)

    assert set(discovered) == set(legacy_cases)
    assert len(discovered) == 137


def test_discovery_unions_repeated_filters(repository_root):
    tests_root = repository_root / "testatron" / "tests"

    discovered = ipopt_characterization.discover_cases(
        tests_root,
        filters=[
            "spacecraft_options/spacecraftoptions_Chem_TrackACSProp",
            "transcription_tests/CoastPhase_EMintercept",
        ],
    )

    assert {
        path.relative_to(tests_root).as_posix() for path in discovered
    } == {
        "spacecraft_options/spacecraftoptions_Chem_TrackACSProp.emtgopt",
        "transcription_tests/CoastPhase_EMintercept.emtgopt",
    }


def test_main_resume_runs_only_missing_filtered_case(tmp_path, monkeypatch):
    tests_root = tmp_path / "tests"
    group = tests_root / "group"
    group.mkdir(parents=True)
    first = group / "first.emtgopt"
    second = group / "second.emtgopt"
    first.write_text("")
    second.write_text("")
    output_root = tmp_path / "output"
    previous = ipopt_characterization.CaseResult(
        case_id="group/first",
        source_options=str(first),
        classification="reviewable",
    )
    previous_directory = output_root / "cases/group/first"
    previous_directory.mkdir(parents=True)
    ipopt_characterization._write_case_result(previous_directory, previous)
    executed = []

    def run_case(source_options, executable, output, timeout, pyemtg_root):
        executed.append(Path(source_options))
        return ipopt_characterization.CaseResult(
            case_id="group/second",
            source_options=str(source_options),
            classification="reviewable",
        )

    monkeypatch.setattr(ipopt_characterization, "TESTS_ROOT", tests_root)
    monkeypatch.setattr(ipopt_characterization, "run_case", run_case)

    exit_code = ipopt_characterization.main(
        [
            "--ipopt-characterization",
            "--emtg",
            "EMTGv9",
            "--output-root",
            str(output_root),
            "--filter",
            "group/first",
            "--filter",
            "group/second",
            "--resume",
        ]
    )

    assert exit_code == 0
    assert executed == [second]
    manifest = json.loads((output_root / "manifest.json").read_text())
    assert manifest["status"] == "unreviewed"
    assert manifest["case_count"] == 2
    assert all(case["status"] == "unreviewed" for case in manifest["cases"])


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


def test_prepare_osiris_2022_replay_injects_aligned_nasa_seed(tmp_path):
    Mission, MissionOptions = ipopt_characterization._load_pyemtg()
    baseline_path = (
        ipopt_characterization.OSIRIS_2022_PACKAGE
        / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    )
    baseline = Mission.Mission(str(baseline_path))

    prepared_path = ipopt_characterization.prepare_osiris_2022_replay(
        tmp_path,
        execution_repository_root="/repo",
        execution_directory="/artifacts",
    )
    prepared = MissionOptions.MissionOptions(str(prepared_path))
    prepared.AssembleMasterDecisionVector()

    assert baseline.objective_value == pytest.approx(12.396265615671549)
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
    compatibility = json.loads((tmp_path / "compatibility.json").read_text())
    assert compatibility["status"] == "unreviewed"
    assert compatibility["seed_alignment_source"] == ipopt_characterization.repo_relative(
        ipopt_characterization.OSIRIS_2022_PACKAGE / "XFfile.csv"
    )
    assert compatibility["source_options"] == ipopt_characterization.repo_relative(
        ipopt_characterization.OSIRIS_2022_PACKAGE / "OSIRIS-REx.emtgopt"
    )


def test_prepare_osiris_2022_refinement_uses_verified_seed(tmp_path):
    Mission, MissionOptions = ipopt_characterization._load_pyemtg()
    baseline_path = (
        ipopt_characterization.OSIRIS_2022_PACKAGE
        / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    )
    baseline = Mission.Mission(str(baseline_path))

    prepared_path = ipopt_characterization.prepare_osiris_2022_refinement(
        tmp_path,
        execution_repository_root="/repo",
        execution_directory="/artifacts",
    )
    prepared = MissionOptions.MissionOptions(str(prepared_path))
    prepared.AssembleMasterDecisionVector()

    assert prepared.run_inner_loop == 3
    assert prepared.NLP_solver_type == 2
    assert prepared.enable_NLP_chaperone == 1
    assert prepared.quiet_NLP == 0
    assert [entry[0] for entry in prepared.trialX] == baseline.Xdescriptions
    assert [float(entry[1]) for entry in prepared.trialX] == baseline.DecisionVector


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


def test_prepare_osiris_2024_refinement_uses_verified_seed(tmp_path):
    Mission, MissionOptions = ipopt_characterization._load_pyemtg()
    baseline_path = (
        ipopt_characterization.OSIRIS_2024_PACKAGE
        / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    )
    baseline = Mission.Mission(str(baseline_path))

    prepared_path = ipopt_characterization.prepare_osiris_2024_refinement(
        tmp_path,
        execution_repository_root="/repo",
        execution_directory="/artifacts",
    )
    prepared = MissionOptions.MissionOptions(str(prepared_path))
    prepared.AssembleMasterDecisionVector()

    assert prepared.run_inner_loop == 3
    assert prepared.NLP_solver_type == 2
    assert prepared.enable_NLP_chaperone == 1
    assert prepared.quiet_NLP == 0
    assert [entry[0] for entry in prepared.trialX] == baseline.Xdescriptions
    assert [float(entry[1]) for entry in prepared.trialX] == baseline.DecisionVector


def test_osiris_2024_objective_regression_is_rejected():
    Mission, _ = ipopt_characterization._load_pyemtg()
    baseline_path = (
        ipopt_characterization.OSIRIS_2024_PACKAGE
        / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    )
    baseline = Mission.Mission(str(baseline_path))

    identical = copy.deepcopy(baseline)
    identical_comparison = ipopt_characterization.compare_refinement(
        baseline, identical, 1.0e-5
    )
    assert identical_comparison["acceptable"]
    assert identical_comparison["checks"]["objective_non_regression"]

    within_band = copy.deepcopy(baseline)
    within_band.objective_value += (
        identical_comparison["objective_comparison_band"] / 2.0
    )
    within_band_comparison = ipopt_characterization.compare_refinement(
        baseline, within_band, 1.0e-5
    )
    assert within_band_comparison["acceptable"]
    assert within_band_comparison["checks"]["objective_non_regression"]

    regressed = copy.deepcopy(baseline)
    regressed.objective_value += 1.0e-6
    regression_comparison = ipopt_characterization.compare_refinement(
        baseline, regressed, 1.0e-5
    )
    assert not regression_comparison["acceptable"]
    assert not regression_comparison["checks"]["objective_non_regression"]
    assert all(
        passed
        for name, passed in regression_comparison["checks"].items()
        if name != "objective_non_regression"
    )
    assert regression_comparison["baseline_objective"] == baseline.objective_value
    assert regression_comparison["generated_objective"] == regressed.objective_value
    assert regressed.objective_value > (
        baseline.objective_value
        + regression_comparison["objective_comparison_band"]
    )


@pytest.mark.parametrize(
    ("policy", "relative_tolerance", "absolute_tolerance"),
    [
        (ipopt_characterization.AUTHORITATIVE_REFINEMENT_POLICY, 1.0e-6, 1.0e-10),
        (ipopt_characterization.DEMONSTRATION_REFINEMENT_POLICY, 1.0e-3, 1.0e-8),
    ],
)
def test_refinement_objective_policy_is_fixed_and_one_sided(
    policy, relative_tolerance, absolute_tolerance
):
    Mission, _ = ipopt_characterization._load_pyemtg()
    baseline = Mission.Mission(
        str(
            ipopt_characterization.OSIRIS_2024_PACKAGE
            / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
        )
    )

    identical = copy.deepcopy(baseline)
    comparison = ipopt_characterization.compare_refinement(
        baseline, identical, 1.0e-5, objective_policy=policy
    )
    band = comparison["objective_comparison_band"]
    assert comparison["acceptable"]
    assert comparison["objective_relative_tolerance"] == relative_tolerance
    assert comparison["objective_absolute_tolerance"] == absolute_tolerance
    assert comparison["objective_delta"] == 0.0
    assert comparison["objective_absolute_delta"] == 0.0

    improved = copy.deepcopy(baseline)
    improved.objective_value -= 10.0 * band
    comparison = ipopt_characterization.compare_refinement(
        baseline, improved, 1.0e-5, objective_policy=policy
    )
    assert comparison["acceptable"]
    assert comparison["objective_delta"] < 0.0

    regressed = copy.deepcopy(baseline)
    regressed.objective_value += 2.0 * band
    comparison = ipopt_characterization.compare_refinement(
        baseline, regressed, 1.0e-5, objective_policy=policy
    )
    assert not comparison["acceptable"]
    assert not comparison["checks"]["objective_non_regression"]


def test_refinement_objective_policy_supports_maximization():
    Mission, _ = ipopt_characterization._load_pyemtg()
    baseline = Mission.Mission(
        str(
            ipopt_characterization.OSIRIS_2024_PACKAGE
            / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
        )
    )
    improved = copy.deepcopy(baseline)
    improved.objective_value += 1.0

    comparison = ipopt_characterization.compare_refinement(
        baseline,
        improved,
        1.0e-5,
        objective_policy=ipopt_characterization.AUTHORITATIVE_REFINEMENT_POLICY,
        objective_sense="maximize",
    )

    assert comparison["acceptable"]
    assert comparison["objective_sense"] == "maximize"
    assert comparison["objective_delta"] == pytest.approx(1.0)


@pytest.mark.parametrize("objective_type", [2, 3, 4, 6, 9, 11, 26])
def test_objective_sense_identifies_maximization(objective_type):
    assert ipopt_characterization.objective_sense(objective_type) == "maximize"


@pytest.mark.parametrize("objective_type", [0, 1, 5, 7, 8, 10, 13, 20, 27])
def test_objective_sense_defaults_to_minimization(objective_type):
    assert ipopt_characterization.objective_sense(objective_type) == "minimize"


def test_deliberate_infeasible_comparison_requires_expected_failure_topology():
    Mission, _ = ipopt_characterization._load_pyemtg()
    case = ipopt_characterization.TUTORIAL_CASES_BY_ID[
        "Force_Models/LowSIRIS-REx_forcemodel"
    ]
    baseline = Mission.Mission(
        str(ipopt_characterization.REPOSITORY_ROOT / case.reference_mission)
    )
    generated = copy.deepcopy(baseline)

    comparison = ipopt_characterization.compare_deliberate_infeasible(
        baseline, generated, 1.0e-5
    )

    assert comparison["status"] == "unreviewed"
    assert comparison["acceptable"]
    assert all(comparison["checks"].values())

    generated.worst_violation = 0.0
    comparison = ipopt_characterization.compare_deliberate_infeasible(
        baseline, generated, 1.0e-5
    )
    assert not comparison["acceptable"]
    assert not comparison["checks"]["intentionally_infeasible"]


def test_refinement_compares_structural_event_topology(repository_root):
    mission_path = (
        repository_root
        / "testatron/tests/spacecraft_options/"
        "spacecraftoptions_Chem_TrackACSProp.emtg"
    )
    Mission, _ = ipopt_characterization._load_pyemtg()
    baseline = Mission.Mission(str(mission_path))

    redistributed_coast = copy.deepcopy(baseline)
    events = redistributed_coast.Journeys[0].missionevents
    coast_index = next(
        index for index, event in enumerate(events) if event.EventType == "coast"
    )
    burn_index = next(
        index for index, event in enumerate(events) if event.EventType == "chem_burn"
    )
    events.insert(burn_index + 1, events.pop(coast_index))
    comparison = ipopt_characterization.compare_refinement(
        baseline, redistributed_coast, 1.0e-5
    )
    assert comparison["checks"]["event_topology"]

    subdivided_thrust = copy.deepcopy(baseline)
    thrust_events = subdivided_thrust.Journeys[0].missionevents
    thrust_index = next(
        index
        for index, event in enumerate(thrust_events)
        if event.EventType not in {"coast", "match_point"}
    )
    thrust_events.insert(thrust_index, copy.deepcopy(thrust_events[thrust_index]))
    comparison = ipopt_characterization.compare_refinement(
        baseline, subdivided_thrust, 1.0e-5
    )
    assert comparison["checks"]["event_topology"]

    changed_structure = copy.deepcopy(baseline)
    structural_event = next(
        event
        for event in changed_structure.Journeys[0].missionevents
        if event.EventType not in {"coast", "match_point"}
    )
    structural_event.EventType = "coast"
    comparison = ipopt_characterization.compare_refinement(
        baseline, changed_structure, 1.0e-5
    )
    assert not comparison["acceptable"]
    assert not comparison["checks"]["event_topology"]


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

    infeasible_seed_log = log_text.replace(
        "EMTG IPOPT initialization policy: near-feasible-primal-seed\n", ""
    )
    diagnostics = ipopt_characterization.parse_ipopt_log(
        infeasible_seed_log, initialization_policy="infeasible-primal-seed"
    )
    assert diagnostics["initialization_policy"] == "infeasible-primal-seed"


def test_parse_and_classify_is_pandas_independent(
    repository_root, tmp_path, monkeypatch
):
    source = (
        repository_root
        / "testatron/tests/spacecraft_options/"
        "spacecraftoptions_Chem_TrackACSProp.emtgopt"
    )
    output = source.with_suffix(".emtg")
    comparison_file = tmp_path / "comparison.csv"
    Mission, _ = ipopt_characterization._load_pyemtg()

    def reject_comparatron(*args, **kwargs):
        raise AssertionError("Characterization must not call Mission.Comparatron")

    monkeypatch.setattr(Mission.Mission, "Comparatron", reject_comparatron)
    classification, mission, detail = ipopt_characterization._parse_and_classify(
        source,
        output,
        comparison_file,
        ipopt_characterization.PYEMTG_ROOT,
    )

    assert classification == "reviewable"
    assert mission.objective_value == pytest.approx(-0.4088862070027368)
    assert detail == "Ready for human review; not a promoted baseline"
    rows = list(csv.DictReader(comparison_file.open(newline="")))
    assert [row["metric"] for row in rows] == [
        "objective_value",
        "worst_violation",
        "total_deterministic_deltav",
        "total_flight_time_years",
        "final_mass_including_propellant_margin",
    ]
    assert all(float(row["delta"]) == 0.0 for row in rows)


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


def test_repo_relative_returns_posix_relative(repository_root):
    target = repository_root / "testatron" / "ipopt_characterization.py"

    assert (
        ipopt_characterization.repo_relative(target)
        == "testatron/ipopt_characterization.py"
    )


def test_repo_relative_rejects_paths_outside_repository(tmp_path):
    outside = tmp_path / "elsewhere" / "artifact.json"

    with pytest.raises(ValueError, match="outside repository root"):
        ipopt_characterization.repo_relative(outside)


def _iter_json_strings(node):
    if isinstance(node, dict):
        for value in node.values():
            yield from _iter_json_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_json_strings(value)
    elif isinstance(node, str):
        yield node


def test_benchmark_artifacts_contain_no_absolute_paths(repository_root):
    benchmark_root = repository_root / "testatron" / "ipopt" / "benchmarks"
    forbidden = re.compile(r"(^/|/Users/|/home/|/private/var|^[A-Za-z]:\\|/repo/|/artifacts/)")

    offenders = []
    for artifact in sorted(benchmark_root.rglob("*.json")):
        payload = json.loads(artifact.read_text())
        for value in _iter_json_strings(payload):
            if forbidden.search(value):
                offenders.append(
                    f"{artifact.relative_to(repository_root).as_posix()}: {value}"
                )

    assert not offenders, "non-portable paths in benchmark artifacts:\n" + "\n".join(
        offenders
    )


def test_benchmark_registry_has_unique_ids_and_outputs():
    benchmarks = ipopt_characterization.BENCHMARKS
    output_roots = [benchmark.output_root for benchmark in benchmarks.values()]

    assert list(benchmarks) == [
        benchmark.benchmark_id for benchmark in benchmarks.values()
    ]
    assert len(output_roots) == len(set(output_roots))


def test_benchmark_registry_sources_exist(repository_root):
    for benchmark in ipopt_characterization.BENCHMARKS.values():
        for field in ("source_options", "reference_mission", "seed_alignment_source"):
            relative = getattr(benchmark, field)
            if relative is None:
                continue
            assert not Path(relative).is_absolute()
            assert (repository_root / relative).is_file()


def test_benchmark_provenance_hashes_current_sources(repository_root):
    provenance = ipopt_characterization.benchmark_provenance(
        "osiris-rex-2022", "ipopt", ["OSIRIS-REx.emtg"]
    )

    assert provenance["benchmark"] == "osiris-rex-2022"
    assert provenance["stage"] == "ipopt"
    assert provenance["generated"] == ["OSIRIS-REx.emtg"]
    for record in provenance["sources"].values():
        assert record["sha256"] == ipopt_characterization._sha256(
            repository_root / record["path"]
        )


def test_benchmark_provenance_rejects_unknown_stage():
    with pytest.raises(ValueError, match="Unknown stage"):
        ipopt_characterization.benchmark_provenance(
            "track-acs-prop", "optimize", ["ignored.emtg"]
        )


def test_committed_provenance_matches_registry_and_directory(repository_root):
    for benchmark in ipopt_characterization.BENCHMARKS.values():
        output_root = repository_root / benchmark.output_root
        for stage in benchmark.stages:
            provenance_file = output_root / stage / "provenance.json"
            assert provenance_file.is_file(), f"missing {provenance_file}"
            provenance = json.loads(provenance_file.read_text())
            assert provenance["benchmark"] == benchmark.benchmark_id
            assert provenance["stage"] == stage
            for record in provenance["sources"].values():
                assert record["sha256"] == ipopt_characterization._sha256(
                    repository_root / record["path"]
                )