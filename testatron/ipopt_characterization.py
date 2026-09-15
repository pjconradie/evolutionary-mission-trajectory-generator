"""Run Testatron cases once with IPOPT and retain unreviewed artifacts."""

import argparse
import csv
import fnmatch
import hashlib
import importlib
import json
import math
import re
import shutil
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
OSIRIS_TUTORIAL_ROOT = (
    REPOSITORY_ROOT
    / "docs/0_Users/tutorial/Tutorial_EMTG_Files"
)
OSIRIS_2022_PACKAGE = (
    OSIRIS_TUTORIAL_ROOT
    / "OSIRIS-REx/results/OSIRIS-REx_11272022_144557"
)
OSIRIS_2024_PACKAGE = (
    OSIRIS_TUTORIAL_ROOT
    / "OSIRIS-REx/results/OSIRIS-REx_412024_11530"
)
CLASSIFICATIONS = (
    "reviewable",
    "infeasible",
    "topology_changed",
    "process_failed",
    "timed_out",
    "parse_failed",
    "dependency_blocked",
)

TUTORIAL_ROOT = "docs/0_Users/tutorial/Tutorial_EMTG_Files"
TUTORIAL_EPHEMERIS_ROOT = "testatron/universe/ephemeris_files"
TUTORIAL_SHARED_EPHEMERIS_FILES = (
    "de430.bsp",
    "naif0012.tls",
    "pck00010.tpc",
)


@dataclass(frozen=True)
class ObjectivePolicy:
    """Fixed one-sided objective non-regression tolerances."""

    relative_tolerance: float
    absolute_tolerance: float


AUTHORITATIVE_REFINEMENT_POLICY = ObjectivePolicy(1.0e-6, 1.0e-10)
DEMONSTRATION_REFINEMENT_POLICY = ObjectivePolicy(1.0e-3, 1.0e-8)
LEGACY_REFINEMENT_POLICY = ObjectivePolicy(1.0e-10, 1.0e-12)


@dataclass(frozen=True)
class TutorialCase:
    """Immutable execution and reference policy for one current tutorial input."""

    case_id: str
    source_options: str
    reference_package: str
    reference_mission: str
    seed_alignment_source: str
    taxonomy: str
    universe_root: str
    hardware_root: str
    ephemeris_root: str = TUTORIAL_EPHEMERIS_ROOT
    replay_seed_source: str = "archive"
    refinement_seed_source: str = "archive"
    refinement_seed_options: str | None = None
    stages: tuple[str, ...] = ("replay", "refinement")
    expected_output: str = "success"
    schema_probe: bool = False
    timeout_seconds: int = 600


def _tutorial_case(
    group,
    name,
    package,
    mission,
    universe,
    hardware_group=None,
    taxonomy="demonstration",
    **overrides,
):
    source = f"{TUTORIAL_ROOT}/{group}/{name}.emtgopt"
    package_path = f"{TUTORIAL_ROOT}/{group}/results/{package}"
    return TutorialCase(
        case_id=f"{group}/{name}",
        source_options=source,
        reference_package=package_path,
        reference_mission=f"{package_path}/{mission}",
        seed_alignment_source=f"{package_path}/XFfile.csv",
        taxonomy=taxonomy,
        universe_root=f"{TUTORIAL_ROOT}/{universe}",
        hardware_root=f"{TUTORIAL_ROOT}/{hardware_group or group}/hardware_models",
        **overrides,
    )


