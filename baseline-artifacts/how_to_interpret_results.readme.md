# Interpret Stage 0 Baseline Results

This directory captures pre-move IPOPT verification behavior. Its artifacts are
unreviewed local evidence, not promoted regression truths. Start with
[results.md](results.md) for the recorded environment, benchmark summary, and
full-corpus classification counts.

## Read the Capture

| Artifact | Meaning |
| --- | --- |
| `environment.txt` and `toolchain.txt` | Commit, working-tree state, host and Docker details, image ID, and IPOPT build volume. |
| `*-replay/` | Benchmark evidence from `run_inner_loop 0`; neither SNOPT nor IPOPT runs. |
| `*-ipopt/` | Benchmark evidence from IPOPT refinement starting from the aligned immutable seed. |
| `cases-representative/` | A deliberately small portability and classification sample. |
| `cases-full/` | One result per discovered Testatron case plus aggregate manifests. |
| `testatron-source-truth.sha256` | Immutable source-option and SNOPT-truth identity report. |

Each benchmark stage normally contains:

- `provenance.json` for source/reference/seed paths and SHA-256 records.
- `compatibility.json` for prepared-input and staged-dependency information.
- `result.json` for stage identity, acceptance, output names, and duration.
- `comparison.json` for numerical and structural comparison checks.
- `run.log` for native EMTG and IPOPT output.
- Generated `.emtg` and `XFfile.csv` files where applicable.

Each characterization case directory contains `result.json`,
`compatibility.json`, `run.log`, and, after a generated mission is parsed,
`comparison.csv`. The root `manifest.json` and `manifest.csv` aggregate every
case result.

## Benchmark Meaning

Replay proves that current EMTG inputs and transcription can evaluate the
decision vector archived in the immutable SNOPT/NASA result. Review replay
`comparison.json` for successful topology, schema, objective, totals, endpoint,
and feasibility checks.

Refinement runs native IPOPT from that aligned seed. Review refinement
`comparison.json` for feasibility, objective policy, topology/schema checks,
and native IPOPT diagnostics such as `initial_infeasibility`, iteration count,
terminal constraint violation, and `native_exit`.

The benchmark subset is valid evidence that IPOPT replay/refinement works
against those immutable SNOPT-generated references. It is not yet the full
case-corpus acceptance contract.

## Case Classifications

The current characterizer records baseline behavior; its classifications are
not all pass/fail decisions:

| Classification | Meaning in this capture |
| --- | --- |
| `reviewable` | EMTG ran, generated a parseable mission, and passed current feasibility/topology checks. It is not a promoted truth or a full SNOPT match. |
| `dependency_blocked` | EMTG could not run the case with available staged public inputs. Preserve the missing-resource detail. |
| `parse_failed` | EMTG completed but the runner found no usable `.emtg` mission output, or could not parse/compare it. |
| `infeasible` | A mission output exists, but its worst constraint exceeds the source feasibility tolerance. |
| `timed_out` | EMTG exceeded the configured process timeout. |
| `process_failed` | EMTG exited with a nonzero status. |
| `topology_changed` | The generated journey/event structure differs from the immutable baseline. |

`reviewable` is not the later `matched_snopt` classification. The later
SNOPT-agreement stage must explicitly replay the archived seed, run IPOPT
refinement, require an accepted native IPOPT exit, and compare the complete
mission contract to SNOPT.

## Known Stage 0 Conditions

The recorded full run has 69 `reviewable`, 54 `dependency_blocked`, 8
`parse_failed`, 5 `infeasible`, and 1 `timed_out` cases. The recurring current
blockers are unavailable `Falcon_9_FT_(RTLS)` data, historical spacecraft and
power-system files, `Earth_MAGIC.emtg_universe`, and
`Sun_SaturnOrientation.emtg_universe`. The known timeout is
`solver_options/solveroptions_ACEfeasibility` at 300 seconds.

These are reference observations. Do not hide them with a tolerance change,
placeholder resource, altered immutable test input, or reclassification during
the path-only migration.

## Compare a Later Run

After moving paths or changing test organization, create a new capture with
the same commands and compare it against this one:

1. The source/truth SHA-256 reports must be identical.
2. Benchmark node outcomes, comparison checks, native IPOPT diagnostics, and
	numerical values must be unchanged within the recorded comparison policy.
3. The full manifest must contain the same case IDs, classification counts,
	and per-case classification/details unless a separately reviewed dependency
	or solver change explains the difference.
4. Generated artifacts must remain outside immutable `testatron/tests` data.

Current case manifests contain runtime `/repo` and `/artifacts` paths. They
are valid baseline evidence but are not portable commit-ready provenance. The
later dependency/provenance work must write repository-relative paths before
such evidence is committed.

## Capture Caveat

The original TrackACS capture retained replay and refinement in separate
directories. The original OSIRIS 2022 and 2024 captures reused a directory per
mission, so their retained `comparison.json` and `result.json` describe only
the later refinement stage even though both pytest nodes passed. New captures
must use separate `*-replay/` and `*-ipopt/` directories.

For detailed routine benchmark commands and field-level review guidance, see
[testatron/ipopt/benchmarks/how_to_generate_results.readme.md](../testatron/ipopt/benchmarks/how_to_generate_results.readme.md)
and
[testatron/ipopt/benchmarks/how_to_interpret_results.readme.md](../testatron/ipopt/benchmarks/how_to_interpret_results.readme.md).
