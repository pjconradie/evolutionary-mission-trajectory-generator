import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


MISSION_ROOT = Path(__file__).resolve().parents[2]
SRC = MISSION_ROOT / "src"


def _read_options_journeys(options_path: Path) -> list[dict[str, str]]:
    journeys: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in options_path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "BEGIN_JOURNEY":
            current = {}
        elif line.strip() == "END_JOURNEY":
            if current is not None:
                journeys.append(current)
            current = None
        elif current is not None and line.strip() and not line.lstrip().startswith("#"):
            key, *values = line.split()
            current[key] = " ".join(values)
    return journeys


def _event_julian_dates(mission_path: Path, event_name: str, location: str) -> list[float]:
    matches = []
    for line in mission_path.read_text(encoding="utf-8").splitlines():
        fields = [field.strip() for field in line.split("|")]
        if len(fields) > 4 and fields[3] == event_name and fields[4] == location:
            matches.append(float(fields[1]))
    return matches


def _chemical_burn_julian_dates_before(
    mission_path: Path, julian_date: float
) -> list[float]:
    lines = mission_path.read_text(encoding="utf-8").splitlines()
    burn_epochs = []
    for line in lines:
        fields = [field.strip() for field in line.split("|")]
        if len(fields) <= 4 or not fields[0].strip().isdigit():
            continue
        if fields[3] == "chem_burn" and float(fields[1]) < julian_date:
            burn_epochs.append(float(fields[1]))
    return burn_epochs


@unittest.skipUnless(
    os.environ.get("RUN_OSIRIS_REX_INTEGRATION") == "1",
    "Set RUN_OSIRIS_REX_INTEGRATION=1 to run the Docker mission pipeline",
)
class PipelineIntegrationTests(unittest.TestCase):
    def test_pipeline_command_completes(self):
        result = subprocess.run(
            [sys.executable, str(SRC / "run_mission.py"), "run"],
            cwd=MISSION_ROOT.parents[1],
            text=True,
            capture_output=True,
            timeout=8 * 60 * 60,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

        self.assertTrue(
            (MISSION_ROOT / "config" / "OSIRIS_REx_Low.emtgopt").is_file()
        )
        self.assertTrue(
            (MISSION_ROOT / "results" / "low" / "OSIRIS_REx_Low.emtg").is_file()
        )

        provenance = json.loads(
            (MISSION_ROOT / "config" / "state_conversion.json").read_text(
                encoding="utf-8"
            )
        )
        targets = provenance["target_event_date_bounds_mjd_tdb"]
        hf_options = MISSION_ROOT / "config" / "high_fidelity" / (
            "OSIRIS_REx_Low_singlePhase_HighFidelity.emtgopt"
        )
        journeys = _read_options_journeys(hf_options)
        self.assertEqual(len(journeys), 4)
        for unconstrained_index in (0, 2):
            self.assertEqual(journeys[unconstrained_index]["timebounded"], "0")
        self.assertEqual(journeys[1]["timebounded"], "2")
        self.assertEqual(
            [float(value) for value in journeys[1]["arrival_date_bounds"].split()],
            targets["earth_periapsis"],
        )
        self.assertEqual(journeys[3]["timebounded"], "2")
        self.assertEqual(
            [float(value) for value in journeys[3]["arrival_date_bounds"].split()],
            targets["bennu_arrival"],
        )
        self.assertIn("p0b0_epoch_abs_", hf_options.read_text(encoding="utf-8"))

        hf_result = MISSION_ROOT / "results" / "high_fidelity" / (
            "OSIRIS_REx_Low_singlePhase_HighFidelity.emtg"
        )
        target_events = (
            ("periapse", "free point", targets["earth_periapsis"]),
            ("rendezvous", "Bennu", targets["bennu_arrival"]),
        )
        for event_name, location, bounds in target_events:
            event_epochs = _event_julian_dates(hf_result, event_name, location)
            self.assertTrue(event_epochs, f"Missing {event_name} event at {location}")
            lower_jd, upper_jd = (float(value) + 2400000.5 for value in bounds)
            self.assertTrue(
                any(lower_jd <= epoch <= upper_jd for epoch in event_epochs),
                f"{event_name} at {location} was outside its UTC target-day bounds",
            )

        earth_periapses = _event_julian_dates(hf_result, "periapse", "free point")
        self.assertTrue(earth_periapses, "Missing Earth periapsis event")
        first_leg_burn_epochs = _chemical_burn_julian_dates_before(
            hf_result, min(earth_periapses)
        )
        self.assertTrue(
            first_leg_burn_epochs,
            "Expected the first outbound DSM before the Earth encounter",
        )
        dsm_lower, dsm_upper = (
            float(value) + 2400000.5
            for value in targets["first_dsm_epoch"]
        )
        self.assertTrue(
            dsm_lower <= first_leg_burn_epochs[0] <= dsm_upper,
            f"First DSM was not on its configured flown-date window: "
            f"{first_leg_burn_epochs[0]}",
        )


if __name__ == "__main__":
    unittest.main()