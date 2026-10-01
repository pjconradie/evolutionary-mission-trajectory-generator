from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from osiris_rex import (
    CONFIG_DIR,
    MISSION_ROOT,
    REPO_ROOT,
    RESULTS_DIR,
    prepare,
)


PREFERRED_IMAGE = "emtg-pytest-toolchain:309abb32ff087c0b"
PLATFORM = "linux/amd64"
BUILD_VOLUME = "emtg-osiris-rex-build"


def run(command: list[str], *, timeout: int = 3600) -> subprocess.CompletedProcess:
    result = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout[-12000:]}"
        )
    return result


def ensure_docker(timeout_seconds: int = 120) -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker CLI is not installed or not on PATH")

    result = subprocess.run(
        ["docker", "info"], capture_output=True, text=True, timeout=15
    )
    if result.returncode == 0:
        return

    if sys.platform == "darwin":
        subprocess.Popen(["open", "-a", "Docker"])
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            time.sleep(2)
            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                return

    detail = (result.stderr or result.stdout).strip()
    raise RuntimeError(
        "Docker daemon is not healthy. Start Docker Desktop and retry. "
        f"Last response: {detail}"
    )


def select_image() -> str:
    # The supplied toolchain image may predate the high-fidelity converter's
    # SciPy requirement. Only reuse it if that runtime dependency is present.
    result = subprocess.run(
        [
            "docker", "run", "--rm", "--platform", PLATFORM,
            PREFERRED_IMAGE, "python", "-c", "import scipy",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode == 0:
        return PREFERRED_IMAGE

    # The updated Dockerfile is content-addressed by the repository helper.
    # This focused test builds that image if absent and runs a real IPOPT case.
    run(
        [
            sys.executable, "-m", "pytest",
            "tests/integration/test_ipopt_backend.py::"
            "test_ipopt_runs_direct_nlp_mission",
            "--integration", "-q",
        ],
        timeout=3600,
    )

    # Read the tag using the repository's own helper, ensuring the image used
    # by this simulation matches the tested image.
    helper = REPO_ROOT / "tests" / "integration" / "_docker_support.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("_docker_support", helper)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import repository Docker helper: {helper}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.toolchain_image_tag(REPO_ROOT)


def docker_run(
    image: str,
    command: str,
    *,
    timeout: int = 3600,
    log_path: Path | None = None,
) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    full_command = [
        "docker", "run", "--rm",
        "--platform", PLATFORM,
        "-v", f"{REPO_ROOT}:/repo:ro",
        "-v", f"{MISSION_ROOT}:/mission:rw",
        "-v", f"{BUILD_VOLUME}:/build",
        "-w", "/repo",
        image, "bash", "-lc", command,
    ]

    try:
        result = run(full_command, timeout=timeout)
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        if log_path:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(str(exc), encoding="utf-8")
        raise

    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(result.stdout, encoding="utf-8")


def prepare_container_build() -> str:
    """Create the stable CMake source wrapper and configure the shared build."""
    return (
        "mkdir -p /mission/.emtg-source; "
        "ln -sfn /repo/src /mission/.emtg-source/src; "
        "ln -sfn /repo/tests /mission/.emtg-source/tests; "
        "cp /repo/CMakeLists.txt /mission/.emtg-source/CMakeLists.txt; "
        "cat >/mission/.emtg-source/EMTG-Config.cmake <<'CMAKE'\n"
        "set(CSPICE_DIR /opt/emtg-deps/cspice)\n"
        "set(SNOPT_ROOT_DIR /tmp/emtg-intentionally-missing-snopt)\n"
        "set(GSL_PATH /opt/emtg-deps/gsl)\n"
        "set(BOOST_ROOT /usr)\n"
        "set(Boost_NO_BOOST_CMAKE ON)\n"
        "CMAKE\n"
        "if [ -f /build/CMakeCache.txt ] && "
        "! grep -Fq 'CMAKE_HOME_DIRECTORY:INTERNAL=/mission/.emtg-source' "
        "/build/CMakeCache.txt; then "
        "find /build -mindepth 1 -maxdepth 1 -exec rm -rf {} +; fi; "
        "cmake -S /mission/.emtg-source -B /build -DEMTG_NLP_SOLVER=IPOPT; "
    )


def build_and_run(
    image: str,
    options_name: str,
    stage: str,
    config_subdirectory: str = "",
) -> None:
    options_path = f"/mission/config/{config_subdirectory}/{options_name}" if config_subdirectory else f"/mission/config/{options_name}"
    expected_result = f"/mission/results/{stage}/{Path(options_name).stem}.emtg"
    log_path = RESULTS_DIR / stage / "emtg.log"

    configure_options = (
        "python3 -c \"import MissionOptions; "
        f"o=MissionOptions.MissionOptions('{options_path}'); "
        f"o.forced_working_directory='/mission/results/{stage}'; "
    )
    if stage == "high_fidelity":
        # Refine with a direct NLP solve; constrain Earth periapsis (Journey 1)
        # and Bennu arrival (Journey 3) to the UTC day windows converted by SPICE.
        # SOI crossing Journeys 0 and 2 must remain free to bracket the flyby.
        configure_options += (
            "import json; "
            "targets=json.load(open('/mission/config/state_conversion.json'))"
            "['target_event_date_bounds_mjd_tdb']; "
            "o.run_inner_loop=3; "
            "assert len(o.Journeys)==4, 'Expected 4 HF Journeys'; "
            "[setattr(j,'timebounded',0) for j in o.Journeys]; "
            "o.Journeys[1].timebounded=2; "
            "o.Journeys[1].arrival_date_bounds=targets['earth_periapsis']; "
            "o.Journeys[3].timebounded=2; "
            "o.Journeys[3].arrival_date_bounds=targets['bennu_arrival']; "
            "first_dsm='p0b0_epoch_abs_{:.12g}_{:.12g}'.format(*targets['first_dsm_epoch']); "
            "o.Journeys[0].ManeuverConstraintDefinitions=[c for c in "
            "o.Journeys[0].ManeuverConstraintDefinitions if 'p0b0_epoch_abs_' not in c]; "
            "o.Journeys[0].ManeuverConstraintDefinitions.append(first_dsm); "
            "o.AssembleMasterConstraintVectors(); "
        )
    elif stage == "single_phase":
        # The split patched-conic mission has Journey 0 arriving at Earth and
        # Journey 1 arriving at Bennu. Bound those event dates before the fresh
        # single-phase solve; do not carry a prior run's solution as a seed.
        configure_options += (
            "import json; "
            "targets=json.load(open('/mission/config/state_conversion.json'))"
            "['target_event_date_bounds_mjd_tdb']; "
            "assert len(o.Journeys)==2, 'Expected 2 single-phase Journeys'; "
            "o.Journeys[0].timebounded=2; "
            "o.Journeys[0].arrival_date_bounds=targets['earth_periapsis']; "
            "o.Journeys[1].timebounded=2; "
            "o.Journeys[1].arrival_date_bounds=targets['bennu_arrival']; "
            "first_dsm='p0b0_epoch_abs_{:.12g}_{:.12g}'.format(*targets['first_dsm_epoch']); "
            "o.Journeys[0].ManeuverConstraintDefinitions=[c for c in "
            "o.Journeys[0].ManeuverConstraintDefinitions if 'p0b0_epoch_abs_' not in c]; "
            "o.Journeys[0].ManeuverConstraintDefinitions.append(first_dsm); "
            "o.AssembleMasterConstraintVectors(); "
        )
    configure_options += (
        f"o.write_options_file('{options_path}', True)\"; "
    )

    command = (
        "set -euo pipefail; "
        f"mkdir -p /mission/results/{stage}; "
        f"rm -f {expected_result} "
        f"/mission/results/{stage}/FAILURE_{Path(options_name).stem}.emtg "
        f"/mission/results/{stage}/{Path(options_name).stem}archive.emtg_archive "
        f"/mission/results/{stage}/XFfile.csv; "
        "export PYTHONPATH=/repo/PyEMTG; "
        + configure_options
        + prepare_container_build()
        + "cmake --build /build --target EMTGv9 -j2; "
        + f"cd /mission/results/{stage}; "
        + f"timeout 7200 /build/src/EMTGv9 {options_path}; "
        + f"test -s {expected_result}; "
        + f"test ! -e /mission/results/{stage}/FAILURE_{Path(options_name).stem}.emtg; "
        + "python3 -c \"import Mission; "
        + f"m=Mission.Mission('{expected_result}'); "
        + "assert m.solution_attempt_index_that_produced_best_feasible_solution > 0, "
        + "f'EMTG found no feasible solution attempt (first_nlp_feasible={m.first_nlp_solve_feasible}, "
        + "best_feasible_attempt={m.solution_attempt_index_that_produced_best_feasible_solution}, "
        + "worst_violation={m.worst_violation})'\""
    )
    docker_run(image, command, timeout=7500, log_path=log_path)


def run_pipeline() -> None:
    # Create the complete mission workspace before preparing options or
    # invoking Docker/converter stages. This keeps each stage independent of
    # whichever directories happened to be left by a previous run.
    for directory in (
        MISSION_ROOT / "hardware-models",
        MISSION_ROOT / "universe" / "ephemeris_files",
        CONFIG_DIR,
        CONFIG_DIR / "high_fidelity",
        RESULTS_DIR,
        RESULTS_DIR / "low",
        RESULTS_DIR / "single_phase",
        RESULTS_DIR / "high_fidelity",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    # Validate mission inputs before Docker checks/builds so missing SPICE
    # kernels fail immediately instead of waiting for the IPOPT fallback.
    options = prepare()
    ensure_docker()
    image = select_image()

    build_and_run(image, options.name, "low")

    # The next conversion stages are run inside the container so PyEMTG uses
    # the repository's Python modules. The high-fidelity driver is a converter,
    # not an optimizer; each generated options file needs a separate EMTG run.
    low_name = "OSIRIS_REx_Low"
    low_options = f"/mission/config/{low_name}.emtgopt"
    low_result = f"/mission/results/low/{low_name}.emtg"

    convert = (
        "set -euo pipefail; "
        "export PYTHONPATH=/repo/PyEMTG:/repo/PyEMTG/Converters:"
        "/repo/PyEMTG/HighFidelity; "
        f"python3 /repo/PyEMTG/Converters/convert_to_single_phase_journeys.py "
        f"{low_options} {low_result}"
    )
    docker_run(
        image,
        convert,
        timeout=900,
        log_path=RESULTS_DIR / "single_phase_conversion.log",
    )

    # The standard high-fidelity converter relies on a compatible parsed
    # solution. Stop rather than silently treating conversion as optimization.
    single_options = f"/mission/config/{low_name}_singlePhase.emtgopt"
    single_result = f"/mission/results/single_phase/{low_name}_singlePhase.emtg"

    build_and_run(
        image,
        Path(single_options).name,
        "single_phase",
    )

    high_driver = (
        "set -euo pipefail; "
        "mkdir -p /mission/config/high_fidelity; "
        "export PYTHONPATH=/repo/PyEMTG:/repo/PyEMTG/Converters:"
        "/repo/PyEMTG/HighFidelity; "
        f"test -s {single_options}; test -s {single_result}; "
        "python3 /repo/PyEMTG/HighFidelity/HighFidelityDriver.py "
        f"{single_options} {single_result} /mission/config/high_fidelity"
    )
    docker_run(
        image,
        high_driver,
        timeout=900,
        log_path=RESULTS_DIR / "high_fidelity_conversion.log",
    )

    # High-fidelity driver output name is derived from the source .emtg name.
    high_options = (
        "/mission/config/high_fidelity/"
        f"{low_name}_singlePhase_HighFidelity.emtgopt"
    )
    build_and_run(
        image,
        Path(high_options).name,
        "high_fidelity",
        config_subdirectory="high_fidelity",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["run"],
        help="Prepare options, check Docker/IPOPT, and run mission stages",
    )
    parser.parse_args()
    run_pipeline()


if __name__ == "__main__":
    main()