TUTORIAL_CASES = (
    _tutorial_case(
        "Config_Files", "LowSIRIS-REx", "LowSIRIS-REx_11292022_132711",
        "LowSIRIS-REx_Sun(EB)_Sun(BE).emtg", "OSIRIS_universe",
    ),
    _tutorial_case(
        "Config_Files", "LowSIRIS-REx_high_thrust",
        "LowSIRIS-REx_high_thrust_11292022_133015",
        "LowSIRIS-REx_high_thrust_Sun(EB)_Sun(BE).emtg", "OSIRIS_universe",
    ),
    _tutorial_case(
        "Config_Files", "LowSIRIS-REx_high_thrust_low_c3",
        "LowSIRIS-REx_high_thrust_low_c3_11292022_133313",
        "LowSIRIS-REx_high_thrust_low_c3_Sun(EB)_Sun(BE).emtg",
        "OSIRIS_universe",
    ),
    _tutorial_case(
        "Journey_Boundaries", "EVM", "EVM_11252022_163915", "EVM.emtg",
        "EVM_universe",
    ),
    _tutorial_case(
        "Journey_Boundaries", "EVM_freepoint", "EVM_freepoint_11252022_17141",
        "EVM_freepoint.emtg", "EVM_universe",
    ),
    _tutorial_case(
        "OSIRIS-REx", "OSIRIS-REx", "OSIRIS-REx_412024_11530",
        "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg", "OSIRIS_universe",
        taxonomy="authoritative", schema_probe=True,
    ),
    _tutorial_case(
        "Force_Models", "LowSIRIS-REx_forcemodel_nlp",
        "LowSIRIS-REx_forcemodel_nlp_11292022_94615",
        "LowSIRIS-REx_forcemodel_nlp_Sun(EB)_Sun(BE).emtg", "OSIRIS_universe",
        replay_seed_source="current_infeasible_trial",
        refinement_seed_source="current_infeasible_trial",
        refinement_seed_options=(
            f"{TUTORIAL_ROOT}/Force_Models/LowSIRIS-REx_forcemodel.emtgopt"
        ),
    ),
    _tutorial_case(
        "Force_Models", "LowSIRIS-REx", "LowSIRIS-REx_11292022_93643",
        "LowSIRIS-REx_Sun(EB)_Sun(BE).emtg", "OSIRIS_universe",
        schema_probe=True,
    ),
    _tutorial_case(
        "Force_Models", "LowSIRIS-REx_forcemodel",
        "LowSIRIS-REx_forcemodel_11292022_94740",
        "FAILURE_LowSIRIS-REx_forcemodel_Sun(EB)_Sun(BE).emtg",
        "OSIRIS_universe", taxonomy="deliberate_infeasible",
        replay_seed_source="current_infeasible_trial", refinement_seed_source="none",
        stages=("replay",), expected_output="failure",
    ),
    _tutorial_case(
        "LowSIRIS-REx", "LowSIRIS-REx_FBLT", "LowSIRIS-REx_FBLT_11252022_15404",
        "LowSIRIS-REx_FBLT_Sun(EB)_Sun(BE).emtg", "OSIRIS_universe",
    ),
    _tutorial_case(
        "LowSIRIS-REx", "LowSIRIS-REx", "LowSIRIS-REx_412024_11158",
        "LowSIRIS-REx_Sun(EB)_Sun(BE).emtg", "OSIRIS_universe",
        taxonomy="authoritative", schema_probe=True,
    ),
    _tutorial_case(
        "Constraint_Scripting", "EVM_freepoint_boundary_constraint",
        "EVM_freepoint_boundary_constraint_6222023_161139",
        "EVM_freepoint_boundary_constraint.emtg", "EVM_universe",
        hardware_group="Journey_Boundaries",
    ),
    _tutorial_case(
        "Constraint_Scripting", "EVM_freepoint", "EVM_freepoint_6222023_16327",
        "EVM_freepoint.emtg", "EVM_universe", hardware_group="Journey_Boundaries",
    ),
    _tutorial_case(
        "Constraint_Scripting", "EVM_freepoint_maneuver_constraint",
        "EVM_freepoint_maneuver_constraint_6252023_145734",
        "EVM_freepoint_maneuver_constraint.emtg", "EVM_universe",
        hardware_group="Journey_Boundaries",
    ),
    _tutorial_case(
        "Flybys", "EVM", "EVM_11292022_112047", "EVM.emtg", "EVM_universe",
    ),
    _tutorial_case(
        "Flybys", "HighFidelity", "HighFidelity_11292022_124422",
        "HighFidelity.emtg", "EVM_universe",
    ),
    _tutorial_case(
        "Flybys", "EVM_singlePhase", "EVM_singlePhase_11292022_115245",
        "EVM_singlePhase.emtg", "EVM_universe",
    ),
)
TUTORIAL_CASES_BY_ID = {case.case_id: case for case in TUTORIAL_CASES}
EXCLUDED_TUTORIAL_VINTAGES = (
    "OSIRIS-REx_11272022_144557",
    "LowSIRIS-REx_11252022_153645",
)


def repo_relative(path, root=None):
    """Return a repository-relative POSIX path, refusing paths outside the repo."""
    root = Path(root) if root is not None else REPOSITORY_ROOT
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(
            f"Refusing to persist path outside repository root: "
            f"{resolved} is not under {root}"
        ) from error


@dataclass(frozen=True)
class Benchmark:
    """Immutable provenance record for one IPOPT benchmark, repo-relative only."""
    benchmark_id: str
    source_options: str
    reference_mission: str
    output_root: str
    seed_alignment_source: str | None = None
    stages: tuple[str, ...] = ("replay", "ipopt")


