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
    assert mission.mission_name.strip() == "CoastPhase_EMintercept"
    assert mission.number_of_solution_attempts == 1
    assert mission.first_nlp_solve_feasible == 1
    assert math.isfinite(mission.worst_violation)
    assert abs(mission.worst_violation) <= 1.0e-5


@pytest.mark.solver_runtime
def test_mgandsms_acs_derivatives(mgandsms_acs_derivative_probe):
    assert mgandsms_acs_derivative_probe[
        "mgandsms_acs_derivative_compile"
    ] == "passed"
    assert mgandsms_acs_derivative_probe[
        "mgandsms_acs_derivative_run"
    ] == "passed"


@pytest.mark.solver_runtime
def test_ipopt_runs_bounded_fixed_seed_mbh_mission(fixed_seed_mbh_mission_probe):
    missions = []
    for run_number, probe in enumerate(fixed_seed_mbh_mission_probe, start=1):
        prefix = f"fixed-seed-mbh-mission-{run_number}"
        assert probe[f"{prefix}_compile"] == "passed"
        assert probe[f"{prefix}_run"] == "passed"
        mission = probe["mission"]
        assert mission.mission_name.strip() == "CoastPhase_EMintercept_MBH_smoke"
        assert 1 <= mission.number_of_solution_attempts <= 3
        assert mission.first_nlp_solve_feasible == 1
        assert mission.solution_attempt_index_that_produced_best_feasible_solution >= 1
        assert math.isfinite(mission.worst_violation)
        assert abs(mission.worst_violation) <= 1.0e-5
        missions.append(mission)

    first, second = missions
    assert second.number_of_solution_attempts == first.number_of_solution_attempts
    assert (
        second.solution_attempt_index_that_produced_best_feasible_solution
        == first.solution_attempt_index_that_produced_best_feasible_solution
    )
    assert second.objective_value == pytest.approx(first.objective_value, abs=1.0e-12)
    assert second.worst_violation == pytest.approx(first.worst_violation, abs=1.0e-12)