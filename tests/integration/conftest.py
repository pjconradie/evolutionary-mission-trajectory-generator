"""Fixtures for disposable Linux toolchain integration tests."""

import json
import uuid
from pathlib import Path

import pytest
import Mission
import MissionOptions

from testatron import ipopt_characterization

from _docker_support import (
    artifact_directory,
    build_clean_toolchain_image,
    build_volume_name,
    ensure_toolchain_image,
    remove_build_volume,
    remove_toolchain_image,
    run_probe,
)


@pytest.fixture(scope="session")
def toolchain_image(repository_root, tmp_path_factory):
    """Return the reusable content-addressed Linux toolchain image."""
    return ensure_toolchain_image(repository_root, tmp_path_factory)


@pytest.fixture(scope="session")
def clean_toolchain_image(repository_root, tmp_path_factory):
    """Build and remove one uniquely tagged uncached Linux toolchain image."""
    image = build_clean_toolchain_image(repository_root, tmp_path_factory)
    try:
        yield image
    finally:
        remove_toolchain_image(image)


@pytest.fixture(scope="session")
def clean_bootstrap_probe(clean_toolchain_image, repository_root, tmp_path_factory):
    """Build and run the dependency and IPOPT stack without reusable layers."""
    script = _backend_source_script("IPOPT") + r'''
set -eu
check() { printf "EMTG_CHECK %s=%s\n" "$1" "$2"; }
trap 'for log in /tmp/clean-*.log; do test ! -f "$log" || cp "$log" /artifacts/; done' EXIT
test "$(uname -m)" = x86_64
test "$(. /etc/os-release; printf '%s' "$VERSION_ID")" = 12
case "$(python --version | awk '{print $2}')" in 3.12.*) ;; *) exit 19 ;; esac
test "$(pkg-config --modversion ipopt)" = 3.11.9
test -f /opt/emtg-deps/cspice/include/SpiceUsr.h
test -f /opt/emtg-deps/cspice/lib/libcspice.a
test "$(ar t /opt/emtg-deps/cspice/lib/libcspice.a | wc -l | tr -d ' ')" = 2229
g++ -std=c++17 -Wall -Wextra -Werror \
    /repo/tests/cpp/dependency_probe.cpp \
    -I/opt/emtg-deps/cspice/include \
    /opt/emtg-deps/cspice/lib/libcspice.a \
    -lboost_filesystem -lboost_system -lboost_serialization \
    -lgsl -lgslcblas $(pkg-config --cflags --libs ipopt) \
    -lm -o /tmp/dependency_probe \
    >/tmp/clean-dependency-build.log 2>&1
check clean_dependency_compile passed
ldd /tmp/dependency_probe >/tmp/clean-dependency-ldd.log
! grep -Fq "not found" /tmp/clean-dependency-ldd.log
/tmp/dependency_probe >/tmp/clean-dependency-runtime.log 2>&1
check clean_dependency_runtime passed
cp /tmp/configure.log /tmp/clean-ipopt-configure.log
grep -Fq "NLP backend: IPOPT" /tmp/clean-ipopt-configure.log
grep -Fq "IPOPT 3.11.9 found through pkg-config" /tmp/clean-ipopt-configure.log
! grep -Fqi "snopt" /tmp/clean-ipopt-configure.log
check clean_ipopt_configure passed
cmake --build /build \
    --target ipopt_adapter_compile_contract ipopt_adapter_contract EMTGv9 -j2 \
    >/tmp/clean-ipopt-build.log 2>&1 \
    || { tail -n 150 /tmp/clean-ipopt-build.log; exit 20; }
check clean_ipopt_build passed
ctest --test-dir /build -R '^ipopt_adapter_contract$' -V \
    >/tmp/clean-ipopt-ctest.log 2>&1 \
    || { cat /tmp/clean-ipopt-ctest.log; exit 21; }
check clean_ipopt_ctest passed
ldd /build/src/EMTGv9 >/tmp/clean-ipopt-ldd.log
grep -Fq "libipopt.so" /tmp/clean-ipopt-ldd.log
! grep -Fqi "snopt" /tmp/clean-ipopt-ldd.log
! grep -Fq "not found" /tmp/clean-ipopt-ldd.log
check clean_ipopt_dynamic_linking resolved
check clean_bootstrap passed
'''
    volume = f"emtg-pytest-clean-ipopt-{uuid.uuid4().hex}"
    try:
        return run_probe(
            image=clean_toolchain_image,
            repository_root=repository_root,
            script=script,
            probe_name="clean-bootstrap",
            tmp_path_factory=tmp_path_factory,
            build_volume=volume,
            writable_artifacts=artifact_directory(tmp_path_factory),
        )
    finally:
        remove_build_volume(volume)


