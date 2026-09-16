"""Verify the open-source Linux toolchain in a disposable Docker container."""

import hashlib

import pytest


pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
    pytest.mark.toolchain,
]

CSPICE_ARCHIVE = "depend/cspice-c_pc_linux_gcc_64bit/cspice.tar.Z"
CSPICE_SHA256 = "60a95b51a6472f1afe7e40d77ebdee43c12bb5b8823676ccc74692ddfede06ce"


def test_cspice_archive_has_pinned_checksum(repository_root):
    """The committed Linux CSPICE input must retain its verified payload."""
    digest = hashlib.sha256()
    with (repository_root / CSPICE_ARCHIVE).open("rb") as archive:
        for chunk in iter(lambda: archive.read(1024 * 1024), b""):
            digest.update(chunk)

    assert digest.hexdigest() == CSPICE_SHA256


def test_target_container_platform_and_runtime(platform_probe):
    """The pinned image must provide Debian 12 and Python 3.12 on amd64."""
    assert platform_probe["architecture"] == "x86_64"
    assert platform_probe["debian_version"] == "12"
    assert platform_probe["python_version"].startswith("3.12.")


def test_debian_toolchain_and_ipopt_are_discoverable(platform_probe):
    """The intended compiler, build tools, GSL, and IPOPT must be installed."""
    assert platform_probe["packages"] == "installed"
    assert platform_probe["compiler_version"].startswith("12.2.")
    assert platform_probe["cmake_version"].startswith("3.25.")
    assert platform_probe["pkg_config_version"] == "1.8.1"
    assert platform_probe["gsl_version"] == "2.7.1"
    assert platform_probe["ipopt_version"] == "3.11.9"


def test_cspice_payload_rebuilds_as_expected(platform_probe):
    """The pinned N0067 archive must validate and rebuild a nonempty static library."""
    assert platform_probe["cspice_checksum"] == CSPICE_SHA256
    assert platform_probe["cspice_payload"] == "valid"
    assert int(platform_probe["cspice_objects"]) == 2229


def test_combined_dependencies_compile_link_and_run(dependency_probe):
    """Boost, GSL, CSPICE, and IPOPT must work together without missing libraries."""
    assert dependency_probe["dependency_compile"] == "passed"
    assert dependency_probe["dynamic_linking"] == "resolved"
    assert dependency_probe["dependency_runtime"] == "passed"


@pytest.mark.clean_bootstrap
def test_toolchain_builds_from_clean_layers(clean_bootstrap_probe):
    """The pinned toolchain must build and validate without reusable layers."""
    assert clean_bootstrap_probe["clean_dependency_compile"] == "passed"
    assert clean_bootstrap_probe["clean_dependency_runtime"] == "passed"
    assert clean_bootstrap_probe["clean_ipopt_configure"] == "passed"
    assert clean_bootstrap_probe["clean_ipopt_build"] == "passed"
    assert clean_bootstrap_probe["clean_ipopt_ctest"] == "passed"
    assert clean_bootstrap_probe["clean_ipopt_dynamic_linking"] == "resolved"
    assert clean_bootstrap_probe["clean_bootstrap"] == "passed"