def _osiris_benchmark(benchmark_id, package_directory, year):
    package = repo_relative(package_directory)
    return Benchmark(
        benchmark_id=benchmark_id,
        source_options=f"{package}/OSIRIS-REx.emtgopt",
        reference_mission=f"{package}/OSIRIS-REx_Sun(EEB)_Sun(BE).emtg",
        seed_alignment_source=f"{package}/XFfile.csv",
        output_root=f"testatron/ipopt/benchmarks/osiris-rex/{year}",
    )


BENCHMARKS = {
    benchmark.benchmark_id: benchmark
    for benchmark in (
        _osiris_benchmark("osiris-rex-2022", OSIRIS_2022_PACKAGE, "2022"),
        _osiris_benchmark("osiris-rex-2024", OSIRIS_2024_PACKAGE, "2024"),
        Benchmark(
            benchmark_id="track-acs-prop",
            source_options=(
                "testatron/tests/spacecraft_options/"
                "spacecraftoptions_Chem_TrackACSProp.emtgopt"
            ),
            reference_mission=(
                "testatron/tests/spacecraft_options/"
                "spacecraftoptions_Chem_TrackACSProp.emtg"
            ),
            output_root="testatron/ipopt/benchmarks/track-acs-prop",
        ),
    )
}


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def benchmark_provenance(benchmark_id, stage, generated_missions, root=None):
    """Build a repo-relative provenance record with hashes of immutable sources."""
    root = Path(root) if root is not None else REPOSITORY_ROOT
    benchmark = BENCHMARKS[benchmark_id]
    if stage not in benchmark.stages:
        raise ValueError(
            f"Unknown stage {stage!r} for benchmark {benchmark_id!r}"
        )
    source_fields = ["source_options", "reference_mission", "seed_alignment_source"]
    sources = {}
    for field in source_fields:
        relative = getattr(benchmark, field)
        if relative is None:
            continue
        sources[field] = {
            "path": relative,
            "sha256": _sha256(root / relative),
        }
    return {
        "status": "unreviewed",
        "benchmark": benchmark_id,
        "stage": stage,
        "sources": sources,
        "generated": [Path(mission).name for mission in generated_missions],
    }


def write_provenance(directory, benchmark_id, stage, generated_missions, root=None):
    """Persist provenance.json into an artifact directory and return the record."""
    provenance = benchmark_provenance(benchmark_id, stage, generated_missions, root)
    (Path(directory) / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )
    return provenance


def tutorial_provenance(case, stage, generated_files, root=None):
    """Build portable SHA-256 evidence for one tutorial stage."""
    root = Path(root) if root is not None else REPOSITORY_ROOT
    if stage not in case.stages and stage != "schema":
        raise ValueError(f"Unknown stage {stage!r} for tutorial {case.case_id!r}")
    source_fields = {
        "source_options": case.source_options,
        "reference_mission": case.reference_mission,
        "seed_alignment_source": case.seed_alignment_source,
    }
    if case.refinement_seed_options:
        source_fields["refinement_seed_options"] = case.refinement_seed_options
    sources = {
        name: {"path": relative, "sha256": _sha256(root / relative)}
        for name, relative in source_fields.items()
    }
    dependency_files = []
    for dependency_root in (case.universe_root, case.hardware_root):
        for path in sorted((root / dependency_root).rglob("*")):
            if path.is_file():
                dependency_files.append(
                    {"path": repo_relative(path, root), "sha256": _sha256(path)}
                )
    case_ephemeris = root / case.universe_root / "ephemeris_files"
    shared_ephemeris = root / case.ephemeris_root
    for name in TUTORIAL_SHARED_EPHEMERIS_FILES:
        if not (case_ephemeris / name).is_file():
            path = shared_ephemeris / name
            dependency_files.append(
                {"path": repo_relative(path, root), "sha256": _sha256(path)}
            )
    return {
        "status": "unreviewed",
        "tutorial": case.case_id,
        "stage": stage,
        "sources": sources,
        "dependencies": dependency_files,
        "generated": [Path(path).name for path in generated_files],
    }


def write_tutorial_provenance(directory, case, stage, generated_files, root=None):
    """Persist portable tutorial provenance into an artifact directory."""
    provenance = tutorial_provenance(case, stage, generated_files, root)
    (Path(directory) / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )
    return provenance


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
                fnmatch.fnmatch(
                    case.relative_to(tests_root).as_posix(), pattern
                )
                or fnmatch.fnmatch(
                    case.relative_to(tests_root).with_suffix("").as_posix(),
                    pattern,
                )
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


