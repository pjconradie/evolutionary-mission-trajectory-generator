"""Build a per-case lookup table mapping each Testatron case to its declared
input configuration, the outputs recorded in its committed truth .emtg, and the
launch-vehicle key resolved by mass-matching the truth launch mass.

The table is the authoritative reference the IPOPT characterization harness needs
to prepare each case correctly (e.g. resolve the real LaunchVehicleKey instead of
defaulting to Falcon_9_FT_(RTLS)) and to verify results against known-good values.

Run from the repository root:
    python testatron/ipopt/tools/build_case_lookup.py
Outputs:
    testatron/ipopt/case_lookup.json
    testatron/ipopt/case_lookup.csv
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "testatron" / "tests"
OUTPUT_JSON = REPO_ROOT / "testatron" / "ipopt" / "case_lookup.json"
OUTPUT_CSV = REPO_ROOT / "testatron" / "ipopt" / "case_lookup.csv"

# Candidate launch-vehicle libraries, in the order the harness would prefer them.
LAUNCH_VEHICLE_LIBRARIES = (
    REPO_ROOT / "docs/0_Users/tutorial/Tutorial_EMTG_Files/Config_Files/hardware_models"
    "/LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt",
    REPO_ROOT / "testatron/HardwareModels/default.emtg_launchvehicleopt",
    REPO_ROOT / "HardwareModels/default.emtg_launchvehicleopt",
)

DEFAULT_LAUNCH_VEHICLE_KEY = "Falcon_9_FT_(RTLS)"
# The delivered mass equals a fixed value for these no-polynomial vehicles.
CONSTANT_MASS_KEYS = {"Fixed_Initial_Mass", "Depart_With_Spacecraft_Thrusters"}
MASS_MATCH_TOLERANCE_KG = 1.0


def load_launch_vehicles():
    """Return {key: (library_name, [coefficients], c3_lo, c3_hi)} across libraries."""
    catalog = {}
    for library in LAUNCH_VEHICLE_LIBRARIES:
        if not library.is_file():
            continue
        for line in library.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            tokens = stripped.split()
            if len(tokens) < 7:
                continue
            name = tokens[0]
            try:
                c3_lo, c3_hi = float(tokens[4]), float(tokens[5])
                coefficients = [float(token) for token in tokens[7:]]  # [6] is AdapterMass
            except ValueError:
                continue
            catalog.setdefault(name, (library.name, coefficients, c3_lo, c3_hi))
    return catalog


def polynomial_mass(coefficients, c3):
    return sum(coefficient * c3**power for power, coefficient in enumerate(coefficients))


def resolve_launch_vehicle(catalog, launch_c3, launch_mass):
    """Return the vehicle key whose delivered mass at launch_c3 matches the truth."""
    if launch_c3 is None or launch_mass is None:
        return None
    best = None
    for key, (library_name, coefficients, c3_lo, c3_hi) in catalog.items():
        if not (c3_lo - 1e-6 <= launch_c3 <= c3_hi + 1e-6):
            continue
        modeled = polynomial_mass(coefficients, launch_c3)
        error = abs(modeled - launch_mass)
        if best is None or error < best["mass_error_kg"]:
            best = {
                "key": key,
                "library": library_name,
                "matched_mass_kg": round(modeled, 4),
                "mass_error_kg": round(error, 4),
            }
    if best is not None and best["mass_error_kg"] <= MASS_MATCH_TOLERANCE_KG:
        return best
    return {"key": None, "library": None, "matched_mass_kg": None,
            "mass_error_kg": None, "note": "no library mass-match at launch C3"}


def read_option(text, name):
    match = re.search(rf"(?m)^{re.escape(name)}\s+(.+?)\s*$", text)
    return match.group(1) if match else None


def parse_source_options(path):
    text = path.read_text(errors="replace")
    declared_key = read_option(text, "LaunchVehicleKey")
    return {
        "mission_type": read_option(text, "mission_type"),
        "objective_type": read_option(text, "objective_type"),
        "run_inner_loop": read_option(text, "run_inner_loop"),
        "spacecraft_model_input": read_option(text, "SpacecraftModelInput"),
        "launch_vehicle_library_declared": read_option(text, "LaunchVehicleLibraryFile"),
        "launch_vehicle_key_declared": declared_key,
        "launch_vehicle_key_effective_default": (
            declared_key if declared_key else DEFAULT_LAUNCH_VEHICLE_KEY
        ),
    }


def parse_truth_mission(path):
    """Extract launch C3/mass and headline outputs from a committed truth .emtg."""
    text = path.read_text(errors="replace")
    launch_c3 = launch_mass = None
    events = []
    for line in text.splitlines():
        if not re.match(r"^\s*\d+\s*\|", line):
            continue
        fields = [field.strip() for field in line.split("|")]
        if len(fields) < 30:
            continue
        events.append(fields[3])
        if fields[3] == "launch" and launch_mass is None:
            try:
                launch_c3 = float(fields[11])
                launch_mass = float(fields[29])
            except ValueError:
                pass

    def grab(pattern, cast=float):
        match = re.search(pattern, text)
        if not match:
            return None
        try:
            return cast(match.group(1))
        except ValueError:
            return None

    return {
        "launch_c3": launch_c3,
        "launch_mass_kg": launch_mass,
        "objective_J": grab(r"(?m)^J = (\S+)"),
        "final_mass_kg": grab(r"Final mass including propellant margin \(kg\): (\S+)"),
        "total_deterministic_deltav_kms": grab(
            r"Total deterministic deltav \(km/s\): (\S+)"
        ),
        "worst_constraint": (
            (m := re.search(r"Worst constraint is (F\[\d+\]: .+)", text))
            and m.group(1).strip()
        )
        or None,
        "num_journeys": text.count("\nJourney name:"),
        "num_events": len(events),
        "event_topology": events,
    }


def build():
    catalog = load_launch_vehicles()
    records = []
    for source in sorted(TESTS_ROOT.rglob("*.emtgopt")):
        case_id = source.relative_to(TESTS_ROOT).with_suffix("").as_posix()
        truth = source.with_suffix(".emtg")
        record = {
            "case_id": case_id,
            "source_options": source.relative_to(REPO_ROOT).as_posix(),
            "truth_mission": (
                truth.relative_to(REPO_ROOT).as_posix() if truth.is_file() else None
            ),
            "input": parse_source_options(source),
        }
        if truth.is_file():
            outputs = parse_truth_mission(truth)
            record["truth_outputs"] = outputs
            effective_key = record["input"]["launch_vehicle_key_effective_default"]
            if effective_key in CONSTANT_MASS_KEYS:
                record["resolved_launch_vehicle"] = {
                    "key": effective_key,
                    "library": "constant-mass vehicle (no C3 polynomial)",
                    "matched_mass_kg": outputs["launch_mass_kg"],
                    "mass_error_kg": 0.0,
                }
            else:
                record["resolved_launch_vehicle"] = resolve_launch_vehicle(
                    catalog, outputs["launch_c3"], outputs["launch_mass_kg"]
                )
        else:
            record["truth_outputs"] = None
            record["resolved_launch_vehicle"] = None
        records.append(record)

    OUTPUT_JSON.write_text(json.dumps(records, indent=2) + "\n")

    flat_fields = [
        "case_id", "mission_type", "objective_type", "run_inner_loop",
        "launch_vehicle_key_declared", "resolved_launch_vehicle_key",
        "launch_c3", "launch_mass_kg", "objective_J", "final_mass_kg",
        "num_journeys", "num_events", "mass_match_error_kg",
    ]
    with OUTPUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=flat_fields)
        writer.writeheader()
        for record in records:
            outputs = record.get("truth_outputs") or {}
            resolved = record.get("resolved_launch_vehicle") or {}
            writer.writerow({
                "case_id": record["case_id"],
                "mission_type": record["input"]["mission_type"],
                "objective_type": record["input"]["objective_type"],
                "run_inner_loop": record["input"]["run_inner_loop"],
                "launch_vehicle_key_declared": record["input"]["launch_vehicle_key_declared"],
                "resolved_launch_vehicle_key": resolved.get("key"),
                "launch_c3": outputs.get("launch_c3"),
                "launch_mass_kg": outputs.get("launch_mass_kg"),
                "objective_J": outputs.get("objective_J"),
                "final_mass_kg": outputs.get("final_mass_kg"),
                "num_journeys": outputs.get("num_journeys"),
                "num_events": outputs.get("num_events"),
                "mass_match_error_kg": resolved.get("mass_error_kg"),
            })

    return records


def main():
    records = build()
    total = len(records)
    with_truth = sum(1 for r in records if r["truth_mission"])
    needs_launch = [
        r for r in records
        if r.get("truth_outputs") and r["truth_outputs"]["launch_c3"] is not None
    ]
    resolved = sum(
        1 for r in needs_launch if (r.get("resolved_launch_vehicle") or {}).get("key")
    )
    key_mismatch = [
        r for r in needs_launch
        if (r.get("resolved_launch_vehicle") or {}).get("key")
        and (r.get("resolved_launch_vehicle") or {}).get("key")
        != r["input"]["launch_vehicle_key_effective_default"]
    ]
    print(f"cases:                 {total}")
    print(f"with committed truth:  {with_truth}")
    print(f"launch-vehicle cases:  {len(needs_launch)}")
    print(f"  mass-matched key:    {resolved}")
    print(f"  key differs from harness default: {len(key_mismatch)}")
    for record in key_mismatch:
        resolved_key = record["resolved_launch_vehicle"]["key"]
        default_key = record["input"]["launch_vehicle_key_effective_default"]
        print(f"    {record['case_id']}: default={default_key} -> truth={resolved_key}")
    print(f"\nwrote {OUTPUT_JSON.relative_to(REPO_ROOT)}")
    print(f"wrote {OUTPUT_CSV.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
