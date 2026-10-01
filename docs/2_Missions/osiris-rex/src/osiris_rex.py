from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[4]
MISSION_ROOT = REPO_ROOT / "docs" / "2_Missions" / "osiris-rex"
INITIAL_STATE = MISSION_ROOT / "initial_state.yaml"
UNIVERSE_DIR = MISSION_ROOT / "universe"
CONFIG_DIR = MISSION_ROOT / "config"
RESULTS_DIR = MISSION_ROOT / "results"

# EMTG universe-list indices, not SPICE IDs.
EARTH_INDEX = 3
BENNU_INDEX = 11
EARTH_FLYBY_UTC_DATE = "2017-09-22"
BENNU_ARRIVAL_UTC_DATE = "2018-12-03"
FIRST_DSM_UTC_DATE = "2016-12-28"
TARGET_DATE_SOURCE = "https://science.nasa.gov/mission/osiris-rex/in-depth/"


def load_initial_state(path: Path = INITIAL_STATE) -> tuple[float, list[float]]:
    """Load ET and the fixed SSB-to-spacecraft J2000 state from YAML."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    initial = data["mission_state"]["initial_conditions"]

    et = float(initial["et_timestamp"])
    position = [float(value) for value in initial["position"]]
    velocity = [float(value) for value in initial["velocity"]]

    if len(position) != 3 or len(velocity) != 3:
        raise ValueError("Initial position and velocity must each have 3 values")
    if not math.isfinite(et) or not all(
        math.isfinite(value) for value in position + velocity
    ):
        raise ValueError("Initial state contains a non-finite value")

    metadata = initial.get("metadata", {})
    origin = metadata.get("origin", "SSB")
    frame = metadata.get("frame", "J2000")
    position_units = metadata.get("position_units", "km")
    velocity_units = metadata.get("velocity_units", "km/s")

    if (origin, frame, position_units, velocity_units) != (
        "SSB", "J2000", "km", "km/s"
    ):
        raise ValueError(
            "Expected SSB/J2000 state in km and km/s; "
            f"got {origin}/{frame}, {position_units}, {velocity_units}"
        )

    return et, position + velocity


def ssb_to_sun_state(
    et: float,
    spacecraft_ssb_state: list[float],
    sun_ssb_state: list[float],
) -> list[float]:
    """Convert an SSB Cartesian state to Sun-relative Cartesian coordinates."""
    if len(spacecraft_ssb_state) != 6 or len(sun_ssb_state) != 6:
        raise ValueError("Both input states must contain 6 values")
    return [sc - sun for sc, sun in zip(spacecraft_ssb_state, sun_ssb_state)]


def transform_state_with_spice(
    et: float,
    spacecraft_ssb_state: list[float],
    kernel_dir: Path = UNIVERSE_DIR / "ephemeris_files",
) -> tuple[list[float], float]:
    """Load kernels, subtract the Sun's SSB state, and return MJD(TDB)."""
    try:
        spice = importlib.import_module("spiceypy")
    except ImportError as exc:
        raise RuntimeError(
            "spiceypy is required in the host Python environment"
        ) from exc

    kernels = sorted(
        path for path in kernel_dir.iterdir()
        if path.suffix.lower() in {".tls", ".tpc", ".bsp", ".bpc", ".tf"}
    ) if kernel_dir.is_dir() else []

    if not any(path.suffix.lower() == ".bsp" for path in kernels):
        raise FileNotFoundError(
            f"No SPK (.bsp) kernel found in {kernel_dir}. "
            "Obtain kernels with coverage for the mission epoch and bodies."
        )

    spice.kclear()
    try:
        for kernel in kernels:
            spice.furnsh(str(kernel))

        sun_state, _ = spice.spkezr(
            "SUN", et, "J2000", "NONE", "SOLAR SYSTEM BARYCENTER"
        )
        sun_ssb_state = [float(value) for value in sun_state]
        sun_relative_state = ssb_to_sun_state(
            et, spacecraft_ssb_state, sun_ssb_state
        )

        # EMTG's departure_elements_reference_epoch is MJD.
        jed = float(spice.unitim(et, "ET", "JED"))
        mjd_tdb = jed - 2400000.5
        return sun_relative_state, mjd_tdb
    finally:
        spice.kclear()