def validate_decision_alignment(source_descriptions, reference_descriptions):
    """Require two nonempty decision schemas to match exactly by position."""
    source_descriptions = list(source_descriptions)
    reference_descriptions = list(reference_descriptions)
    if not source_descriptions or not reference_descriptions:
        raise ValueError("Decision variable descriptions must be nonempty")
    if len(source_descriptions) != len(reference_descriptions):
        raise ValueError(
            "Decision variable description lengths differ: "
            f"{len(source_descriptions)} != {len(reference_descriptions)}"
        )
    for index, (source, reference) in enumerate(
        zip(source_descriptions, reference_descriptions)
    ):
        if _normalized_description(source) != _normalized_description(reference):
            raise ValueError(
                f"Decision variable description mismatch at index {index}: "
                f"{source!r} != {reference!r}"
            )


_WINDOWS_HARDWARE_PATH = re.compile(
    r"[A-Za-z]:[\\/][^\s\r\n]+[\\/](?P<name>[^\\/\s\r\n]+)"
)


def prepare_tutorial_hardware(case, case_directory, repository_root=REPOSITORY_ROOT):
    """Copy and portably rewrite one tutorial's declared hardware tree."""
    repository_root = Path(repository_root)
    source_root = repository_root / case.hardware_root
    if not source_root.is_dir():
        raise FileNotFoundError(f"Tutorial hardware root does not exist: {source_root}")
    destination = Path(case_directory) / "hardware_models"
    shutil.copytree(source_root, destination, dirs_exist_ok=True)
    available = {path.name for path in destination.rglob("*") if path.is_file()}
    for hardware_file in (path for path in destination.rglob("*") if path.is_file()):
        try:
            text = hardware_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        missing = {
            match.group("name")
            for match in _WINDOWS_HARDWARE_PATH.finditer(text)
            if match.group("name") not in available
        }
        if missing:
            raise FileNotFoundError(
                f"Missing tutorial hardware dependencies in {case.hardware_root}: "
                f"{', '.join(sorted(missing))}"
            )
        rewritten = _WINDOWS_HARDWARE_PATH.sub(
            lambda match: f"/artifacts/hardware_models/{match.group('name')}",
            text,
        )
        if rewritten != text:
            hardware_file.write_text(rewritten, encoding="utf-8")
    return destination


def prepare_tutorial_universe(case, case_directory, repository_root=REPOSITORY_ROOT):
    """Stage one tutorial universe and supplement its missing shared kernels."""
    repository_root = Path(repository_root)
    source_root = repository_root / case.universe_root
    ephemeris_root = repository_root / case.ephemeris_root
    if not source_root.is_dir():
        raise FileNotFoundError(f"Tutorial universe root does not exist: {source_root}")
    if not ephemeris_root.is_dir():
        raise FileNotFoundError(
            f"Tutorial ephemeris root does not exist: {ephemeris_root}"
        )
    destination = Path(case_directory) / "universe"
    shutil.copytree(source_root, destination, dirs_exist_ok=True)
    destination_ephemeris = destination / "ephemeris_files"
    destination_ephemeris.mkdir(parents=True, exist_ok=True)
    for name in TUTORIAL_SHARED_EPHEMERIS_FILES:
        source = ephemeris_root / name
        if not source.is_file():
            raise FileNotFoundError(f"Tutorial ephemeris file does not exist: {source}")
        destination_file = destination_ephemeris / source.name
        if not destination_file.exists():
            shutil.copy2(source, destination_file)
    return destination


def validate_tutorial_case_dependencies(case, repository_root=REPOSITORY_ROOT):
    """Fail before execution when a registry source or declared root is absent."""
    repository_root = Path(repository_root)
    required = (
        case.source_options,
        case.reference_package,
        case.reference_mission,
        case.seed_alignment_source,
        case.universe_root,
        case.hardware_root,
        case.ephemeris_root,
    )
    missing = [relative for relative in required if not (repository_root / relative).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing tutorial dependencies for {case.case_id}: {', '.join(missing)}"
        )


def load_xf_descriptions(xf_file):
    """Load a contiguous ordered decision-description schema from an XF file."""
    with Path(xf_file).open(newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader, None)
        if header is None:
            raise ValueError("XF decision-description schema is missing")
        columns = {name.strip(): index for index, name in enumerate(header)}
        if not {"Xindex", "Description"}.issubset(columns):
            raise ValueError("XF decision-description schema is missing")
        descriptions = []
        for row in reader:
            if row and row[0].strip() == "Findex":
                break
            if len(row) <= max(columns.values()):
                raise ValueError("XF decision descriptions are malformed")
            try:
                row_index = int(row[columns["Xindex"]])
            except ValueError as error:
                raise ValueError("XF decision descriptions are malformed") from error
            description = row[columns["Description"]].strip()
            if row_index != len(descriptions) or not description:
                raise ValueError("XF decision descriptions are missing or out of order")
            descriptions.append(description)
    if not descriptions:
        raise ValueError("XF decision descriptions are missing or out of order")
    return descriptions


