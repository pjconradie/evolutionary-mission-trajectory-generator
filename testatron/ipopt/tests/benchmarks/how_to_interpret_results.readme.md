# How to Interpret Benchmark Results

Benchmark artifacts are unreviewed evidence. They do not replace the immutable
Testatron, tutorial, or NASA SNOPT result packages used as references.

## Artifact Checklist

Review these files in each probe's artifact directory:

| File | What to verify |
| --- | --- |
| `provenance.json` | Source options, immutable baseline `.emtg`, and seed `XFfile.csv` paths and SHA-256 values. |
| `compatibility.json` | Staged options, hardware, universe, and seed configuration. |
| `result.json` | Intended stage, `acceptable: true`, generated mission, log, comparison file, and duration. |
| `comparison.json` | Primary numerical and structural comparison evidence. |
| `run.log` | Native EMTG and IPOPT diagnostics. |
| Generated `.emtg` | Inspect when a comparison check fails or appears suspicious. |

## Replay Results

A replay evaluates the aligned immutable reference decision vector without
running IPOPT. In `comparison.json`, verify that:

- Every `checks` entry is `true`.
- `baseline_objective` and `generated_objective` agree within the listed
	tolerance.
- Journey names, event topology, decision descriptions, and decision-vector
	length agree.
- Endpoint deltas remain below their endpoint tolerances.
- `feasible` is `true`.

For example, the TrackACS replay has a position delta of `0.18779 km`, below
the `1 km` limit, and a velocity delta of $4.0 \times 10^{-8}$ km/s, below
$1.0 \times 10^{-7}$ km/s.

## IPOPT Refinement Results

An IPOPT refinement starts from the verified reference seed. In
`comparison.json`, verify that:

- `ipopt_native_success`, `feasible`, `event_topology`, and every
	decision-schema check are `true`.
- `objective_delta` is within `objective_comparison_band`.
- `initial_infeasibility` and `terminal_constraint_violation` are acceptable.
- `native_exit` is `Optimal Solution Found.`

The TrackACS refinement is a clean example: it has zero objective delta,
feasibility of $8.19 \times 10^{-6}$ against a $1.0 \times 10^{-5}$ limit,
eight IPOPT iterations, and a native successful exit.

## Preserve Both Stages

Use a distinct `EMTG_TEST_ARTIFACT_DIR` for replay and refinement. Each stage
writes files such as `comparison.json` and `result.json`; running both stages
in one directory causes the later stage to overwrite the earlier evidence.

For example, retain OSIRIS 2024 evidence in separate directories:

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/osiris-2024-replay" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2024_replay_matches_nasa_result \
	--integration -vv

EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/osiris-2024-ipopt" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2024_ipopt_refinement_retains_nasa_seed \
	--integration -vv
```