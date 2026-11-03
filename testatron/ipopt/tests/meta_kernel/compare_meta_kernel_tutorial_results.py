"""Lightweight comparison: meta-kernel tutorial baselining vs. flat-mode promoted baselines.

Reads each of the 8 promoted tutorial cases' meta-kernel baselining result.json
(written under testatron/ipopt/tests/meta_kernel/baselining/<case_id>/) and
prints, per case, the replay-stage baseline/generated objective pair already
embedded in each result by the existing comparator (compare_replay), plus
classification and repeatability. No new comparison machinery is introduced:
this only reformats evidence the test run already produced.

Usage:
    python testatron/ipopt/tests/meta_kernel/compare_meta_kernel_tutorial_results.py
"""

import json
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
META_KERNEL_BASELINING_ROOT = REPOSITORY_ROOT / "testatron/ipopt/tests/meta_kernel/baselining"

CASE_IDS = (
    "Config_Files/LowSIRIS-REx",
    "Config_Files/LowSIRIS-REx_high_thrust",
    "Config_Files/LowSIRIS-REx_high_thrust_low_c3",
    "Flybys/EVM",
    "Force_Models/LowSIRIS-REx",
    "Force_Models/LowSIRIS-REx_forcemodel_nlp",
    "LowSIRIS-REx/LowSIRIS-REx",
    "OSIRIS-REx/OSIRIS-REx",
)


def main():
    rows = []
    for case_id in CASE_IDS:
        result_path = META_KERNEL_BASELINING_ROOT / case_id / "result.json"
        if not result_path.is_file():
            rows.append((case_id, "MISSING", None, None, None, None, None))
            continue
        result = json.loads(result_path.read_text())
        first = result.get("first") or {}
        replay = first.get("replay") or {}
        comparison = replay.get("comparison") or {}
        baseline_objective = comparison.get("baseline_objective")
        generated_objective = comparison.get("generated_objective")
        if "baseline_objective" in comparison:
            # Ordinary replay comparison: an explicit objective pair is available.
            objective_match = baseline_objective == generated_objective
        else:
            # Deliberately-infeasible seeded cases (e.g. forcemodel_nlp) use
            # compare_deliberate_infeasible instead, which has no objective
            # pair; structural/feasibility-metric matching is what "acceptable"
            # already encodes for these.
            objective_match = "n/a (deliberate_infeasible)"
        rows.append(
            (
                case_id,
                result.get("classification"),
                bool((result.get("repeatability") or {}).get("stable")),
                baseline_objective,
                generated_objective,
                objective_match,
                comparison.get("acceptable"),
            )
        )

    _print_table(rows)

    all_matched = all(
        row[1] == "matched_tutorial_reference" and row[6]
        for row in rows
    )
    print()
    print(f"8/8 cases present: {len(rows) == len(CASE_IDS) and all(r[1] != 'MISSING' for r in rows)}")
    print(f"All objectives match and classified matched_tutorial_reference: {all_matched}")


def _format_cell(value):
    if value is None:
        return "--"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _print_table(rows):
    """Print rows as a column-aligned, bordered table for console readability."""
    header = (
        "case_id",
        "classification",
        "repeatable",
        "baseline_objective",
        "generated_objective",
        "objective_match",
        "acceptable",
    )
    formatted_rows = [[_format_cell(value) for value in row] for row in rows]
    widths = [
        max(len(header[col]), *(len(row[col]) for row in formatted_rows))
        for col in range(len(header))
    ]

    def render(cells):
        return "| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)) + " |"

    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    print(separator)
    print(render(header))
    print(separator)
    for row in formatted_rows:
        print(render(row))
    print(separator)


if __name__ == "__main__":
    main()
