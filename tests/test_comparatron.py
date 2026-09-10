"""Characterize identity and mismatch behavior of Mission.Comparatron."""

import pytest

from Mission import Mission


pytestmark = pytest.mark.regression


@pytest.mark.parametrize("vintage", ["2022", "2024"])
def test_comparatron_matches_each_osiris_baseline_to_itself(
    vintage, osiris_baselines, tmp_path
):
    """Comparing a parsed solution with the same file must report an exact match."""
    baseline = osiris_baselines[vintage]
    mission = Mission(str(baseline))

    matches, differences = mission.Comparatron(
        str(baseline), csv_file_name=str(tmp_path / f"self-{vintage}.csv")
    )

    assert matches is True, f"{vintage} OSIRIS baseline did not match itself"
    assert differences.empty, (
        f"{vintage} OSIRIS self-comparison unexpectedly reported differences"
    )


@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="Mission.Comparatron uses DataFrame.append, removed in pandas 3",
)
def test_comparatron_reports_differences_between_osiris_baselines(
    osiris_baselines, tmp_path
):
    """Distinct OSIRIS solutions should return a populated mismatch report."""
    mission_2022 = Mission(str(osiris_baselines["2022"]))

    matches, differences = mission_2022.Comparatron(
        str(osiris_baselines["2024"]),
        csv_file_name=str(tmp_path / "cross-2022-vs-2024.csv"),
        full_output=False,
    )

    assert matches is False, "Distinct OSIRIS baselines unexpectedly matched"
    assert not differences.empty, "Cross-comparison returned no mismatch details"
