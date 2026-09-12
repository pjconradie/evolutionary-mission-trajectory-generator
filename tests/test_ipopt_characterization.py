"""Contracts for the unreviewed IPOPT characterization runner."""

import json
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