"""Run Testatron cases once with IPOPT and retain unreviewed artifacts."""

import argparse
import csv
import fnmatch
import importlib
import json
import math
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TESTATRON_ROOT = REPOSITORY_ROOT / "testatron"
TESTS_ROOT = TESTATRON_ROOT / "tests"
PYEMTG_ROOT = REPOSITORY_ROOT / "PyEMTG"
DEFAULT_OUTPUT_ROOT = TESTATRON_ROOT / "ipopt"
PUBLIC_HARDWARE_ROOT = (
    REPOSITORY_ROOT
    / "docs"
    / "0_Users"
    / "tutorial"
    / "Tutorial_EMTG_Files"
    / "Config_Files"
    / "hardware_models"
)
LEGACY_NLSII_LIBRARIES = (
    "NLSII_April2017.emtg_launchvehicleopt",
    "NLSII_August2018.emtg_launchvehicleopt",
)
PUBLIC_NLSII_LIBRARY = "LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt"
LEGACY_UNUSED_THROTTLE_TABLE = "NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable"
INERT_THROTTLE_TABLE = "empty.ThrottleTable"
TABLE_INDEPENDENT_ENGINE_TYPES = (0, 3, 5, *range(6, 29))
CLASSIFICATIONS = (
    "reviewable",
    "infeasible",
    "topology_changed",
    "process_failed",
    "timed_out",
    "parse_failed",
    "dependency_blocked",
)


@dataclass
class CaseResult:
    case_id: str
    source_options: str
    classification: str
    status: str = "unreviewed"
    prepared_options: str = ""
    output_file: str = ""
    comparison_file: str = ""
    log_file: str = ""
    compatibility_file: str = ""
    return_code: int | None = None
    duration_seconds: float = 0.0
    objective_value: float | None = None
    worst_violation: float | None = None
    worst_constraint: str = ""
    detail: str = ""


def discover_cases(tests_root=TESTS_ROOT, filters=None):
    """Discover the same root and one-level-folder cases as MakeTestsList()."""
    tests_root = Path(tests_root)
    folders = sorted(child for child in tests_root.iterdir() if child.is_dir())
    cases = []
    for folder in folders + [tests_root]:
        cases.extend(sorted(folder.glob("*.emtgopt")))

    if filters:
        cases = [
            case
            for case in cases
            if any(
                fnmatch.fnmatch(case.relative_to(tests_root).as_posix(), pattern)
                for pattern in filters
            )
        ]
    return cases


def case_id(source_options, tests_root=TESTS_ROOT):
    return Path(source_options).relative_to(tests_root).with_suffix("").as_posix()


def _load_pyemtg(pyemtg_root=PYEMTG_ROOT):
    pyemtg_root = str(Path(pyemtg_root))
    if pyemtg_root not in sys.path:
        sys.path.insert(0, pyemtg_root)
    return (
        importlib.import_module("Mission"),
        importlib.import_module("MissionOptions"),
    )


def _normalized_description(description):
    return description.replace(": ", ":").strip()


def inject_aligned_mission_seed(options, mission):
    """Inject a mission decision vector after strict ordered alignment checks."""
    bound_absolute_tolerance = 1.0e-12
    bound_relative_tolerance = 1.0e-12
    descriptions = list(mission.Xdescriptions)
    values = list(mission.DecisionVector)
    lower_bounds = list(mission.Xlowerbounds)
    upper_bounds = list(mission.Xupperbounds)
    if not (
        len(descriptions)
        == len(values)
        == len(lower_bounds)
        == len(upper_bounds)
    ):
        raise ValueError("Mission decision vector descriptions, values, and bounds differ in length")

    options.AssembleMasterDecisionVector()
    option_descriptions = [entry[0] for entry in options.trialX]
    if len(option_descriptions) != len(descriptions):
        raise ValueError("Mission and options decision vectors differ in length")
    for index, (option_description, mission_description) in enumerate(
        zip(option_descriptions, descriptions)
    ):
        if _normalized_description(option_description) != _normalized_description(
            mission_description
        ):
            raise ValueError(
                f"Decision variable description mismatch at index {index}: "
                f"{option_description!r} != {mission_description!r}"
            )

    for index, (value, lower_bound, upper_bound) in enumerate(
        zip(values, lower_bounds, upper_bounds)
    ):
        if not all(math.isfinite(item) for item in (value, lower_bound, upper_bound)):
            raise ValueError(f"Non-finite decision variable or bound at index {index}")
        bound_tolerance = bound_absolute_tolerance + bound_relative_tolerance * max(
            abs(value), abs(lower_bound), abs(upper_bound)
        )
        if value < lower_bound - bound_tolerance or value > upper_bound + bound_tolerance:
            raise ValueError(f"Decision variable at index {index} is outside its bounds")

    options.trialX = list(zip(descriptions, values))
    options.DisassembleMasterDecisionVector()


