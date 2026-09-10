"""Fixtures for disposable Linux toolchain integration tests."""

import shutil
import subprocess
import uuid

import pytest


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

cmake --build /tmp/emtg-none-build --target nlp_solver_contract -j2 \
    >/tmp/nlp-contract-build.log 2>&1
ctest --test-dir /tmp/emtg-none-build --output-on-failure \
    >/tmp/nlp-contract-test.log 2>&1
check nlp_contract passed

set +e
cmake -S /tmp/emtg-none -B /tmp/emtg-invalid-build \
    -DEMTG_NLP_SOLVER=INVALID >/tmp/emtg-invalid.log 2>&1
invalid_status=$?
cmake -S /tmp/emtg-none -B /tmp/emtg-ipopt-build \
    -DEMTG_NLP_SOLVER=IPOPT >/tmp/emtg-ipopt.log 2>&1
ipopt_status=$?
set -e
test "$invalid_status" -ne 0
grep -Fq "Unsupported EMTG_NLP_SOLVER 'INVALID'" /tmp/emtg-invalid.log
test "$ipopt_status" -ne 0
grep -Fq "IPOPT adapter is not implemented" /tmp/emtg-ipopt.log
check cmake_solver_rejections passed

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
cmake -S /tmp/cmake-source -B /tmp/cmake-build >/tmp/cmake.log 2>&1
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