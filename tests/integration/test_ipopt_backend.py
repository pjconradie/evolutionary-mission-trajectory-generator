"""Verify the focused IPOPT build and dynamic-link boundary."""

import math

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


@pytest.mark.solver_runtime
def test_ipopt_runs_direct_nlp_mission(direct_nlp_mission_probe):
    assert direct_nlp_mission_probe["direct-nlp-mission_compile"] == "passed"
    assert direct_nlp_mission_probe["direct-nlp-mission_run"] == "passed"
    mission = direct_nlp_mission_probe["mission"]
    assert mission.mission_name == "CoastPhase_EMintercept"
    assert mission.number_of_solution_attempts == 1
    assert mission.first_nlp_solve_feasible == 1
    assert math.isfinite(mission.worst_violation)
    assert abs(mission.worst_violation) <= 1.0e-5


@pytest.mark.solver_runtime
def test_ipopt_runs_bounded_fixed_seed_mbh_mission(fixed_seed_mbh_mission_probe):
    assert fixed_seed_mbh_mission_probe["fixed-seed-mbh-mission_compile"] == "passed"
    assert fixed_seed_mbh_mission_probe["fixed-seed-mbh-mission_run"] == "passed"
    mission = fixed_seed_mbh_mission_probe["mission"]
    assert mission.mission_name == "CoastPhase_EMintercept_MBH_smoke"
    assert 1 <= mission.number_of_solution_attempts <= 3
    assert mission.first_nlp_solve_feasible == 1
    assert mission.solution_attempt_index_that_produced_best_feasible_solution >= 1
    assert math.isfinite(mission.worst_violation)
    assert abs(mission.worst_violation) <= 1.0e-5