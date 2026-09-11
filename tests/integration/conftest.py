"""Fixtures for disposable Linux toolchain integration tests."""

import shutil
import subprocess
import uuid
from pathlib import Path

import pytest
import Mission
import MissionOptions

from _docker_support import (
    build_clean_toolchain_image,
    build_volume_name,
    ensure_toolchain_image,
    remove_toolchain_image,
    run_probe,
)


IMAGE = (
    "python:3.12-slim-bookworm@"
    "sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254"
)
PROBE_TIMEOUT_SECONDS = 3600
CHECK_PREFIX = "EMTG_CHECK "

PROBE_SCRIPT = r'''
set -eu

check() {
    printf "EMTG_CHECK %s=%s\n" "$1" "$2"
}

architecture=$(uname -m)
test "$architecture" = "x86_64"
check architecture "$architecture"

. /etc/os-release
test "$ID" = "debian"
test "$VERSION_ID" = "12"
check debian_version "$VERSION_ID"

python_version=$(python --version | awk '{print $2}')
case "$python_version" in
    3.12.*) ;;
    *) exit 10 ;;
esac
check python_version "$python_version"

apt-get update -qq
if ! DEBIAN_FRONTEND=noninteractive apt-get install -qq -y --no-install-recommends \
    build-essential cmake pkg-config csh gzip tar \
    libboost-filesystem-dev libboost-system-dev libboost-serialization-dev \
    libgsl-dev libblas-dev liblapack-dev coinor-libipopt-dev \
    >/tmp/apt.log 2>&1; then
    tail -n 100 /tmp/apt.log
    exit 11
fi
check packages installed

compiler_version=$(g++ -dumpfullversion)
cmake_version=$(cmake --version | awk 'NR == 1 {print $3}')
pkg_config_version=$(pkg-config --version)
gsl_version=$(pkg-config --modversion gsl)
ipopt_version=$(pkg-config --modversion ipopt)
check compiler_version "$compiler_version"
check cmake_version "$cmake_version"
check pkg_config_version "$pkg_config_version"
check gsl_version "$gsl_version"
check ipopt_version "$ipopt_version"

archive=/repo/depend/cspice-c_pc_linux_gcc_64bit/cspice.tar.Z
archive_checksum=$(sha256sum "$archive" | awk '{print $1}')
test "$archive_checksum" = "60a95b51a6472f1afe7e40d77ebdee43c12bb5b8823676ccc74692ddfede06ce"
check cspice_checksum "$archive_checksum"

mkdir /tmp/spice
cp "$archive" /tmp/spice/
cd /tmp/spice
gzip -d cspice.tar.Z
tar -xf cspice.tar
test -f cspice/makeall.csh
test -f cspice/src/cspice/mkprodct.csh
test -f cspice/include/SpiceUsr.h
test -f cspice/lib/cspice.a
check cspice_payload valid

cd /tmp/spice/cspice
if ! /bin/csh -f makeall.csh >/tmp/cspice-build.log 2>&1; then
    tail -n 100 /tmp/cspice-build.log
    exit 12
fi
test -f lib/cspice.a
cp lib/cspice.a lib/libcspice.a
object_count=$(ar t lib/libcspice.a | wc -l | tr -d ' ')
test "$object_count" -gt 0
check cspice_objects "$object_count"

mkdir -p /tmp/gsl /tmp/emtg-none
cp -a /usr/include/gsl /tmp/gsl/
ln -s /usr/lib/x86_64-linux-gnu/libgsl.a /tmp/gsl/libgsl.a
ln -s /usr/lib/x86_64-linux-gnu/libgslcblas.a /tmp/gsl/libgslcblas.a
ln -s /repo/src /tmp/emtg-none/src
ln -s /repo/tests /tmp/emtg-none/tests
cp /repo/CMakeLists.txt /tmp/emtg-none/CMakeLists.txt
cat >/tmp/emtg-none/EMTG-Config.cmake <<'CMAKE'
set(CSPICE_DIR /tmp/spice/cspice)
set(SNOPT_ROOT_DIR /tmp/emtg-intentionally-missing-snopt)
set(GSL_PATH /tmp/gsl)
set(BOOST_ROOT /usr)
set(Boost_NO_BOOST_CMAKE ON)
CMAKE

cmake -S /tmp/emtg-none -B /tmp/emtg-none-build \
    -DEMTG_NLP_SOLVER=NONE \
    -DBUILD_NLP_CONTRACT_TESTS=ON \
    >/tmp/emtg-none-configure.log 2>&1
! grep -Fq "Now checking on SNOPT" /tmp/emtg-none-configure.log
! grep -Fq "SNOPT directory specified" /tmp/emtg-none-configure.log
check none_backend_configure passed

if ! cmake --build /tmp/emtg-none-build --target emtg -j2 \
    >/tmp/emtg-none-build.log 2>&1; then
    tail -n 150 /tmp/emtg-none-build.log
    exit 13
fi
check none_backend_compile passed

if ! cmake --build /tmp/emtg-none-build --target nlp_solver_contract -j2 \
    >/tmp/nlp-contract-build.log 2>&1; then
    tail -n 150 /tmp/nlp-contract-build.log
    exit 14
fi
ctest --test-dir /tmp/emtg-none-build --output-on-failure \
    >/tmp/nlp-contract-test.log 2>&1
check nlp_contract passed

set +e
cmake -S /tmp/emtg-none -B /tmp/emtg-invalid-build \
    -DEMTG_NLP_SOLVER=INVALID >/tmp/emtg-invalid.log 2>&1
invalid_status=$?
set -e
test "$invalid_status" -ne 0
grep -Fq "Unsupported EMTG_NLP_SOLVER 'INVALID'" /tmp/emtg-invalid.log
check cmake_invalid_solver_rejection passed

cmake -S /tmp/emtg-none -B /tmp/emtg-ipopt-build \
    >/tmp/emtg-ipopt.log 2>&1
grep -Fq "NLP backend: IPOPT" /tmp/emtg-ipopt.log
grep -Fq "IPOPT 3.11.9 found through pkg-config" /tmp/emtg-ipopt.log
! grep -Fq "Now checking on SNOPT" /tmp/emtg-ipopt.log
check cmake_default_ipopt passed

if ! cmake --build /tmp/emtg-ipopt-build --target EMTGv9 -j2 \
    >/tmp/emtg-ipopt-build.log 2>&1; then
    tail -n 150 /tmp/emtg-ipopt-build.log
    exit 15
fi
ipopt_executable=/tmp/emtg-ipopt-build/src/EMTGv9
test -x "$ipopt_executable"
ldd "$ipopt_executable" >/tmp/emtg-ipopt.ldd
grep -Fq "libipopt.so" /tmp/emtg-ipopt.ldd
! grep -iFq "snopt" /tmp/emtg-ipopt.ldd
! grep -Fq "not found" /tmp/emtg-ipopt.ldd
check ipopt_backend_compile passed
check ipopt_dynamic_linking resolved

cat >/tmp/dependency_probe.cpp <<'CPP'
#include <boost/archive/text_oarchive.hpp>
#include <boost/filesystem.hpp>
#include <coin/IpIpoptApplication.hpp>
#include <gsl/gsl_sf_bessel.h>
#include <SpiceUsr.h>

#include <cmath>
#include <sstream>
#include <string>

int main()
{
    const boost::filesystem::path path("/tmp/emtg-dependency-probe");
    boost::filesystem::create_directories(path);
    if (!boost::filesystem::exists(path))
        return 1;

    std::ostringstream stream;
    boost::archive::text_oarchive archive(stream);
    std::string serialized_value = path.string();
    archive << serialized_value;
    boost::filesystem::remove_all(path);

    if (stream.str().empty())
        return 2;
    if (std::abs(gsl_sf_bessel_J0(0.0) - 1.0) > 1.0e-15)
        return 3;

    furnsh_c("/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS_universe/ephemeris_files/naif0012.tls");
    SpiceInt kernel_count = 0;
    ktotal_c("ALL", &kernel_count);
    if (failed_c() || kernel_count != 1)
        return 4;

    SpiceDouble epoch = 0.0;
    str2et_c("2000 JAN 1 12:00:00 TDB", &epoch);
    if (failed_c() || std::abs(epoch) > 1.0e-6)
        return 5;
    kclear_c();

    Ipopt::SmartPtr<Ipopt::IpoptApplication> application =
        IpoptApplicationFactory();
    if (static_cast<int>(application->Initialize()) != 0)
        return 6;

    return 0;
}
CPP

g++ -std=c++17 -Wall -Wextra -Werror \
    /tmp/dependency_probe.cpp \
    -I/tmp/spice/cspice/include \
    /tmp/spice/cspice/lib/libcspice.a \
    -lboost_filesystem -lboost_system -lboost_serialization \
    -lgsl -lgslcblas \
    $(pkg-config --cflags --libs ipopt) \
    -lm -o /tmp/dependency_probe
check dependency_compile passed

ldd /tmp/dependency_probe >/tmp/dependency_probe.ldd
! grep -q "not found" /tmp/dependency_probe.ldd
check dynamic_linking resolved

/tmp/dependency_probe
check dependency_runtime passed

mkdir /tmp/cmake-source
cp /repo/CMakeLists.txt /tmp/cmake-source/CMakeLists.txt
printf '%s\n' \
    'set(SNOPT_ROOT_DIR /tmp/emtg-intentionally-missing-snopt)' \
    >/tmp/cmake-source/EMTG-Config.cmake

set +e
cmake -S /tmp/cmake-source -B /tmp/cmake-build \
    -DEMTG_NLP_SOLVER=SNOPT >/tmp/cmake.log 2>&1
cmake_status=$?
set -e
tr '\n' ' ' </tmp/cmake.log | tr -s ' ' >/tmp/cmake-normalized.log
test "$cmake_status" -ne 0
! grep -Fq "include could not find requested file" /tmp/cmake.log
grep -Fq \
    "SNOPT directory specified (/tmp/emtg-intentionally-missing-snopt) does not exist" \
    /tmp/cmake-normalized.log
! grep -Fq "Now checking for CSpice" /tmp/cmake.log
check cmake_snopt_gate passed
'''