def _prepare_seeded_case(
    source_options,
    baseline_mission,
    case_directory,
    run_inner_loop,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
):
    """Prepare a run mode from an aligned committed mission seed."""
    Mission, MissionOptions = _load_pyemtg(pyemtg_root)
    case_directory = Path(case_directory)
    prepared_options = prepare_case(source_options, case_directory, pyemtg_root)
    options = MissionOptions.MissionOptions(str(prepared_options))
    baseline = Mission.Mission(str(baseline_mission))
    inject_aligned_mission_seed(options, baseline)
    options.run_inner_loop = run_inner_loop
    if execution_repository_root is not None:
        execution_repository_root = Path(execution_repository_root)
        options.universe_folder = str(execution_repository_root / "testatron/universe")
        options.HardwarePath = str(
            execution_repository_root
            / "docs/0_Users/tutorial/Tutorial_EMTG_Files/"
            "Config_Files/hardware_models"
        )
        gravity_root = execution_repository_root / "testatron/universe/gravity_files"
        for journey in options.Journeys:
            gravity_name = Path(
                journey.central_body_gravity_file.replace("\\", "/")
            ).name
            journey.central_body_gravity_file = str(gravity_root / gravity_name)
    if execution_directory is not None:
        options.forced_working_directory = str(execution_directory)
    options.write_options_file(
        str(prepared_options), not options.print_only_non_default_options
    )
    return prepared_options


def prepare_replay(
    source_options,
    baseline_mission,
    case_directory,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
):
    """Prepare an evaluate-only replay from an aligned committed mission seed."""
    return _prepare_seeded_case(
        source_options,
        baseline_mission,
        case_directory,
        0,
        pyemtg_root,
        execution_repository_root,
        execution_directory,
    )


def prepare_refinement(
    source_options,
    baseline_mission,
    case_directory,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
):
    """Prepare a direct IPOPT refinement from an aligned committed mission seed."""
    prepared_options = _prepare_seeded_case(
        source_options,
        baseline_mission,
        case_directory,
        3,
        pyemtg_root,
        execution_repository_root,
        execution_directory,
    )
    _, MissionOptions = _load_pyemtg(pyemtg_root)
    options = MissionOptions.MissionOptions(str(prepared_options))
    options.quiet_NLP = 0
    options.enable_NLP_chaperone = 1
    options.write_options_file(
        str(prepared_options), not options.print_only_non_default_options
    )
    return prepared_options