@pytest.fixture(scope="session")
def platform_probe(toolchain_image, repository_root, tmp_path_factory):
    """Report immutable platform, package, and CSPICE properties."""
    script = r'''
set -eu
check() { printf "EMTG_CHECK %s=%s\n" "$1" "$2"; }
test "$(uname -m)" = x86_64
check architecture "$(uname -m)"
. /etc/os-release
test "$ID" = debian
test "$VERSION_ID" = 12
check debian_version "$VERSION_ID"
python_version=$(python --version | awk '{print $2}')
case "$python_version" in 3.12.*) ;; *) exit 10 ;; esac
check python_version "$python_version"
check packages installed
check compiler_version "$(g++ -dumpfullversion)"
check cmake_version "$(cmake --version | awk 'NR == 1 {print $3}')"
check pkg_config_version "$(pkg-config --version)"
check gsl_version "$(pkg-config --modversion gsl)"
check ipopt_version "$(pkg-config --modversion ipopt)"
archive=/repo/depend/cspice-c_pc_linux_gcc_64bit/cspice.tar.Z
checksum=$(sha256sum "$archive" | awk '{print $1}')
test "$checksum" = 60a95b51a6472f1afe7e40d77ebdee43c12bb5b8823676ccc74692ddfede06ce
check cspice_checksum "$checksum"
test -f /opt/emtg-deps/cspice/makeall.csh
test -f /opt/emtg-deps/cspice/include/SpiceUsr.h
test -f /opt/emtg-deps/cspice/lib/libcspice.a
check cspice_payload valid
objects=$(ar t /opt/emtg-deps/cspice/lib/libcspice.a | wc -l | tr -d ' ')
test "$objects" = 2229
check cspice_objects "$objects"
'''
    return run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="platform",
        tmp_path_factory=tmp_path_factory,
    )


@pytest.fixture(scope="session")
def dependency_probe(toolchain_image, repository_root, tmp_path_factory):
    """Compile, link, and run the extracted dependency probe."""
    script = r'''
set -eu
check() { printf "EMTG_CHECK %s=%s\n" "$1" "$2"; }
g++ -std=c++17 -Wall -Wextra -Werror \
    /repo/tests/cpp/dependency_probe.cpp \
    -I/opt/emtg-deps/cspice/include \
    /opt/emtg-deps/cspice/lib/libcspice.a \
    -lboost_filesystem -lboost_system -lboost_serialization \
    -lgsl -lgslcblas $(pkg-config --cflags --libs ipopt) \
    -lm -o /tmp/dependency_probe
check dependency_compile passed
ldd /tmp/dependency_probe >/tmp/dependency-probe.ldd
! grep -Fq "not found" /tmp/dependency-probe.ldd
check dynamic_linking resolved
/tmp/dependency_probe
check dependency_runtime passed
'''
    return run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="dependencies",
        tmp_path_factory=tmp_path_factory,
    )


