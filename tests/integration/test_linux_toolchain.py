"""Verify the open-source Linux toolchain in a disposable Docker container."""

import hashlib

import pytest


pytestmark = pytest.mark.integration

CSPICE_ARCHIVE = "depend/cspice-c_pc_linux_gcc_64bit/cspice.tar.Z"
CSPICE_SHA256 = "60a95b51a6472f1afe7e40d77ebdee43c12bb5b8823676ccc74692ddfede06ce"


def test_cspice_archive_has_pinned_checksum(repository_root):
    """The committed Linux CSPICE input must retain its verified payload."""
    digest = hashlib.sha256()
    with (repository_root / CSPICE_ARCHIVE).open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest.update(chunk)

    assert digest.hexdigest() == CSPICE_SHA256


def test_target_container_platform_and_runtime(phase1_toolchain_probe):
    """The pinned image must provide Debian 12 and Python 3.12 on amd64."""
    assert phase1_toolchain_probe["architecture"] == "x86_64"
    assert phase1_toolchain_probe["debian_version"] == "12"
    assert phase1_toolchain_probe["python_version"].startswith("3.12.")


def test_debian_toolchain_and_ipopt_are_discoverable(phase1_toolchain_probe):
    """The intended compiler, build tools, GSL, and IPOPT must be installed."""
    assert phase1_toolchain_probe["packages"] == "installed"
    assert phase1_toolchain_probe["compiler_version"].startswith("12.2.")
    assert phase1_toolchain_probe["cmake_version"].startswith("3.25.")
    assert phase1_toolchain_probe["pkg_config_version"] == "1.8.1"
    assert phase1_toolchain_probe["gsl_version"] == "2.7.1"
    assert phase1_toolchain_probe["ipopt_version"] == "3.11.9"


def test_cspice_payload_rebuilds_as_expected(phase1_toolchain_probe):
    """The pinned N0067 archive must validate and rebuild a nonempty static library."""
    assert phase1_toolchain_probe["cspice_checksum"] == CSPICE_SHA256
    assert phase1_toolchain_probe["cspice_payload"] == "valid"
    assert int(phase1_toolchain_probe["cspice_objects"]) == 2229


def test_combined_dependencies_compile_link_and_run(phase1_toolchain_probe):
    """Boost, GSL, CSPICE, and IPOPT must work together without missing libraries."""
    assert phase1_toolchain_probe["dependency_compile"] == "passed"
    assert phase1_toolchain_probe["dynamic_linking"] == "resolved"
    assert phase1_toolchain_probe["dependency_runtime"] == "passed"


def test_unchanged_cmake_reaches_snopt_gate_first(phase1_toolchain_probe):
    """Current CMake must fail at missing SNOPT before dependency discovery."""
    assert phase1_toolchain_probe["cmake_snopt_gate"] == "passed"


def test_none_backend_configures_and_compiles_without_snopt(phase1_toolchain_probe):
    """The complete EMTG library must compile without proprietary solver sources."""
    assert phase1_toolchain_probe["none_backend_configure"] == "passed"
    assert phase1_toolchain_probe["none_backend_compile"] == "passed"


def test_native_nlp_contract_passes_in_target_environment(phase1_toolchain_probe):
    """Solver-neutral native contracts must pass on Debian 12 amd64."""
    assert phase1_toolchain_probe["nlp_contract"] == "passed"


def test_cmake_rejects_invalid_and_unimplemented_solvers(phase1_toolchain_probe):
    """CMake must reject unknown backends and IPOPT before its adapter exists."""
    assert phase1_toolchain_probe["cmake_solver_rejections"] == "passed"