def inject_aligned_mission_seed(options, mission, expected_descriptions=None):
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
    if not option_descriptions and expected_descriptions is not None:
        option_descriptions = list(expected_descriptions)
    validate_decision_alignment(option_descriptions, descriptions)

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
    universe_root=None,
    hardware_root=None,
    expected_descriptions=None,
):
    """Prepare a run mode from an aligned committed mission seed."""
    Mission, MissionOptions = _load_pyemtg(pyemtg_root)
    case_directory = Path(case_directory)
    prepared_options = prepare_case(source_options, case_directory, pyemtg_root)
    options = MissionOptions.MissionOptions(str(prepared_options))
    baseline = Mission.Mission(str(baseline_mission))
    inject_aligned_mission_seed(
        options, baseline, expected_descriptions=expected_descriptions
    )
    options.run_inner_loop = run_inner_loop
    if execution_repository_root is not None:
        execution_repository_root = Path(execution_repository_root)
        options.universe_folder = str(
            execution_repository_root / (universe_root or "testatron/universe")
        )
        options.HardwarePath = str(
            execution_repository_root
            / (
                hardware_root
                or "docs/0_Users/tutorial/Tutorial_EMTG_Files/Config_Files/hardware_models"
            )
        )
        gravity_root = Path(options.universe_folder) / "gravity_files"
        for journey in options.Journeys:
            if journey.central_body_gravity_order == 0:
                journey.central_body_gravity_file = "DoesNotExist.grv"
            else:
                gravity_name = Path(
                    journey.central_body_gravity_file.replace("\\", "/")
                ).name
                journey.central_body_gravity_file = str(gravity_root / gravity_name)
    if execution_directory is not None:
        options.forced_working_directory = str(execution_directory)
    options.write_options_file(
        str(prepared_options), not options.print_only_non_default_options
    )
    compatibility_path = case_directory / "compatibility.json"
    compatibility = json.loads(compatibility_path.read_text())
    compatibility["source_options"] = repo_relative(compatibility["source_options"])
    compatibility_path.write_text(json.dumps(compatibility, indent=2) + "\n")
    return prepared_options


def prepare_replay(
    source_options,
    baseline_mission,
    case_directory,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
    universe_root=None,
    hardware_root=None,
    expected_descriptions=None,
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
        universe_root,
        hardware_root,
        expected_descriptions,
    )


def _prepare_osiris_replay(
    package_directory,
    case_directory,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
):
    """Prepare an immutable NASA OSIRIS-REx package for evaluate-only replay."""
    package_directory = Path(package_directory)
    source_options = package_directory / "OSIRIS-REx.emtgopt"
    baseline_mission = (
        package_directory / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    )
    Mission, MissionOptions = _load_pyemtg(pyemtg_root)
    case_directory = Path(case_directory)
    prepared_options = prepare_case(source_options, case_directory, pyemtg_root)
    options = MissionOptions.MissionOptions(str(prepared_options))
    baseline = Mission.Mission(str(baseline_mission))
    xf_file = package_directory / "XFfile.csv"
    inject_aligned_mission_seed(
        options,
        baseline,
        expected_descriptions=load_xf_descriptions(xf_file),
    )
    options.run_inner_loop = 0
    repository_root = (
        Path(execution_repository_root)
        if execution_repository_root is not None
        else REPOSITORY_ROOT
    )
    tutorial_root = (
        repository_root / "docs/0_Users/tutorial/Tutorial_EMTG_Files"
    )
    options.universe_folder = str(tutorial_root / "OSIRIS_universe")
    options.HardwarePath = str(tutorial_root / "OSIRIS-REx/hardware_models")
    for journey in options.Journeys:
        journey.central_body_gravity_file = "DoesNotExist.grv"
    if execution_directory is not None:
        options.forced_working_directory = str(execution_directory)
    options.write_options_file(
        str(prepared_options), not options.print_only_non_default_options
    )
    compatibility_path = case_directory / "compatibility.json"
    compatibility = json.loads(compatibility_path.read_text())
    compatibility["source_options"] = repo_relative(compatibility["source_options"])
    compatibility["seed_alignment_source"] = repo_relative(xf_file)
    compatibility_path.write_text(json.dumps(compatibility, indent=2) + "\n")
    return prepared_options