@pytest.fixture(scope="session")
def cmake_policy_probe(toolchain_image, repository_root, tmp_path_factory):
    """Check invalid, default IPOPT, and explicit SNOPT configuration policy."""
    script = r'''
set -eu
check() { printf "EMTG_CHECK %s=%s\n" "$1" "$2"; }
make_source() {
    destination=$1
    mkdir -p "$destination"
    ln -s /repo/src "$destination/src"
    ln -s /repo/tests "$destination/tests"
    cp /repo/CMakeLists.txt "$destination/CMakeLists.txt"
    cat >"$destination/EMTG-Config.cmake" <<'CMAKE'
set(CSPICE_DIR /opt/emtg-deps/cspice)
set(SNOPT_ROOT_DIR /tmp/emtg-intentionally-missing-snopt)
set(GSL_PATH /opt/emtg-deps/gsl)
set(BOOST_ROOT /usr)
set(Boost_NO_BOOST_CMAKE ON)
CMAKE
}
make_source /tmp/emtg-policy
set +e
cmake -S /tmp/emtg-policy -B /tmp/invalid \
    -DEMTG_NLP_SOLVER=INVALID >/tmp/invalid.log 2>&1
invalid_status=$?
set -e
test "$invalid_status" -ne 0
grep -Fq "Unsupported EMTG_NLP_SOLVER 'INVALID'" /tmp/invalid.log
check cmake_invalid_solver_rejection passed
cmake -S /tmp/emtg-policy -B /tmp/default >/tmp/default.log 2>&1
grep -Fq "NLP backend: IPOPT" /tmp/default.log
grep -Fq "IPOPT 3.11.9 found through pkg-config" /tmp/default.log
! grep -Fq "Now checking on SNOPT" /tmp/default.log
check cmake_default_ipopt passed
mkdir /tmp/snopt-policy
cp /repo/CMakeLists.txt /tmp/snopt-policy/CMakeLists.txt
printf '%s\n' 'set(SNOPT_ROOT_DIR /tmp/emtg-intentionally-missing-snopt)' \
    >/tmp/snopt-policy/EMTG-Config.cmake
set +e
cmake -S /tmp/snopt-policy -B /tmp/snopt-build \
    -DEMTG_NLP_SOLVER=SNOPT >/tmp/snopt.log 2>&1
snopt_status=$?
set -e
test "$snopt_status" -ne 0
tr '\n' ' ' </tmp/snopt.log | tr -s ' ' >/tmp/snopt-normalized.log
grep -Fq "SNOPT directory specified (/tmp/emtg-intentionally-missing-snopt) does not exist" \
    /tmp/snopt-normalized.log
! grep -Fq "Now checking for CSpice" /tmp/snopt.log
check cmake_snopt_gate passed
'''
    return run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="cmake-policy",
        tmp_path_factory=tmp_path_factory,
    )


def _backend_source_script(backend):
    return rf'''
set -eu
check() {{ printf "EMTG_CHECK %s=%s\n" "$1" "$2"; }}
rm -rf /tmp/emtg-source
mkdir /tmp/emtg-source
ln -s /repo/src /tmp/emtg-source/src
ln -s /repo/tests /tmp/emtg-source/tests
cp /repo/CMakeLists.txt /tmp/emtg-source/CMakeLists.txt
cat >/tmp/emtg-source/EMTG-Config.cmake <<'CMAKE'
set(CSPICE_DIR /opt/emtg-deps/cspice)
set(SNOPT_ROOT_DIR /tmp/emtg-intentionally-missing-snopt)
set(GSL_PATH /opt/emtg-deps/gsl)
set(BOOST_ROOT /usr)
set(Boost_NO_BOOST_CMAKE ON)
CMAKE
cmake -S /tmp/emtg-source -B /build \
    -DEMTG_NLP_SOLVER={backend} -DBUILD_NLP_CONTRACT_TESTS=ON \
    >/tmp/configure.log 2>&1
'''


@pytest.fixture(scope="session")
def none_backend_probe(toolchain_image, repository_root, tmp_path_factory):
    """Build and test only the solver-neutral NONE backend."""
    script = _backend_source_script("NONE") + r'''
! grep -Fq "Now checking on SNOPT" /tmp/configure.log
check none_backend_configure passed
cmake --build /build --target emtg nlp_pure_contract nlp_interface_contract -j2 \
    >/tmp/build.log 2>&1 || { tail -n 150 /tmp/build.log; exit 13; }
check none_backend_compile passed
ctest --test-dir /build --output-on-failure \
    >/tmp/ctest.log 2>&1 || { cat /tmp/ctest.log; exit 14; }
check nlp_contract passed
'''
    volume = build_volume_name(toolchain_image, "none")
    return run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="none-backend",
        tmp_path_factory=tmp_path_factory,
        build_volume=volume,
    )