def utc_calendar_day_to_mjd_tdb_bounds(
    utc_day: str,
    kernel_dir: Path = UNIVERSE_DIR / "ephemeris_files",
) -> list[float]:
    """Return MJD(TDB) bounds for one UTC calendar day using the staged LSK.

    The interval is one UTC calendar day. EMTG treats numerical arrival bounds
    as inclusive, so move the converted next-midnight endpoint inward by one
    second to keep a boundary solution on the requested UTC date.
    """
    day = date.fromisoformat(utc_day)
    next_day = day + timedelta(days=1)
    try:
        spice = importlib.import_module("spiceypy")
    except ImportError as exc:
        raise RuntimeError(
            "spiceypy is required to convert target UTC dates to MJD(TDB)"
        ) from exc

    kernels = sorted(
        path for path in kernel_dir.iterdir()
        if path.suffix.lower() in {".tls", ".tpc", ".bsp", ".bpc", ".tf"}
    ) if kernel_dir.is_dir() else []
    if not any(path.suffix.lower() == ".tls" for path in kernels):
        raise FileNotFoundError(f"No leap-seconds (.tls) kernel found in {kernel_dir}")

    spice.kclear()
    try:
        for kernel in kernels:
            spice.furnsh(str(kernel))

        et_bounds = [
            # CSPICE rejects ISO strings with a trailing textual "UTC" after
            # the T delimiter. Use its unambiguous calendar form instead.
            float(spice.str2et(boundary.strftime("%Y %b %d 00:00:00 UTC").upper()))
            for boundary in (day, next_day)
        ]
        mjd_bounds = [
            float(spice.unitim(et, "ET", "JED")) - 2400000.5
            for et in et_bounds
        ]
        mjd_bounds[1] -= 1.0 / 86400.0
        return mjd_bounds
    finally:
        spice.kclear()


def set_arrival_date_window(journey: Any, bounds: list[float]) -> None:
    """Apply EMTG's bounded-arrival-date mode to one JourneyOptions object."""
    if len(bounds) != 2 or not all(math.isfinite(float(value)) for value in bounds):
        raise ValueError("Arrival date bounds must contain two finite MJD values")
    if bounds[0] >= bounds[1]:
        raise ValueError("Arrival date lower bound must precede its upper bound")
    journey.timebounded = 2
    journey.arrival_date_bounds = [float(value) for value in bounds]


def first_dsm_epoch_constraint(bounds: list[float]) -> str:
    """Constrain phase-zero's first DSM to its flown UTC calendar day."""
    if len(bounds) != 2 or not all(math.isfinite(float(value)) for value in bounds):
        raise ValueError("DSM epoch bounds must contain two finite MJD values")
    if bounds[0] >= bounds[1]:
        raise ValueError("DSM epoch lower bound must precede its upper bound")
    return f"p0b0_epoch_abs_{float(bounds[0]):.12g}_{float(bounds[1]):.12g}"


def build_options(
    sun_state: list[float],
    epoch_mjd: float,
    bennu_arrival_bounds: list[float],
    first_dsm_epoch_bounds: list[float],
    output_path: Path,
) -> None:
    """Write fixed free-point, Earth-flyby, Bennu-rendezvous MGAnDSMs options."""
    if len(sun_state) != 6:
        raise ValueError("Sun-relative state must contain 6 values")

    pyemtg = REPO_ROOT / "PyEMTG"
    sys.path.insert(0, str(pyemtg))

    import MissionOptions
    import JourneyOptions

    options = MissionOptions.MissionOptions()
    journey = JourneyOptions.JourneyOptions()

    options.mission_name = "OSIRIS_REx_Low"
    options.mission_type = 6             # MGAnDSMs
    options.objective_type = 0           # Minimum deterministic delta-V
    options.NLP_solver_type = 2          # IPOPT
    options.NLP_solver_mode = 1
    options.include_initial_impulse_in_cost = 0
    # A free-point state is defined at its reference epoch, but EMTG's actual
    # first-event epoch is bounded by launch_window_open_date + wait_time.
    # Pin both to the state epoch; otherwise default launch/wait bounds can
    # send trial trajectories before the Bennu SPK coverage begins.
    options.launch_window_open_date = epoch_mjd
    options.global_timebounded = 1
    options.total_flight_time_bounds = [300.0, 900.0]

    # The bundled Bennu SPK is deliberately shorter than DE430. The EMTG
    # defaults start SplineEphem in year 2000 (MJD 51554.5), outside the
    # Bennu kernel's coverage, which causes spline setup to fail before the
    # optimizer starts. These are the OSIRIS tutorial's documented bounds.
    options.earliestPossibleEpoch = 57037.0
    options.latestPossibleEpoch = 60079.0
    if not options.earliestPossibleEpoch <= epoch_mjd <= options.latestPossibleEpoch:
        raise ValueError(
            f"Initial epoch MJD {epoch_mjd:.6f} is outside the configured "
            f"SPICE/SplineEphem window "
            f"[{options.earliestPossibleEpoch}, {options.latestPossibleEpoch}]"
        )

    # These are container paths; the runner mounts the mission and repository
    # at these fixed locations.
    options.universe_folder = "/mission/universe"
    options.HardwarePath = "/repo/HardwareModels/"
    options.override_working_directory = 1
    options.forced_working_directory = "/mission/results/low"
    options.override_mission_subfolder = 1
    options.forced_mission_subfolder = "."

    # EMTG's chemical model needs valid Isp, but fuel/mass is not the objective.
    options.SpacecraftModelInput = 2
    options.IspChem = 320.0
    options.constrain_final_mass = 0
    options.constrain_dry_mass = 0
    options.enable_chemical_propellant_tank_constraint = 0

    journey.journey_name = "FreePoint_Earth_Bennu"
    journey.phase_type = 6
    journey.journey_central_body = "Sun"
    journey.destination_list = [-1, BENNU_INDEX]
    journey.sequence = [EARTH_INDEX]

    journey.departure_class = 1             # Free point
    journey.departure_type = 2              # Free direct
    journey.departure_elements_state_representation = 0  # Cartesian
    journey.departure_elements_frame = 0                  # J2000 / ICRF
    journey.AllowJourneyFreePointDepartureToPropagate = 0
    journey.departure_elements_vary_flag = [0] * 6
    journey.departure_elements = list(sun_state)
    journey.departure_elements_reference_epoch = epoch_mjd
    journey.wait_time_bounds = [0.0, 0.0]

    journey.arrival_type = 1                # Chemical rendezvous
    set_arrival_date_window(journey, bennu_arrival_bounds)
    journey.ManeuverConstraintDefinitions = [
        first_dsm_epoch_constraint(first_dsm_epoch_bounds)
    ]

    options.Journeys = [journey]
    options.number_of_journeys = 1
    options.AssembleMasterConstraintVectors()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    options.write_options_file(str(output_path), writeAll=True)