def prepare_osiris_2022_replay(
    case_directory,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
):
    """Prepare the immutable NASA 2022 package for evaluate-only replay."""
    return _prepare_osiris_replay(
        OSIRIS_2022_PACKAGE,
        case_directory,
        pyemtg_root,
        execution_repository_root,
        execution_directory,
    )


def prepare_osiris_2024_replay(
    case_directory,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
):
    """Prepare the immutable NASA 2024 package for evaluate-only replay."""
    return _prepare_osiris_replay(
        OSIRIS_2024_PACKAGE,
        case_directory,
        pyemtg_root,
        execution_repository_root,
        execution_directory,
    )


def _prepare_osiris_refinement(
    package_directory,
    case_directory,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
):
    """Prepare direct IPOPT refinement from an aligned NASA package seed."""
    prepared_options = _prepare_osiris_replay(
        package_directory,
        case_directory,
        pyemtg_root,
        execution_repository_root,
        execution_directory,
    )
    _, MissionOptions = _load_pyemtg(pyemtg_root)
    options = MissionOptions.MissionOptions(str(prepared_options))
    options.run_inner_loop = 3
    options.quiet_NLP = 0
    options.enable_NLP_chaperone = 1
    options.write_options_file(
        str(prepared_options), not options.print_only_non_default_options
    )
    return prepared_options


def prepare_osiris_2022_refinement(
    case_directory,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
):
    """Prepare direct IPOPT refinement from the aligned NASA 2022 seed."""
    return _prepare_osiris_refinement(
        OSIRIS_2022_PACKAGE,
        case_directory,
        pyemtg_root,
        execution_repository_root,
        execution_directory,
    )


def prepare_osiris_2024_refinement(
    case_directory,
    pyemtg_root=PYEMTG_ROOT,
    execution_repository_root=None,
    execution_directory=None,
):
    """Prepare direct IPOPT refinement from the aligned NASA 2024 seed."""
    return _prepare_osiris_refinement(
        OSIRIS_2024_PACKAGE,
        case_directory,
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
    universe_root=None,
    hardware_root=None,
    expected_descriptions=None,
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
        universe_root,
        hardware_root,
        expected_descriptions,
    )
    _, MissionOptions = _load_pyemtg(pyemtg_root)
    options = MissionOptions.MissionOptions(str(prepared_options))
    options.quiet_NLP = 0
    options.enable_NLP_chaperone = 1
    options.write_options_file(
        str(prepared_options), not options.print_only_non_default_options
    )
    return prepared_options


def tutorial_objective_policy(case):
    """Return the fixed refinement objective policy for a tutorial case."""
    if case.taxonomy == "authoritative":
        return AUTHORITATIVE_REFINEMENT_POLICY
    if case.taxonomy == "demonstration":
        return DEMONSTRATION_REFINEMENT_POLICY
    raise ValueError(f"Tutorial case {case.case_id!r} has no refinement policy")


def objective_sense(objective_type):
    """Return the documented optimization direction for an EMTG objective type."""
    maximizing_types = {2, 3, 4, 6, 9, 11, 12, 14, 15, 16, 17, 18, 19, 26}
    return "maximize" if objective_type in maximizing_types else "minimize"


def prepare_tutorial_schema_probe(
    case,
    case_directory,
    *,
    repository_root=REPOSITORY_ROOT,
    execution_repository_root="/repo",
    execution_directory="/artifacts",
):
    """Prepare an evaluate-only current model that emits its decision schema."""
    if not case.schema_probe:
        raise ValueError(f"Tutorial case {case.case_id!r} does not need a schema probe")
    repository_root = Path(repository_root)
    validate_tutorial_case_dependencies(case, repository_root)
    prepare_tutorial_universe(case, case_directory, repository_root)
    prepare_tutorial_hardware(case, case_directory, repository_root)
    _, MissionOptions = _load_pyemtg()
    prepared_options = prepare_case(
        repository_root / case.source_options, case_directory
    )
    options = MissionOptions.MissionOptions(str(prepared_options))
    options.run_inner_loop = 0
    options.universe_folder = str(Path(execution_directory) / "universe")
    options.HardwarePath = str(Path(execution_directory) / "hardware_models")
    options.forced_working_directory = str(execution_directory)
    for journey in options.Journeys:
        if journey.central_body_gravity_order == 0:
            journey.central_body_gravity_file = "DoesNotExist.grv"
        else:
            gravity_name = Path(
                journey.central_body_gravity_file.replace("\\", "/")
            ).name
            journey.central_body_gravity_file = str(
                Path(options.universe_folder) / "gravity_files" / gravity_name
            )
    options.write_options_file(
        str(prepared_options), not options.print_only_non_default_options
    )
    return prepared_options


