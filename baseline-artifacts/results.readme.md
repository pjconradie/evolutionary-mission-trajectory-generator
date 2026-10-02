# Stage 0 Baseline Results

Captured on 2026-10-02 before relocating regression suites or IPOPT artifact
roots. This directory contains unreviewed baseline evidence only; it does not
replace immutable Testatron, tutorial, or NASA SNOPT results.

## Execution Environment

| Property | Value |
| --- | --- |
| Commit | `437b6bc9c9091a05d6fa438d6effd720333c15fb` |
| Host Python | `3.13.1` |
| Container platform | `linux/amd64` |
| IPOPT toolchain image | `emtg-pytest-toolchain:2179aeb75eeb13d3` |
| Image ID | `sha256:c67fe5d28c9178cc596bd6e89b5744f03af4dd8ee2f70f3931e72198298a2c2a` |
| Persistent IPOPT build volume | `emtg-pytest-ipopt-2179aeb75eeb13d3` |

The working tree had local documentation and generated-artifact changes during
this capture. The Testatron source options and committed SNOPT baseline files
were not intentionally modified by any Stage 0 command.

## Characterization Contracts

```text
python -m pytest tests/test_ipopt_characterization.py -q
58 passed in 0.51s
```

This confirms the current runner's registry, discovery, staging, provenance,
comparison, classification, and manifest contracts before any relocation.

## Benchmark Results

All six Docker-backed benchmark nodes passed:

| Benchmark | Replay | IPOPT refinement | Recorded duration |
| --- | --- | --- | --- |
| TrackACSProp | Passed | Passed | 3.50 s refinement |
| OSIRIS-REx 2022 | Passed | Passed | 13.60 s refinement |
| OSIRIS-REx 2024 | Passed | Passed | 4.37 s refinement |

The replay stages evaluated the immutable SNOPT/NASA decision vectors with
`run_inner_loop 0`. The refinement stages ran IPOPT from the aligned seed and
passed the current benchmark comparison contracts.

The TrackACS replay and refinement evidence is retained separately in
`track-acs-replay/` and `track-acs-ipopt/`. OSIRIS 2022 and 2024 replay and
refinement were run in shared directories, so their retained `comparison.json`
and `result.json` files describe the later refinement stage. The terminal test
results establish that both nodes passed; future captures must use separate
directories for each stage.

## Testatron Characterization

The full Docker-backed case run completed at 2026-10-02T08:56:48Z. Its
unreviewed manifest is [cases-full/manifest.json](cases-full/manifest.json).

| Classification | Count |
| --- | ---: |
| `reviewable` | 69 |
| `infeasible` | 5 |
| `topology_changed` | 0 |
| `process_failed` | 0 |
| `timed_out` | 1 |
| `parse_failed` | 8 |
| `dependency_blocked` | 54 |
| **Total** | **137** |

The representative run at [cases-representative/manifest.json](cases-representative/manifest.json)
recorded the same kinds of outcomes before the full sweep. TrackACSProp was
also run individually at [cases-track-acs/manifest.json](cases-track-acs/manifest.json).

Recurring current blockers include unavailable `Falcon_9_FT_(RTLS)` vehicle
data, historical spacecraft and power-system files, `Earth_MAGIC.emtg_universe`,
and `Sun_SaturnOrientation.emtg_universe`. The single timeout was
`solver_options/solveroptions_ACEfeasibility` at the configured 300-second
limit. These are baseline classifications, not regressions and not candidates
for tolerance changes during Stage 0.

## Interpretation

The benchmark subset establishes that the current Docker toolchain can replay
aligned immutable SNOPT/NASA seeds and run IPOPT refinements that satisfy the
existing benchmark checks. The full corpus establishes the current
characterizer's portability and failure inventory.

The case characterizer's `reviewable` status is not the future
`matched_snopt` acceptance classification. It does not yet require the
explicit replay-then-refinement workflow or the complete direct comparison
contract planned for the later SNOPT-agreement stage.

Do not alter these baseline artifacts while moving paths or registering pytest
markers. Repeat the same commands after the move and compare classifications,
artifacts, source/truth hashes, and numerical values before changing dependency
or solver-comparison behavior.
