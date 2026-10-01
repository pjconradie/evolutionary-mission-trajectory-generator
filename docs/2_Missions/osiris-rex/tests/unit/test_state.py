import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC))

from osiris_rex import (
    BENNU_ARRIVAL_UTC_DATE,
    EARTH_FLYBY_UTC_DATE,
    FIRST_DSM_UTC_DATE,
    build_options,
    first_dsm_epoch_constraint,
    load_initial_state,
    set_arrival_date_window,
    ssb_to_sun_state,
    utc_calendar_day_to_mjd_tdb_bounds,
)


class StateTests(unittest.TestCase):
    def test_ssb_to_sun_subtracts_sun_state(self):
        spacecraft = [10, 20, 30, 1, 2, 3]
        sun = [4, 5, 6, 0.1, 0.2, 0.3]
        self.assertEqual(
            ssb_to_sun_state(0.0, spacecraft, sun),
            [6, 15, 24, 0.9, 1.8, 2.7],
        )

    def test_loads_fixed_initial_state(self):
        et, state = load_initial_state()
        self.assertAlmostEqual(et, 526676400.2)
        self.assertEqual(len(state), 6)
        self.assertAlmostEqual(state[0], 147061808.6)
        self.assertAlmostEqual(state[3], 0.474986)

    def test_rejects_wrong_state_length(self):
        with self.assertRaises(ValueError):
            ssb_to_sun_state(0.0, [1.0], [0.0] * 6)

    def test_mission_epoch_is_inside_tutorial_bennu_window(self):
        et, _ = load_initial_state()
        # The allowed SplineEphem window comes from the OSIRIS tutorial and
        # must include the fixed 2016 initial epoch while excluding year 2000.
        epoch_mjd = 51544.5 + et / 86400.0
        self.assertGreaterEqual(epoch_mjd, 57037.0)
        self.assertLessEqual(epoch_mjd, 60079.0)

    def test_target_dates_are_flight_dates(self):
        self.assertEqual(EARTH_FLYBY_UTC_DATE, "2017-09-22")
        self.assertEqual(BENNU_ARRIVAL_UTC_DATE, "2018-12-03")
        self.assertEqual(FIRST_DSM_UTC_DATE, "2016-12-28")

    def test_utc_calendar_day_converts_to_one_mjd_day(self):
        fake_spice = SimpleNamespace()
        fake_spice.kclear = lambda: None
        fake_spice.furnsh = lambda _path: None
        fake_spice.str2et = lambda value: (
            0.0 if value.startswith("2017 SEP 22") else 86400.0
        )
        fake_spice.unitim = lambda et, _source, _target: 2451545.0 + et / 86400.0

        with tempfile.TemporaryDirectory() as temporary_directory:
            kernels = Path(temporary_directory)
            (kernels / "naif0012.tls").touch()
            (kernels / "de430.bsp").touch()
            with patch("osiris_rex.importlib.import_module", return_value=fake_spice):
                lower, upper = utc_calendar_day_to_mjd_tdb_bounds(
                    "2017-09-22", kernels
                )

        self.assertAlmostEqual(lower, 51544.5)
        self.assertAlmostEqual(upper - lower, 1.0 - 1.0 / 86400.0)

    def test_arrival_window_is_journey_specific_and_validated(self):
        journey = SimpleNamespace()
        set_arrival_date_window(journey, [58000.0, 58001.0])
        self.assertEqual(journey.timebounded, 2)
        self.assertEqual(journey.arrival_date_bounds, [58000.0, 58001.0])
        with self.assertRaises(ValueError):
            set_arrival_date_window(journey, [58001.0, 58000.0])

    def test_first_dsm_is_constrained_to_flown_day(self):
        self.assertEqual(
            first_dsm_epoch_constraint([57754.0, 57755.0]),
            "p0b0_epoch_abs_57754_57755",
        )

    def test_generated_low_options_bound_bennu_and_first_dsm(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "mission.emtgopt"
            build_options(
                [1.4e8, -3.0e7, -1.3e7, 0.5, 27.0, 11.0],
                57640.291668981314,
                [58452.0, 58453.0],
                [57754.0, 57755.0],
                output,
            )
            options_text = output.read_text(encoding="utf-8")

        self.assertIn("arrival_date_bounds 58452.0 58453.0", options_text)
        self.assertIn("p0b0_epoch_abs_57754_57755", options_text)


if __name__ == "__main__":
    unittest.main()