def _docker_is_available():
    if shutil.which("docker") is None:
        return False, "Docker CLI is not installed"

    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, f"Docker daemon check failed: {error}"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return False, f"Docker daemon is unavailable: {detail}"
    return True, ""


@pytest.fixture(scope="session")
def phase1_toolchain_probe(repository_root):
    """Run all expensive Phase 1 checks once in a disposable amd64 container."""
    available, reason = _docker_is_available()
    if not available:
        pytest.skip(reason)

    container_name = f"emtg-phase1-pytest-{uuid.uuid4().hex}"
    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        container_name,
        "--platform",
        "linux/amd64",
        "--mount",
        f"type=bind,src={repository_root},dst=/repo,readonly",
        IMAGE,
        "sh",
        "-c",
        PROBE_SCRIPT,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=PROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        pytest.fail(
            f"Phase 1 Docker probe exceeded {PROBE_TIMEOUT_SECONDS} seconds\n"
            f"stdout:\n{error.stdout or ''}\nstderr:\n{error.stderr or ''}"
        )
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    if result.returncode != 0:
        pytest.fail(
            f"Phase 1 Docker probe exited with {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

    checks = {}
    for line in result.stdout.splitlines():
        if line.startswith(CHECK_PREFIX):
            key, value = line[len(CHECK_PREFIX) :].split("=", 1)
            checks[key] = value

    return checks


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
    """Validate essential outputs from a clean toolchain bootstrap."""
    script = r'''
set -eu
check() { printf "EMTG_CHECK %s=%s\n" "$1" "$2"; }
test "$(uname -m)" = x86_64
test "$(. /etc/os-release; printf '%s' "$VERSION_ID")" = 12
case "$(python --version | awk '{print $2}')" in 3.12.*) ;; *) exit 19 ;; esac
test "$(pkg-config --modversion ipopt)" = 3.11.9
test -f /opt/emtg-deps/cspice/include/SpiceUsr.h
test -f /opt/emtg-deps/cspice/lib/libcspice.a
test "$(ar t /opt/emtg-deps/cspice/lib/libcspice.a | wc -l | tr -d ' ')" = 2229
check clean_bootstrap passed
'''
    return run_probe(
        image=clean_toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="clean-bootstrap",
        tmp_path_factory=tmp_path_factory,
    )


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


def _prepare_mission_options(source, artifacts, *, mbh):
    options = MissionOptions.MissionOptions(str(source))
    options.NLP_solver_type = 2
    options.background_mode = 1
    options.short_output_file_names = 1
    options.override_working_directory = 1
    options.forced_working_directory = "/artifacts"
    options.override_mission_subfolder = 1
    options.forced_mission_subfolder = "."
    options.universe_folder = "/repo/testatron/universe/"
    options.HardwarePath = "/repo/HardwareModels/"
    options.LaunchVehicleLibraryFile = "default.emtg_launchvehicleopt"
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
):
    artifacts = tmp_path_factory.mktemp(probe_name)
    mission_name, options_path = _prepare_mission_options(
        source, artifacts, mbh=mbh
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
def fixed_seed_mbh_mission_probe(
    toolchain_image, repository_root, tmp_path_factory
):
    """Run and parse one bounded fixed-seed MBH IPOPT mission."""
    source = (
        repository_root
        / "testatron/tests/transcription_tests/CoastPhase_EMintercept.emtgopt"
    )
    return _mission_runtime_probe(
        toolchain_image=toolchain_image,
        repository_root=repository_root,
        tmp_path_factory=tmp_path_factory,
        source=source,
        probe_name="fixed-seed-mbh-mission",
        mbh=True,
    )