@pytest.fixture(scope="session")
def ipopt_backend_probe(toolchain_image, repository_root, tmp_path_factory):
    """Build and inspect only the default IPOPT executable."""
    script = _backend_source_script("IPOPT") + r'''
grep -Fq "NLP backend: IPOPT" /tmp/configure.log
grep -Fq "IPOPT 3.11.9 found through pkg-config" /tmp/configure.log
! grep -Fq "Now checking on SNOPT" /tmp/configure.log
check cmake_default_ipopt passed
cmake --build /build --target ipopt_adapter_compile_contract -j2 \
    >/tmp/adapter-build.log 2>&1 || { tail -n 150 /tmp/adapter-build.log; exit 15; }
check ipopt_adapter_compile passed
cmake --build /build --target EMTGv9 -j2 \
    >/tmp/build.log 2>&1 || { tail -n 150 /tmp/build.log; exit 16; }
executable=/build/src/EMTGv9
test -x "$executable"
ldd "$executable" >/tmp/emtg.ldd
grep -Fq "libipopt.so" /tmp/emtg.ldd
! grep -iFq "snopt" /tmp/emtg.ldd
! grep -Fq "not found" /tmp/emtg.ldd
check ipopt_backend_compile passed
check ipopt_dynamic_linking resolved
'''
    volume = build_volume_name(toolchain_image, "ipopt")
    return run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="ipopt-backend",
        tmp_path_factory=tmp_path_factory,
        build_volume=volume,
    )


@pytest.fixture(scope="session")
def ipopt_runtime_probe(toolchain_image, repository_root, tmp_path_factory):
    """Build and run only the deterministic IPOPT adapter contract."""
    script = _backend_source_script("IPOPT") + r'''
cmake --build /build --target ipopt_adapter_contract -j2 \
    >/tmp/runtime-build.log 2>&1 \
    || { tail -n 150 /tmp/runtime-build.log; exit 17; }
check ipopt_runtime_compile passed
set +e
ctest --test-dir /build -R '^ipopt_adapter_contract$' -V \
    >/tmp/runtime-test.log 2>&1
runtime_status=$?
set -e
cat /tmp/runtime-test.log
test "$runtime_status" -eq 0 || exit 18
check ipopt_runtime passed
'''
    volume = build_volume_name(toolchain_image, "ipopt")
    return run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="ipopt-runtime",
        tmp_path_factory=tmp_path_factory,
        build_volume=volume,
    )


def _prepare_mission_options(
    source, artifacts, *, mbh, launch_vehicle_key="Atlas_V_401"
):
    options = MissionOptions.MissionOptions(str(source))
    options.NLP_solver_type = 2
    options.background_mode = 1
    options.short_output_file_names = 1
    options.override_working_directory = 1
    options.forced_working_directory = "/artifacts"
    options.override_mission_subfolder = 1
    options.forced_mission_subfolder = "."
    options.universe_folder = "/repo/testatron/universe/"
    options.HardwarePath = (
        "/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/"
        "Config_Files/hardware_models/"
    )
    options.LaunchVehicleLibraryFile = (
        "LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt"
    )
    options.LaunchVehicleKey = launch_vehicle_key
    options.snopt_max_run_time = 30
    if mbh:
        options.mission_name = "CoastPhase_EMintercept_MBH_smoke"
        options.run_inner_loop = 1
        options.MBH_max_trials = 3
        options.MBH_max_run_time = 60
        options.MBH_RNG_seed = 17
        options.seed_MBH = 1
    for journey in options.Journeys:
        gravity_file = Path(
            journey.central_body_gravity_file.replace("\\", "/")
        ).name
        journey.central_body_gravity_file = (
            f"/repo/testatron/universe/gravity_files/{gravity_file}"
        )

    destination = artifacts / f"{options.mission_name}.emtgopt"
    options.write_options_file(str(destination), True)
    return options.mission_name, destination


def _mission_runtime_probe(
    *,
    toolchain_image,
    repository_root,
    tmp_path_factory,
    source,
    probe_name,
    mbh,
    launch_vehicle_key="Atlas_V_401",
):
    artifacts = tmp_path_factory.mktemp(probe_name)
    mission_name, options_path = _prepare_mission_options(
        source,
        artifacts,
        mbh=mbh,
        launch_vehicle_key=launch_vehicle_key,
    )
    timeout_seconds = 300 if mbh else 180
    script = _backend_source_script("IPOPT") + rf'''
cmake --build /build --target EMTGv9 -j2 >/tmp/mission-build.log 2>&1 \
    || {{ tail -n 150 /tmp/mission-build.log; exit 20; }}
check {probe_name}_compile passed
set +e
timeout {timeout_seconds} /build/src/EMTGv9 /artifacts/{options_path.name} \
    >/tmp/mission-runtime.log 2>&1
mission_status=$?
set -e
cat /tmp/mission-runtime.log
test "$mission_status" -eq 0 || exit 21
test -s /artifacts/{mission_name}.emtg || exit 22
check {probe_name}_run passed
'''
    volume = build_volume_name(toolchain_image, "ipopt")
    checks = run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name=probe_name,
        tmp_path_factory=tmp_path_factory,
        build_volume=volume,
        writable_artifacts=artifacts,
    )
    result_path = artifacts / f"{mission_name}.emtg"
    checks["mission"] = Mission.Mission(str(result_path))
    checks["result_path"] = str(result_path)
    return checks


