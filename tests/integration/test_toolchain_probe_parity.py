"""Temporary parity gate for removing the monolithic toolchain probe."""

import pytest


pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
    pytest.mark.toolchain,
    pytest.mark.toolchain_parity,
]

LEGACY_CHECK_KEYS = {
    "architecture",
    "debian_version",
    "python_version",
    "packages",
    "compiler_version",
    "cmake_version",
    "pkg_config_version",
    "gsl_version",
    "ipopt_version",
    "cspice_checksum",
    "cspice_payload",
    "cspice_objects",
    "none_backend_configure",
    "none_backend_compile",
    "nlp_contract",
    "cmake_invalid_solver_rejection",
    "cmake_default_ipopt",
    "cmake_snopt_gate",
    "ipopt_backend_compile",
    "ipopt_dynamic_linking",
    "dependency_compile",
    "dynamic_linking",
    "dependency_runtime",
}


def test_split_probes_preserve_all_legacy_checks(
    phase1_toolchain_probe,
    platform_probe,
    dependency_probe,
    cmake_policy_probe,
    none_backend_probe,
    ipopt_backend_probe,
):
    split_probes = (
        platform_probe,
        dependency_probe,
        cmake_policy_probe,
        none_backend_probe,
        ipopt_backend_probe,
    )
    split_checks = {}
    for probe in split_probes:
        for key, value in probe.items():
            if key in split_checks:
                assert split_checks[key] == value
            split_checks[key] = value

    assert set(phase1_toolchain_probe) == LEGACY_CHECK_KEYS
    assert len(LEGACY_CHECK_KEYS) == 23
    assert {
        key: split_checks[key] for key in LEGACY_CHECK_KEYS
    } == phase1_toolchain_probe