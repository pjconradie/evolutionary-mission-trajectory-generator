"""Run Testatron cases once with IPOPT and retain unreviewed artifacts."""

import argparse
import csv
import fnmatch
import importlib
import json
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
LEGACY_NLSII_LIBRARY = "NLSII_April2017.emtg_launchvehicleopt"
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
    if options.LaunchVehicleLibraryFile == LEGACY_NLSII_LIBRARY:
        options.HardwarePath = str(PUBLIC_HARDWARE_ROOT)
        options.LaunchVehicleLibraryFile = PUBLIC_NLSII_LIBRARY
        compatibility_mappings.append(
            {
                "option": "LaunchVehicleLibraryFile",
                "source": LEGACY_NLSII_LIBRARY,
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
                line[line.index("Cannot find") :]
                for line in log_text.splitlines()
                if "Cannot find" in line
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