@pytest.fixture(scope="session")
def direct_nlp_mission_probe(toolchain_image, repository_root, tmp_path_factory):
    """Run and parse one deterministic direct-NLP IPOPT mission."""
    source = (
        repository_root
        / "testatron/tests/transcription_tests/CoastPhase_EMintercept.emtgopt"
    )
    return _mission_runtime_probe(
        toolchain_image=toolchain_image,
        repository_root=repository_root,
        tmp_path_factory=tmp_path_factory,
        source=source,
        probe_name="direct-nlp-mission",
        mbh=False,
    )


@pytest.fixture(scope="session")
def track_acs_replay_probe(toolchain_image, repository_root, tmp_path_factory):
    """Replay the committed TrackACSProp solution without optimization."""
    artifacts = artifact_directory(tmp_path_factory)
    source = (
        repository_root
        / "testatron/tests/spacecraft_options/"
        "spacecraftoptions_Chem_TrackACSProp.emtgopt"
    )
    baseline_path = source.with_suffix(".emtg")
    options_path = ipopt_characterization.prepare_replay(
        source,
        baseline_path,
        artifacts,
        execution_repository_root="/repo",
        execution_directory="/artifacts",
    )
    script = _backend_source_script("IPOPT") + rf'''
cmake --build /build --target EMTGv9 -j2 >/tmp/track-acs-replay-build.log 2>&1 \
    || {{ tail -n 150 /tmp/track-acs-replay-build.log; exit 25; }}
check track_acs_replay_compile passed
set +e
timeout 60 /build/src/EMTGv9 /artifacts/{options_path.name} \
    >/artifacts/run.log 2>&1
replay_status=$?
set -e
cat /artifacts/run.log
test "$replay_status" -eq 0 || exit 26
test -s /artifacts/spacecraftoptions_Chem_TrackACSProp.emtg || exit 27
check track_acs_replay_run passed
'''
    checks = run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="track-acs-replay",
        tmp_path_factory=tmp_path_factory,
        build_volume=build_volume_name(toolchain_image, "ipopt"),
        writable_artifacts=artifacts,
    )
    generated_path = artifacts / "spacecraftoptions_Chem_TrackACSProp.emtg"
    baseline = Mission.Mission(str(baseline_path))
    generated = Mission.Mission(str(generated_path))
    comparison = ipopt_characterization.compare_replay(baseline, generated)
    comparison["feasibility_tolerance"] = 1.0e-5
    comparison["feasible"] = (
        comparison["generated_feasibility_metric"]
        <= comparison["feasibility_tolerance"]
    )
    (artifacts / "comparison.json").write_text(
        json.dumps(comparison, indent=2) + "\n"
    )
    result = {
        "status": "unreviewed",
        "stage": "replay",
        "acceptable": comparison["acceptable"] and comparison["feasible"],
        "source_options": str(source),
        "baseline_mission": str(baseline_path),
        "prepared_options": str(options_path),
        "generated_mission": str(generated_path),
        "comparison": str(artifacts / "comparison.json"),
        "log": str(artifacts / "run.log"),
    }
    (artifacts / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    checks["comparison"] = comparison
    checks["result"] = result
    return checks


@pytest.fixture(scope="session")
def mgandsms_acs_derivative_probe(
    toolchain_image, repository_root, tmp_path_factory
):
    """Check derivatives for MGAnDSMs with ACS propellant tracking enabled."""
    artifacts = tmp_path_factory.mktemp("mgandsms-acs-derivatives")
    source = (
        repository_root
        / "testatron/tests/spacecraft_options/"
        "spacecraftoptions_Chem_TrackACSProp.emtgopt"
    )
    options = MissionOptions.MissionOptions(str(source))
    journey = options.Journeys[0]
    trial_descriptions = {entry[0] for entry in journey.trialX}
    assert options.mission_type == 6
    assert options.trackACS == 1
    assert options.LaunchVehicleKey == "Atlas_V_411"
    assert journey.phase_type == 6
    assert journey.initial_impulse_bounds[0] < journey.initial_impulse_bounds[1]
    assert any(
        "EphemerisPeggedLaunchDirectInsertion: magnitude of outgoing velocity asymptote"
        in description
        for description in trial_descriptions
    )
    assert any(
        "MGAnDSMs: virtual chemical fuel" in description
        for description in trial_descriptions
    )
    options.mission_name = "spacecraftoptions_Chem_TrackACSProp_derivatives"
    options.NLP_solver_type = 2
    options.run_inner_loop = 3
    options.quiet_NLP = 0
    options.check_derivatives = 1
    options.background_mode = 1
    options.short_output_file_names = 1
    options.override_working_directory = 1
    options.forced_working_directory = "/artifacts"
    options.override_mission_subfolder = 1
    options.forced_mission_subfolder = "."
    options.universe_folder = "/repo/testatron/universe/"
    options.HardwarePath = (
        "/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/"
        "Config_Files/hardware_models/"
    )
    options.LaunchVehicleLibraryFile = (
        "LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt"
    )
    options.LaunchVehicleKey = "Atlas_V_411"
    for journey in options.Journeys:
        gravity_file = Path(
            journey.central_body_gravity_file.replace("\\", "/")
        ).name
        journey.central_body_gravity_file = (
            f"/repo/testatron/universe/gravity_files/{gravity_file}"
        )

    options_path = artifacts / f"{options.mission_name}.emtgopt"
    options.write_options_file(str(options_path), True)
    (artifacts / "ipopt.opt").write_text("max_iter 0\n", encoding="ascii")

    script = _backend_source_script("IPOPT") + rf'''
cmake --build /build --target EMTGv9 -j2 >/tmp/derivative-build.log 2>&1 \
    || {{ tail -n 150 /tmp/derivative-build.log; exit 23; }}
check mgandsms_acs_derivative_compile passed
cd /artifacts
set +e
timeout 30 /build/src/EMTGv9 /artifacts/{options_path.name} \
    >/tmp/derivative-runtime.log 2>&1
derivative_status=$?
set -e
cat /tmp/derivative-runtime.log
test "$derivative_status" -eq 0 || exit 24
grep -Fq "Starting derivative checker for first derivatives." \
    /tmp/derivative-runtime.log
grep -Fq "No errors detected by derivative checker." \
    /tmp/derivative-runtime.log
! grep -Eq '^\* (grad_f|jac_g)' /tmp/derivative-runtime.log
grep -Fq "j0p0MGAnDSMs: match point virtual chemical fuel" \
    /artifacts/*XFfile.csv
check mgandsms_acs_derivative_run passed
'''
    volume = build_volume_name(toolchain_image, "ipopt")
    return run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="mgandsms-acs-derivatives",
        tmp_path_factory=tmp_path_factory,
        build_volume=volume,
        writable_artifacts=artifacts,
    )


