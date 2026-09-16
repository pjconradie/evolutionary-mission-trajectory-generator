"""Characterize PyEMTG parsing across Testatron and OSIRIS result files."""

from pathlib import Path

import pytest

from Mission import Mission

pytestmark = pytest.mark.regression

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TESTATRON_TESTS_ROOT = REPOSITORY_ROOT / "testatron" / "tests"
OSIRIS_RESULTS_ROOT = (
    REPOSITORY_ROOT
    / "docs"
    / "0_Users"
    / "tutorial"
    / "Tutorial_EMTG_Files"
    / "OSIRIS-REx"
    / "results"
)
OSIRIS_BASELINES = {
    "2022": (
        OSIRIS_RESULTS_ROOT
        / "OSIRIS-REx_11272022_144557"
        / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    ),
    "2024": (
        OSIRIS_RESULTS_ROOT
        / "OSIRIS-REx_412024_11530"
        / "OSIRIS-REx_Sun(EEB)_Sun(BE).emtg"
    ),
}

TRUTH_FILES = sorted(TESTATRON_TESTS_ROOT.glob("**/*.emtg"))
TRUTH_IDS = [str(path.relative_to(TESTATRON_TESTS_ROOT)) for path in TRUTH_FILES]

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


def assert_complete_mission_parse(mission, source: Path):
    """Require the minimum structure that distinguishes a useful result parse."""
    relative_source = source.relative_to(REPOSITORY_ROOT)
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


@pytest.mark.parametrize("truth_file", TRUTH_FILES, ids=TRUTH_IDS)
def test_each_testatron_truth_is_parseable(truth_file):
    """Every committed Testatron result must produce a named mission with journeys."""
    assert_complete_mission_parse(Mission(str(truth_file)), truth_file)


@pytest.mark.parametrize("vintage", ["2022", "2024"])
def test_osiris_baseline_preserves_frozen_metrics_and_topology(vintage):
    """Each mandatory OSIRIS result must retain its topology and reference metrics."""
    baseline = OSIRIS_BASELINES[vintage]
    expected = OSIRIS_EXPECTATIONS[vintage]
    mission = Mission(str(baseline))

    assert_complete_mission_parse(mission, baseline)
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