def prepare_case(source_options, case_directory, pyemtg_root=PYEMTG_ROOT):
    """Write an IPOPT input while preserving the source optimization policy."""
    _, MissionOptions = _load_pyemtg(pyemtg_root)
    source_options = Path(source_options)
    case_directory = Path(case_directory)
    case_directory.mkdir(parents=True, exist_ok=True)

    options = MissionOptions.MissionOptions(str(source_options))
    options.NLP_solver_type = 2
    options.override_working_directory = 1
    options.forced_working_directory = str(case_directory)
    options.override_mission_subfolder = 1
    options.forced_mission_subfolder = "."
    options.short_output_file_names = 1
    options.background_mode = 1
    options.universe_folder = str(TESTATRON_ROOT / "universe")
    compatibility_mappings = []
    options.HardwarePath = str(TESTATRON_ROOT / "HardwareModels")
    if options.LaunchVehicleLibraryFile in LEGACY_NLSII_LIBRARIES:
        legacy_library = options.LaunchVehicleLibraryFile
        options.HardwarePath = str(PUBLIC_HARDWARE_ROOT)
        options.LaunchVehicleLibraryFile = PUBLIC_NLSII_LIBRARY
        compatibility_mappings.append(
            {
                "option": "LaunchVehicleLibraryFile",
                "source": legacy_library,
                "replacement": PUBLIC_NLSII_LIBRARY,
                "reason": "public replacement library; LaunchVehicleKey preserved",
            }
        )
    if (
        options.SpacecraftModelInput == 2
        and options.engine_type in TABLE_INDEPENDENT_ENGINE_TYPES
        and options.ThrottleTableFile == LEGACY_UNUSED_THROTTLE_TABLE
    ):
        options.ThrottleTableFile = INERT_THROTTLE_TABLE
        compatibility_mappings.append(
            {
                "option": "ThrottleTableFile",
                "source": LEGACY_UNUSED_THROTTLE_TABLE,
                "replacement": INERT_THROTTLE_TABLE,
                "reason": (
                    f"engine_type {options.engine_type} does not use throttle-table "
                    "performance data"
                ),
            }
        )
    gravity_root = TESTATRON_ROOT / "universe" / "gravity_files"
    for journey in options.Journeys:
        gravity_name = Path(
            journey.central_body_gravity_file.replace("\\", "/")
        ).name
        journey.central_body_gravity_file = str(gravity_root / gravity_name)

    prepared_options = case_directory / source_options.name
    options.write_options_file(
        str(prepared_options), not options.print_only_non_default_options
    )
    (case_directory / "compatibility.json").write_text(
        json.dumps(
            {
                "status": "unreviewed",
                "source_options": str(source_options),
                "mappings": compatibility_mappings,
            },
            indent=2,
        )
        + "\n"
    )
    return prepared_options


def _topology(mission):
    return tuple(len(journey.missionevents) for journey in mission.Journeys)


def _event_topology(mission):
    return tuple(
        tuple((event.EventType, event.Location) for event in journey.missionevents)
        for journey in mission.Journeys
    )


def compare_replay(baseline, generated):
    """Compare replay semantics directly without the pandas-backed Comparatron."""
    absolute_tolerance = 1.0e-12
    relative_tolerance = 1.0e-10

    def close(left, right):
        return math.isfinite(left) and math.isfinite(right) and math.isclose(
            left,
            right,
            rel_tol=relative_tolerance,
            abs_tol=absolute_tolerance,
        )

    checks = {
        "journey_names": [journey.journey_name for journey in generated.Journeys]
        == [journey.journey_name for journey in baseline.Journeys],
        "event_topology": _event_topology(generated) == _event_topology(baseline),
        "decision_descriptions": [
            _normalized_description(description)
            for description in generated.Xdescriptions
        ]
        == [
            _normalized_description(description)
            for description in baseline.Xdescriptions
        ],
        "decision_vector_length": len(generated.DecisionVector)
        == len(baseline.DecisionVector),
        "objective": close(generated.objective_value, baseline.objective_value),
        "total_deterministic_deltav": close(
            generated.total_deterministic_deltav,
            baseline.total_deterministic_deltav,
        ),
        "total_flight_time_years": close(
            generated.total_flight_time_years,
            baseline.total_flight_time_years,
        ),
        "final_mass": close(
            generated.final_mass_including_propellant_margin,
            baseline.final_mass_including_propellant_margin,
        ),
    }
    endpoint_checks = []
    endpoint_deltas = {
        "max_epoch_days": 0.0,
        "max_position_km": 0.0,
        "max_velocity_km_s": 0.0,
        "max_mass_kg": 0.0,
    }
    if len(generated.Journeys) == len(baseline.Journeys):
        for generated_journey, baseline_journey in zip(
            generated.Journeys, baseline.Journeys
        ):
            if not generated_journey.missionevents or not baseline_journey.missionevents:
                endpoint_checks.append(False)
                continue
            for generated_event, baseline_event in (
                (generated_journey.missionevents[0], baseline_journey.missionevents[0]),
                (generated_journey.missionevents[-1], baseline_journey.missionevents[-1]),
            ):
                epoch_delta = abs(generated_event.JulianDate - baseline_event.JulianDate)
                mass_delta = abs(generated_event.Mass - baseline_event.Mass)
                position_deltas = [
                    abs(generated_value - baseline_value)
                    for generated_value, baseline_value in zip(
                        generated_event.SpacecraftState[:3],
                        baseline_event.SpacecraftState[:3],
                    )
                ]
                velocity_deltas = [
                    abs(generated_value - baseline_value)
                    for generated_value, baseline_value in zip(
                        generated_event.SpacecraftState[3:],
                        baseline_event.SpacecraftState[3:],
                    )
                ]
                endpoint_deltas["max_epoch_days"] = max(
                    endpoint_deltas["max_epoch_days"], epoch_delta
                )
                endpoint_deltas["max_position_km"] = max(
                    endpoint_deltas["max_position_km"], *position_deltas
                )
                endpoint_deltas["max_velocity_km_s"] = max(
                    endpoint_deltas["max_velocity_km_s"], *velocity_deltas
                )
                endpoint_deltas["max_mass_kg"] = max(
                    endpoint_deltas["max_mass_kg"], mass_delta
                )
                endpoint_checks.append(
                    epoch_delta <= 1.0e-8
                    and mass_delta <= 1.0e-6
                    and max(position_deltas) <= 1.0
                    and max(velocity_deltas) <= 1.0e-7
                )
    checks["journey_endpoints"] = bool(endpoint_checks) and all(endpoint_checks)

    return {
        "status": "unreviewed",
        "acceptable": all(checks.values()),
        "absolute_tolerance": absolute_tolerance,
        "relative_tolerance": relative_tolerance,
        "checks": checks,
        "baseline_objective": baseline.objective_value,
        "generated_objective": generated.objective_value,
        "generated_feasibility_metric": abs(generated.worst_violation),
        "endpoint_tolerances": {
            "epoch_days": 1.0e-8,
            "position_km": 1.0,
            "velocity_km_s": 1.0e-7,
            "mass_kg": 1.0e-6,
        },
        "endpoint_deltas": endpoint_deltas,
    }