@pytest.fixture(scope="session")
def track_acs_chaperone_mission_probe(
    toolchain_image, repository_root, tmp_path_factory
):
    """Run TrackACSProp and parse the chaperoned IPOPT result."""
    source = (
        repository_root
        / "testatron/tests/spacecraft_options/"
        "spacecraftoptions_Chem_TrackACSProp.emtgopt"
    )
    return _mission_runtime_probe(
        toolchain_image=toolchain_image,
        repository_root=repository_root,
        tmp_path_factory=tmp_path_factory,
        source=source,
        probe_name="track-acs-chaperone-mission",
        mbh=False,
        launch_vehicle_key="Atlas_V_411",
    )


@pytest.fixture(scope="session")
def fixed_seed_mbh_mission_probe(
    toolchain_image, repository_root, tmp_path_factory
):
    """Run and parse the bounded fixed-seed MBH IPOPT mission twice."""
    source = (
        repository_root
        / "testatron/tests/transcription_tests/CoastPhase_EMintercept.emtgopt"
    )
    return tuple(
        _mission_runtime_probe(
            toolchain_image=toolchain_image,
            repository_root=repository_root,
            tmp_path_factory=tmp_path_factory,
            source=source,
            probe_name=f"fixed-seed-mbh-mission-{run_number}",
            mbh=True,
        )
        for run_number in (1, 2)
    )