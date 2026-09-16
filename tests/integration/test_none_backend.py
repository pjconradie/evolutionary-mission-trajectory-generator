"""Verify solver-neutral build and native contracts."""

import pytest


pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
    pytest.mark.none_backend,
    pytest.mark.compile,
]


def test_none_backend_configures_and_compiles_without_snopt(none_backend_probe):
    assert none_backend_probe["none_backend_configure"] == "passed"
    assert none_backend_probe["none_backend_compile"] == "passed"


def test_native_nlp_contracts_pass(none_backend_probe):
    assert none_backend_probe["nlp_contract"] == "passed"