def compare_refinement(baseline, generated, feasibility_tolerance):
    """Check feasibility, topology, and objective non-regression after refinement."""
    absolute_tolerance = 1.0e-12
    relative_tolerance = 1.0e-10
    decision_bounds_complete = (
        len(generated.DecisionVector)
        == len(generated.Xlowerbounds)
        == len(generated.Xupperbounds)
        and bool(generated.DecisionVector)
    )

    def decision_value_in_bounds(value, lower_bound, upper_bound):
        tolerance = absolute_tolerance + relative_tolerance * max(
            abs(value), abs(lower_bound), abs(upper_bound)
        )
        return lower_bound - tolerance <= value <= upper_bound + tolerance

    objective_band = absolute_tolerance + relative_tolerance * max(
        abs(baseline.objective_value), abs(generated.objective_value)
    )
    checks = {
        "finite_objective": math.isfinite(generated.objective_value),
        "finite_feasibility": math.isfinite(generated.worst_violation),
        "decision_bounds_complete": decision_bounds_complete,
        "finite_decision_vector": bool(generated.DecisionVector)
        and all(math.isfinite(value) for value in generated.DecisionVector),
        "decision_vector_in_bounds": decision_bounds_complete
        and all(
            decision_value_in_bounds(value, lower_bound, upper_bound)
            for value, lower_bound, upper_bound in zip(
                generated.DecisionVector,
                generated.Xlowerbounds,
                generated.Xupperbounds,
            )
        ),
        "finite_constraint_vector": bool(generated.ConstraintVector)
        and all(math.isfinite(value) for value in generated.ConstraintVector),
        "feasible": abs(generated.worst_violation) <= feasibility_tolerance,
        "journey_names": [journey.journey_name for journey in generated.Journeys]
        == [journey.journey_name for journey in baseline.Journeys],
        "event_topology": _event_topology(generated) == _event_topology(baseline),
        "decision_descriptions": [
            _normalized_description(description)
            for description in generated.Xdescriptions
        ]
        == [
            _normalized_description(description)
            for description in baseline.Xdescriptions
        ],
        "objective_non_regression": generated.objective_value
        <= baseline.objective_value + objective_band,
    }
    return {
        "status": "unreviewed",
        "acceptable": all(checks.values()),
        "checks": checks,
        "baseline_objective": baseline.objective_value,
        "generated_objective": generated.objective_value,
        "objective_comparison_band": objective_band,
        "generated_feasibility_metric": abs(generated.worst_violation),
        "feasibility_tolerance": feasibility_tolerance,
    }


