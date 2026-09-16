"""Verify CMake solver-selection policy in the target toolchain."""

import pytest


pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
    pytest.mark.toolchain,
]


def test_cmake_rejects_invalid_solver(cmake_policy_probe):
    assert cmake_policy_probe["cmake_invalid_solver_rejection"] == "passed"


def test_cmake_defaults_to_discovered_ipopt(cmake_policy_probe):
    assert cmake_policy_probe["cmake_default_ipopt"] == "passed"


def test_explicit_snopt_reaches_snopt_gate_first(cmake_policy_probe):
    assert cmake_policy_probe["cmake_snopt_gate"] == "passed"