def prepare() -> Path:
    # EMTG resolves the central-body Universe as <body>.emtg_universe. The
    # tutorial asset is named Sun_OREx.emtg_universe, so expose the expected
    # standard filename without modifying the source asset.
    universe_source = UNIVERSE_DIR / "Sun_OREx.emtg_universe"
    universe_expected = UNIVERSE_DIR / "Sun.emtg_universe"
    if universe_source.is_file() and not universe_expected.exists():
        universe_expected.symlink_to(universe_source.name)

    # High-fidelity flyby conversion creates Earth-centered Journeys, so EMTG
    # also requires an Earth.emtg_universe alongside the Sun universe. Use the
    # repository's standard Earth model as the initial staged model, preserving
    # any mission-specific Earth model the user has already supplied.
    earth_universe_source = REPO_ROOT / "Universe" / "Earth.emtg_universe"
    earth_universe_target = UNIVERSE_DIR / "Earth.emtg_universe"
    if not earth_universe_target.exists():
        if not earth_universe_source.is_file():
            raise FileNotFoundError(
                f"Required Earth-centered Universe file is missing: "
                f"{earth_universe_source}"
            )
        shutil.copy2(earth_universe_source, earth_universe_target)

    et, spacecraft_ssb_state = load_initial_state()
    sun_state, epoch_mjd = transform_state_with_spice(et, spacecraft_ssb_state)
    earth_flyby_bounds = utc_calendar_day_to_mjd_tdb_bounds(
        EARTH_FLYBY_UTC_DATE
    )
    bennu_arrival_bounds = utc_calendar_day_to_mjd_tdb_bounds(
        BENNU_ARRIVAL_UTC_DATE
    )
    first_dsm_epoch_bounds = utc_calendar_day_to_mjd_tdb_bounds(FIRST_DSM_UTC_DATE)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    provenance = {
        "et_seconds_past_j2000": et,
        "epoch_mjd_tdb": epoch_mjd,
        "input_origin": "SSB",
        "input_frame": "J2000",
        "input_position_units": "km",
        "input_velocity_units": "km/s",
        "output_origin": "Sun",
        "output_frame": "J2000",
        "sun_relative_state_km_km_s": sun_state,
        "target_event_date_bounds_mjd_tdb": {
            "earth_periapsis": earth_flyby_bounds,
            "bennu_arrival": bennu_arrival_bounds,
            "first_dsm_epoch": first_dsm_epoch_bounds,
        },
        "target_event_dates_utc": {
            "earth_periapsis": EARTH_FLYBY_UTC_DATE,
            "bennu_arrival": BENNU_ARRIVAL_UTC_DATE,
            "first_dsm_epoch": FIRST_DSM_UTC_DATE,
        },
        "target_event_date_source": TARGET_DATE_SOURCE,
    }
    (CONFIG_DIR / "state_conversion.json").write_text(
        json.dumps(provenance, indent=2) + "\n",
        encoding="utf-8",
    )

    output = CONFIG_DIR / "OSIRIS_REx_Low.emtgopt"
    build_options(
        sun_state,
        epoch_mjd,
        bennu_arrival_bounds,
        first_dsm_epoch_bounds,
        output,
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["prepare"],
        help="Generate the Sun-relative state and EMTG low-fidelity options",
    )
    args = parser.parse_args()

    if args.command == "prepare":
        print(prepare())


if __name__ == "__main__":
    main()