def parse_ipopt_log(log_text):
    """Extract refinement diagnostics from verbose IPOPT output."""
    initialization_match = re.search(
        r"^EMTG IPOPT initialization policy:\s*(?P<policy>\S+)$",
        log_text,
        re.MULTILINE,
    )
    initial_match = re.search(
        r"^\s*0\s+\S+\s+(?P<inf_pr>\S+)", log_text, re.MULTILINE
    )
    iterations_match = re.search(
        r"Number of Iterations\.*:\s*(?P<iterations>\d+)", log_text
    )
    violation_match = re.search(
        r"Constraint violation\.*:\s+\S+\s+(?P<violation>\S+)", log_text
    )
    exit_match = re.search(r"^EXIT:\s*(?P<exit>.+)$", log_text, re.MULTILINE)
    if not all(
        (
            initialization_match,
            initial_match,
            iterations_match,
            violation_match,
            exit_match,
        )
    ):
        raise ValueError("IPOPT log is missing required refinement diagnostics")
    return {
        "initialization_policy": initialization_match.group("policy"),
        "initial_infeasibility": float(initial_match.group("inf_pr")),
        "iterations": int(iterations_match.group("iterations")),
        "terminal_constraint_violation": float(
            violation_match.group("violation")
        ),
        "native_exit": exit_match.group("exit").strip(),
    }


def _write_case_result(case_directory, result):
    result_file = Path(case_directory) / "result.json"
    result_file.write_text(json.dumps(asdict(result), indent=2) + "\n")


def _load_case_results(output_root):
    results = []
    for result_file in sorted((Path(output_root) / "cases").glob("**/result.json")):
        try:
            results.append(CaseResult(**json.loads(result_file.read_text())))
        except (OSError, TypeError, ValueError):
            continue
    return results