def prepare_tutorial_case(
    case,
    stage,
    case_directory,
    *,
    repository_root=REPOSITORY_ROOT,
    execution_repository_root="/repo",
    execution_directory="/artifacts",
    schema_descriptions=None,
):
    """Prepare one tutorial replay or refinement from its declared seed policy."""
    if stage not in case.stages:
        raise ValueError(f"Stage {stage!r} is disabled for {case.case_id!r}")
    repository_root = Path(repository_root)
    source_options = repository_root / case.source_options
    seed_source = (
        case.replay_seed_source
        if stage == "replay"
        else case.refinement_seed_source
    )
    if case.schema_probe and schema_descriptions is None:
        raise ValueError(f"Tutorial case {case.case_id!r} requires a schema probe")
    validate_tutorial_case_dependencies(case, repository_root)
    prepare_tutorial_universe(case, case_directory, repository_root)
    prepare_tutorial_hardware(case, case_directory, repository_root)

    if seed_source == "archive":
        prepare = prepare_replay if stage == "replay" else prepare_refinement
        return prepare(
            source_options,
            repository_root / case.reference_mission,
            case_directory,
            execution_repository_root=execution_repository_root,
            execution_directory=execution_directory,
            universe_root=str(Path(execution_directory) / "universe"),
            hardware_root=str(Path(execution_directory) / "hardware_models"),
            expected_descriptions=schema_descriptions,
        )
    if seed_source != "current_infeasible_trial":
        raise ValueError(f"Unknown tutorial seed source: {seed_source!r}")

    _, MissionOptions = _load_pyemtg()
    prepared_options = prepare_case(source_options, case_directory)
    options = MissionOptions.MissionOptions(str(prepared_options))
    options.AssembleMasterDecisionVector()
    source_trial = list(options.trialX)
    if case.refinement_seed_options:
        seed_options = MissionOptions.MissionOptions(
            str(repository_root / case.refinement_seed_options)
        )
        seed_options.AssembleMasterDecisionVector()
        validate_decision_alignment(
            [entry[0] for entry in source_trial],
            [entry[0] for entry in seed_options.trialX],
        )
        source_trial = list(seed_options.trialX)
    source_descriptions = [entry[0] for entry in source_trial]
    reference_descriptions = load_xf_descriptions(
        repository_root / case.seed_alignment_source
    )
    validate_decision_alignment(source_descriptions, reference_descriptions)
    options.trialX = source_trial
    options.DisassembleMasterDecisionVector()
    options.run_inner_loop = 0 if stage == "replay" else 3
    options.quiet_NLP = 0
    options.enable_NLP_chaperone = 1
    options.universe_folder = str(Path(execution_directory) / "universe")
    options.HardwarePath = str(Path(execution_directory) / "hardware_models")
    options.forced_working_directory = str(execution_directory)
    for journey in options.Journeys:
        if journey.central_body_gravity_order == 0:
            journey.central_body_gravity_file = "DoesNotExist.grv"
        else:
            gravity_name = Path(
                journey.central_body_gravity_file.replace("\\", "/")
            ).name
            journey.central_body_gravity_file = str(
                Path(options.universe_folder) / "gravity_files" / gravity_name
            )
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


def _structural_event_topology(mission):
    report_events = {"coast", "match_point"}
    topology = []
    for journey in mission.Journeys:
        structural_events = []
        for event in journey.missionevents:
            identity = (event.EventType, event.Location)
            if event.EventType in report_events:
                continue
            if not structural_events or structural_events[-1] != identity:
                structural_events.append(identity)
        topology.append(tuple(structural_events))
    return tuple(topology)


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


