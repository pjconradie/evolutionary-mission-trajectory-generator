"""Verify the focused IPOPT build and dynamic-link boundary."""

import pytest


pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
    pytest.mark.ipopt_backend,
]


@pytest.mark.compile
def test_ipopt_backend_builds_without_snopt(ipopt_backend_probe):
    assert ipopt_backend_probe["cmake_default_ipopt"] == "passed"
    assert ipopt_backend_probe["ipopt_adapter_compile"] == "passed"
    assert ipopt_backend_probe["ipopt_backend_compile"] == "passed"
    assert ipopt_backend_probe["ipopt_dynamic_linking"] == "resolved"


@pytest.mark.solver_runtime
def test_ipopt_adapter_solves_deterministic_problem(ipopt_runtime_probe):
    assert ipopt_runtime_probe["ipopt_runtime_compile"] == "passed"
    assert ipopt_runtime_probe["ipopt_runtime"] == "passed"