def write_manifests(output_root, results):
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    rows = [asdict(result) for result in sorted(results, key=lambda item: item.case_id)]
    manifest = {
        "status": "unreviewed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(rows),
        "classifications": {
            classification: sum(
                row["classification"] == classification for row in rows
            )
            for classification in CLASSIFICATIONS
        },
        "cases": rows,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    fieldnames = list(asdict(CaseResult("", "", "")).keys())
    with (output_root / "manifest.csv").open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _parse_and_classify(source_options, output_file, comparison_file, pyemtg_root):
    Mission, MissionOptions = _load_pyemtg(pyemtg_root)
    generated = Mission.Mission(str(output_file))
    baseline = Mission.Mission(str(Path(source_options).with_suffix(".emtg")))
    if not hasattr(generated, "Journeys"):
        return "parse_failed", generated, "Generated mission has no journeys"
    if not hasattr(baseline, "Journeys"):
        return "dependency_blocked", generated, "Committed truth mission is unavailable"
    if _topology(generated) != _topology(baseline):
        return "topology_changed", generated, "Journey or mission-event topology changed"

    generated.Comparatron(
        baseline_path=str(Path(source_options).with_suffix(".emtg")),
        csv_file_name=str(comparison_file),
        full_output=False,
        tolerance_dict={},
        default_tolerance=1.0e-10,
        attributes_to_ignore=[],
    )
    source = MissionOptions.MissionOptions(str(source_options))
    if generated.worst_violation > source.snopt_feasibility_tolerance:
        return "infeasible", generated, "Worst constraint exceeds source tolerance"
    return "reviewable", generated, "Ready for human review; not a promoted baseline"


def run_case(source_options, executable, output_root, timeout, pyemtg_root=PYEMTG_ROOT):
    source_options = Path(source_options)
    identifier = case_id(source_options)
    case_directory = Path(output_root) / "cases" / identifier
    case_directory.mkdir(parents=True, exist_ok=True)
    log_file = case_directory / "run.log"
    result = CaseResult(
        case_id=identifier,
        source_options=str(source_options),
        classification="dependency_blocked",
        log_file=str(log_file),
    )

    try:
        prepared_options = prepare_case(source_options, case_directory, pyemtg_root)
        result.prepared_options = str(prepared_options)
        result.compatibility_file = str(case_directory / "compatibility.json")
    except Exception as error:
        result.detail = f"Unable to prepare options: {error}"
        _write_case_result(case_directory, result)
        return result

    started = time.monotonic()
    try:
        with log_file.open("w") as output:
            completed = subprocess.run(
                [str(executable), str(prepared_options)],
                cwd=case_directory,
                stdout=output,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        result.return_code = completed.returncode
    except subprocess.TimeoutExpired:
        result.classification = "timed_out"
        result.detail = f"Exceeded {timeout:g} second process timeout"
        result.duration_seconds = time.monotonic() - started
        _write_case_result(case_directory, result)
        return result
    except OSError as error:
        result.detail = f"Unable to execute EMTG: {error}"
        result.duration_seconds = time.monotonic() - started
        _write_case_result(case_directory, result)
        return result

    result.duration_seconds = time.monotonic() - started
    if result.return_code != 0:
        result.classification = "process_failed"
        result.detail = f"EMTG exited with status {result.return_code}"
        _write_case_result(case_directory, result)
        return result

    outputs = sorted(case_directory.glob("*.emtg"))
    if not outputs:
        log_text = log_file.read_text(errors="replace")
        missing_dependency = next(
            (
                (
                    line[line.index("Cannot find") :].strip()
                    if "Cannot find" in line
                    else line.strip()
                )
                for line in log_text.splitlines()
                if "Cannot find" in line
                or ("Launch vehicle '" in line and "not found" in line)
            ),
            "",
        )
        if missing_dependency:
            result.classification = "dependency_blocked"
            result.detail = missing_dependency
        else:
            result.classification = "parse_failed"
            result.detail = "EMTG produced no .emtg result"
        _write_case_result(case_directory, result)
        return result

    output_file = max(outputs, key=lambda candidate: candidate.stat().st_mtime)
    comparison_file = case_directory / "comparison.csv"
    result.output_file = str(output_file)
    result.comparison_file = str(comparison_file)
    try:
        classification, mission, detail = _parse_and_classify(
            source_options, output_file, comparison_file, pyemtg_root
        )
        result.classification = classification
        result.objective_value = mission.objective_value
        result.worst_violation = mission.worst_violation
        result.worst_constraint = mission.worst_constraint
        result.detail = detail
    except Exception as error:
        result.classification = "parse_failed"
        result.detail = f"Unable to parse or compare result: {error}"
    _write_case_result(case_directory, result)
    return result


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run unreviewed Testatron characterization with IPOPT"
    )
    parser.add_argument("--ipopt-characterization", action="store_true")
    parser.add_argument("-e", "--emtg", help="path to the IPOPT-enabled EMTG executable")
    parser.add_argument("--pyemtg", default=str(PYEMTG_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument(
        "--filter",
        action="append",
        help="glob matched against a case path relative to testatron/tests",
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    output_root = Path(args.output_root).resolve()
    if args.report_only:
        results = _load_case_results(output_root)
        write_manifests(output_root, results)
        print(f"Wrote unreviewed report for {len(results)} existing case result(s)")
        return 0
    if not args.emtg:
        raise SystemExit("--emtg is required unless --report-only is used")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")

    cases = discover_cases(filters=args.filter)
    previous = {
        result.case_id: result for result in _load_case_results(output_root)
    } if args.resume else {}
    results = []
    for index, source_options in enumerate(cases, start=1):
        identifier = case_id(source_options)
        if identifier in previous:
            result = previous[identifier]
            print(f"[{index}/{len(cases)}] resumed {identifier}: {result.classification}")
        else:
            print(f"[{index}/{len(cases)}] running {identifier}")
            result = run_case(
                source_options, args.emtg, output_root, args.timeout, args.pyemtg
            )
            print(f"[{index}/{len(cases)}] {identifier}: {result.classification}")
        results.append(result)
        write_manifests(output_root, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())