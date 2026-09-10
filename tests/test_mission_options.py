"""Characterize portable parsing and writing of EMTG mission options."""

import pytest

from MissionOptions import MissionOptions


pytestmark = pytest.mark.regression


def test_osiris_options_round_trip_preserves_execution_settings(
    repository_root, tmp_path
):
    """Writing portable options must preserve mission, solver, MBH, and path data."""
    source = (
        repository_root
        / "docs"
        / "0_Users"
        / "tutorial"
        / "Tutorial_EMTG_Files"
        / "OSIRIS-REx"
        / "OSIRIS-REx.emtgopt"
    )
    original = MissionOptions(str(source))
    output = tmp_path / "OSIRIS-REx-roundtrip.emtgopt"

    original.write_options_file(str(output), writeAll=True)
    roundtrip = MissionOptions(str(output))

    preserved_attributes = (
        "mission_name",
        "NLP_solver_type",
        "seed_MBH",
        "MBH_RNG_seed",
        "MBH_max_trials",
        "MBH_max_run_time",
        "universe_folder",
        "HardwarePath",
        "forced_working_directory",
    )
    for attribute in preserved_attributes:
        assert getattr(roundtrip, attribute) == getattr(original, attribute), (
            f"OSIRIS option {attribute!r} changed during parse/write/reparse"
        )

    journey_names = [journey.journey_name for journey in roundtrip.Journeys]
    assert journey_names == ["Earth_to_Bennu", "Bennu_to_Earth"], (
        "OSIRIS journey order changed during options round-trip"
    )


def test_ipopt_solver_option_round_trips(repository_root, tmp_path):
    """The portable option model must preserve the explicit IPOPT solver value."""
    source = (
        repository_root
        / "docs"
        / "0_Users"
        / "tutorial"
        / "Tutorial_EMTG_Files"
        / "OSIRIS-REx"
        / "OSIRIS-REx.emtgopt"
    )
    options = MissionOptions(str(source))
    options.NLP_solver_type = 2
    output = tmp_path / "OSIRIS-REx-ipopt.emtgopt"

    options.write_options_file(str(output), writeAll=True)
    roundtrip = MissionOptions(str(output))

    assert roundtrip.NLP_solver_type == 2
    assert "#2: IPOPT" in output.read_text()