def compare_refinement(
    baseline,
    generated,
    feasibility_tolerance,
    *,
    objective_policy=None,
    objective_sense="minimize",
):
    """Check feasibility, topology, and objective non-regression after refinement."""
    bound_absolute_tolerance = 1.0e-12
    bound_relative_tolerance = 1.0e-10
    objective_policy = objective_policy or LEGACY_REFINEMENT_POLICY
    if objective_sense not in {"minimize", "maximize"}:
        raise ValueError(f"Unknown objective sense: {objective_sense!r}")
    decision_bounds_complete = (
        len(generated.DecisionVector)
        == len(generated.Xlowerbounds)
        == len(generated.Xupperbounds)
        and bool(generated.DecisionVector)
    )

    def decision_value_in_bounds(value, lower_bound, upper_bound):
        tolerance = bound_absolute_tolerance + bound_relative_tolerance * max(
            abs(value), abs(lower_bound), abs(upper_bound)
        )
        return lower_bound - tolerance <= value <= upper_bound + tolerance

    objective_band = (
        objective_policy.absolute_tolerance
        + objective_policy.relative_tolerance
        * max(abs(baseline.objective_value), abs(generated.objective_value))
    )
    objective_delta = generated.objective_value - baseline.objective_value
    objective_non_regression = (
        objective_delta <= objective_band
        if objective_sense == "minimize"
        else objective_delta >= -objective_band
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
        "event_topology": _structural_event_topology(generated)
        == _structural_event_topology(baseline),
        "decision_descriptions": [
            _normalized_description(description)
            for description in generated.Xdescriptions
        ]
        == [
            _normalized_description(description)
            for description in baseline.Xdescriptions
        ],
        "objective_non_regression": objective_non_regression,
    }
    return {
        "status": "unreviewed",
        "acceptable": all(checks.values()),
        "checks": checks,
        "baseline_objective": baseline.objective_value,
        "generated_objective": generated.objective_value,
        "objective_sense": objective_sense,
        "objective_relative_tolerance": objective_policy.relative_tolerance,
        "objective_absolute_tolerance": objective_policy.absolute_tolerance,
        "objective_comparison_band": objective_band,
        "objective_delta": objective_delta,
        "objective_absolute_delta": abs(objective_delta),
        "generated_feasibility_metric": abs(generated.worst_violation),
        "feasibility_tolerance": feasibility_tolerance,
    }


def compare_deliberate_infeasible(baseline, generated, feasibility_tolerance):
    """Accept a tutorial replay only when it reproduces the intended failure."""
    finite_decision_vector = bool(generated.DecisionVector) and all(
        math.isfinite(value) for value in generated.DecisionVector
    )
    finite_constraint_vector = bool(generated.ConstraintVector) and all(
        math.isfinite(value) for value in generated.ConstraintVector
    )
    try:
        validate_decision_alignment(
            generated.Xdescriptions, baseline.Xdescriptions
        )
        descriptions_match = True
    except ValueError:
        descriptions_match = False
    checks = {
        "journey_names": [journey.journey_name for journey in generated.Journeys]
        == [journey.journey_name for journey in baseline.Journeys],
        "event_topology": _structural_event_topology(generated)
        == _structural_event_topology(baseline),
        "decision_descriptions": descriptions_match,
        "finite_decision_vector": finite_decision_vector,
        "finite_constraint_vector": finite_constraint_vector,
        "intentionally_infeasible": math.isfinite(generated.worst_violation)
        and abs(generated.worst_violation) > feasibility_tolerance,
    }
    return {
        "status": "unreviewed",
        "acceptable": all(checks.values()),
        "checks": checks,
        "generated_feasibility_metric": abs(generated.worst_violation),
        "feasibility_tolerance": feasibility_tolerance,
    }


def parse_ipopt_log(log_text, initialization_policy=None):
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
    if not all((initial_match, iterations_match, violation_match, exit_match)):
        raise ValueError("IPOPT log is missing required refinement diagnostics")
    if initialization_match is None and initialization_policy is None:
        raise ValueError("IPOPT log is missing required refinement diagnostics")
    return {
        "initialization_policy": (
            initialization_match.group("policy")
            if initialization_match is not None
            else initialization_policy
        ),
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


def _write_numeric_comparison(baseline, generated, comparison_file):
    metrics = (
        ("objective_value", baseline.objective_value, generated.objective_value),
        ("worst_violation", baseline.worst_violation, generated.worst_violation),
        (
            "total_deterministic_deltav",
            baseline.total_deterministic_deltav,
            generated.total_deterministic_deltav,
        ),
        (
            "total_flight_time_years",
            baseline.total_flight_time_years,
            generated.total_flight_time_years,
        ),
        (
            "final_mass_including_propellant_margin",
            baseline.final_mass_including_propellant_margin,
            generated.final_mass_including_propellant_margin,
        ),
    )
    with Path(comparison_file).open("w", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=("metric", "baseline_value", "generated_value", "delta"),
        )
        writer.writeheader()
        for metric, baseline_value, generated_value in metrics:
            writer.writerow(
                {
                    "metric": metric,
                    "baseline_value": baseline_value,
                    "generated_value": generated_value,
                    "delta": generated_value - baseline_value,
                }
            )


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

    _write_numeric_comparison(baseline, generated, comparison_file)
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

    cases = discover_cases(TESTS_ROOT, filters=args.filter)
    previous = {
        result.case_id: result for result in _load_case_results(output_root)
    } if args.resume else {}
    results = []
    for index, source_options in enumerate(cases, start=1):
        identifier = case_id(source_options, TESTS_ROOT)
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