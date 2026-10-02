"""Characterize PyEMTG parsing across Testatron and OSIRIS result files."""

from pathlib import Path

import pytest

from Mission import Mission

pytestmark = pytest.mark.regression

OSIRIS_EXPECTATIONS = {
    "2022": {
        "total_deterministic_deltav": 12.39626561567154894306,
        "total_flight_time_years": 4.03330016605067598334,
        "journey_flight_times": [457.83732226, 284.82555470],
        "final_mass_including_propellant_margin": 5.73351819481526181477,
        "worst_violation": 0.00000049086793289867,
    },
    "2024": {
        "total_deterministic_deltav": 7.12363247375914987458,
        "total_flight_time_years": 6.73501897861011755708,
        "journey_flight_times": [1179.32045074, 550.14523120],
        "final_mass_including_propellant_margin": 59.38915568108948406234,
        "worst_violation": 0.00000877916857574499,
    },
}


def osiris_baselines(repository_root: Path) -> dict[str, Path]:
    """Return the immutable OSIRIS result files from the repository root."""
    osiris_results_root = (
        repository_root
        / "docs"
        / "0_Users"
        / "tutorial"
        / "Tutorial_EMTG_Files"
        / "OSIRIS-REx"
        / "results"
    )
    return {
        "2022": (
            osiris_results_root
            / "OSIRIS-REx_11272022_144557"
            / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
        ),
        "2024": (
            osiris_results_root
            / "OSIRIS-REx_412024_11530"
            / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
        ),
    }


def pytest_generate_tests(metafunc):
    """Generate an independently reported parse test for each immutable truth."""
    if "truth_file" not in metafunc.fixturenames:
        return

    testatron_tests_root = metafunc.config.rootpath / "testatron" / "tests"
    truth_files = sorted(testatron_tests_root.glob("**/*.emtg"))
    truth_ids = [str(path.relative_to(testatron_tests_root)) for path in truth_files]
    metafunc.parametrize("truth_file", truth_files, ids=truth_ids)


def assert_complete_mission_parse(mission, source: Path, repository_root: Path):
    """Require the minimum structure that distinguishes a useful result parse."""
    relative_source = source.relative_to(repository_root)
    assert mission.success == 1, f"Mission parser could not open {relative_source}"
    assert mission.mission_name != "bob", (
        f"Mission parser retained its sentinel name for {relative_source}"
    )
    assert mission.Journeys, f"Mission parser found no journeys in {relative_source}"


def test_testatron_truth_inventory_contains_137_results(testatron_truth_files):
    """The frozen regression corpus must retain all 137 committed result files."""
    assert len(testatron_truth_files) == 137, (
        "Testatron truth inventory changed; update the characterization baseline only "
        "after reviewing added or removed cases"
    )


def test_each_testatron_truth_is_parseable(truth_file, repository_root):
    """Every committed Testatron result must produce a named mission with journeys."""
    assert_complete_mission_parse(Mission(str(truth_file)), truth_file, repository_root)


@pytest.mark.parametrize("vintage", ["2022", "2024"])
def test_osiris_baseline_preserves_frozen_metrics_and_topology(vintage, repository_root):
    """Each mandatory OSIRIS result must retain its topology and reference metrics."""
    baseline = osiris_baselines(repository_root)[vintage]
    expected = OSIRIS_EXPECTATIONS[vintage]
    mission = Mission(str(baseline))

    assert_complete_mission_parse(mission, baseline, repository_root)
    assert mission.mission_name.strip() == "OSIRIS-REx", (
        f"{vintage} baseline mission name changed"
    )
    assert [journey.journey_name for journey in mission.Journeys] == [
        "Earth_to_Bennu",
        "Bennu_to_Earth",
    ], f"{vintage} baseline journey topology changed"

    assert mission.total_deterministic_deltav == pytest.approx(
        expected["total_deterministic_deltav"]
    )
    assert mission.total_flight_time_years == pytest.approx(
        expected["total_flight_time_years"]
    )
    assert [journey.journey_flight_time_days for journey in mission.Journeys] == (
        pytest.approx(expected["journey_flight_times"])
    )
    assert mission.final_mass_including_propellant_margin == pytest.approx(
        expected["final_mass_including_propellant_margin"]
    )
    assert mission.worst_violation == pytest.approx(expected["worst_violation"])
