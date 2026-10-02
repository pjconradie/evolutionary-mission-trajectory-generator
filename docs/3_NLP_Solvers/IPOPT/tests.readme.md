# IPOPT Testatron Verification Plan

## Purpose

This plan makes the complete `testatron/tests` corpus executable with the
open-source IPOPT backend and uses the committed SNOPT-generated `.emtg` files
as the immutable numerical baseline.

IPOPT is not accepted merely because it produces a feasible result. For each
comparable case, the IPOPT result must agree with the corresponding SNOPT
result within an explicit, reviewed numerical contract. The committed SNOPT
options and `.emtg` files are never overwritten, regenerated, or promoted from
an IPOPT run.

Run commands in this document from the repository root.

## IPOPT Suite Layout

The immutable source inputs and SNOPT baselines remain below
`testatron/tests`. IPOPT-generated characterization evidence is organized
separately beneath `testatron/ipopt/tests`:

| Root | Contents | Pytest marker |
| --- | --- | --- |
| `testatron/ipopt/tests/tests` | Per-case IPOPT Testatron staging, logs, comparisons, and manifests | `ipopt_tests` |
| `testatron/ipopt/tests/benchmarks` | IPOPT benchmark replay and refinement evidence | `ipopt_benchmarks` |

`testatron/ipopt/tests/tests` is artifact data despite its nested `tests/tests`
name. Python test code remains below the repository-level `tests/` directory.

`ipopt_benchmarks` marks the current Python tests that create or validate the
benchmark artifact root. `ipopt_tests` is reserved for the future Docker-backed
per-case suite: each node must replay an immutable SNOPT baseline, refine it
with IPOPT, and enforce direct SNOPT/IPOPT agreement. The existing
characterization-runner contracts are `unit` tests; they do not carry
`ipopt_tests` because they neither execute the corpus nor compare IPOPT against
SNOPT.

Use focused selections when working on one suite:

```bash
pytest -m ipopt_benchmarks
```

After the per-case suite is implemented, run it with:

```bash
pytest -m ipopt_tests
```

## Baseline Rules

- The source option file is `testatron/tests/<group>/<case>.emtgopt`.
- The immutable SNOPT baseline is its adjacent
  `testatron/tests/<group>/<case>.emtg` file.
- IPOPT runs use staged copies of options and dependencies only. The source
  options, SNOPT baseline, tutorial result packages, and NASA result packages
  must remain unchanged.
- Every generated artifact is marked `unreviewed` until a reviewer accepts the
  comparison and its provenance.
- A public replacement for an unavailable input is permitted only when its
  mapping is explicit, physically justified, and recorded in the case
  `compatibility.json`.
- A case with unavailable or incompatible public hardware is
  `dependency_blocked`; it is not a solver pass.

## Unavailable Hardware Models

Hardware availability is a prerequisite for cross-solver verification. A case
cannot establish IPOPT accuracy unless it uses the same physical hardware model
as its SNOPT baseline, or a public replacement that has first passed the
SNOPT-seed replay comparison.

When a required launch-vehicle library, spacecraft file, propulsion file,
power-system file, throttle table, or nested hardware dependency is unavailable,
the staging/preflight process must stop before invoking EMTG for that case. It
must classify the case as `dependency_blocked`, which is neither an IPOPT pass
nor an IPOPT numerical mismatch.

Each blocked case must write `compatibility.json` and `result.json` containing:

- The source case and option field that references the unavailable model.
- The required filename and dependency type.
- Any public replacement considered, whether it was accepted or rejected, and
	the technical reason.
- The expected source location, checksum when known, and the exact remediation
	needed to make the case runnable.

The aggregate manifest must count blocked cases separately, list their missing
dependencies, and cause preflight and full-suite commands to return a nonzero
status while any dependency remains unresolved.

Resolve unavailable hardware in this order:

1. **Equivalent public model available:** stage the model in the generated
	 case directory, retain the original vehicle/engine key where applicable,
	 record its SHA-256 and mapping rationale, then run SNOPT-seed replay. The
	 replacement is accepted only if replay agrees with the immutable SNOPT
	 baseline within the approved replay contract.
2. **Original distributable model available:** preserve the model with a
	 documented source and checksum, stage it without modifying the source test,
	 and run replay before IPOPT refinement.
3. **No equivalent public model:** leave the case `dependency_blocked`. A new
	 public substitute may be introduced only through review and only after it
	 demonstrably reproduces the SNOPT replay within tolerance.
4. **Proprietary or nonredistributable model:** do not add a fabricated file,
	 an empty throttle table, a symlink that conceals a semantic change, or a
	 case-specific tolerance exception. The case remains blocked until an
	 approved public counterpart exists.

A public replacement that changes replay objective, topology, endpoint state,
or other required metric is incompatible. The correct outcome is
`dependency_blocked` with an explanation, not an IPOPT run whose difference is
attributed to the solver.

## What Must Match

The solver should reproduce the physical mission represented by the SNOPT
baseline. Decision vectors are diagnostic data, not the primary equality
criterion: distinct local optima can use different decision vectors while
describing an equivalent solution. The required comparison is instead:

| Property | Requirement |
| --- | --- |
| Native solver outcome | IPOPT reports an accepted native success, not merely an EMTG chaperone-restored incumbent. |
| Feasibility | IPOPT worst constraint violation is within the source mission feasibility tolerance. |
| Mission structure | Same journey count, journey names, event topology, and event identities as the SNOPT baseline. |
| Objective | IPOPT objective agrees with the SNOPT objective within the approved objective tolerance for the case. |
| Mission totals | Total deterministic delta-v, flight time, and final mass agree within approved metric tolerances. |
| Event states | Departure and arrival epoch, Cartesian position, velocity, and mass agree within approved endpoint tolerances. |
| Decision schema | Decision-variable descriptions and vector length agree. Values are reported for diagnosis but are not required to be identical when equivalent solutions exist. |

A feasible IPOPT solution with a materially different objective, topology, or
terminal state is a comparison failure. It is not evidence that IPOPT is an
accurate replacement for SNOPT.

## Two-Stage Comparison

### 1. SNOPT-seed replay

The first stage evaluates the decision vector archived in the immutable SNOPT baseline with `run_inner_loop 0`; neither SNOPT nor IPOPT runs during this replay. Its
purpose is to prove that the current EMTG transcription, staged dependencies,
and baseline use the same decision schema.

The replay must match the SNOPT baseline tightly. A mismatch here is a model,
input, schema, or dependency problem, not an IPOPT convergence problem. Do not
continue to solver comparison until replay succeeds.

Initial replay contract:

| Metric | Initial tolerance |
| --- | --- |
| Objective and mission totals | Relative $1 \times 10^{-10}$, absolute $1 \times 10^{-12}$ |
| Departure/arrival epoch | $1 \times 10^{-8}$ days |
| Position | $1$ km |
| Velocity | $1 \times 10^{-7}$ km/s |
| Mass | $1 \times 10^{-6}$ kg |

These values match the existing replay implementation in
`testatron/ipopt_characterization.py`. They are a starting contract, not a
license to weaken a failing case without analysis.

### 2. IPOPT refinement from the SNOPT seed

The second stage runs IPOPT from the same aligned SNOPT decision vector. It
proves whether IPOPT can preserve the SNOPT solution's mission quality and
physical outcome.

For every successful refinement, the comparison must write:

- IPOPT native exit, iteration count, initial infeasibility, and terminal
  constraint violation from `run.log`.
- SNOPT and IPOPT values plus deltas for objective, worst violation, total
  delta-v, flight time, and final mass.
- Departure/arrival state deltas for every journey.
- Topology and decision-schema checks.
- The full staged-input dependency provenance and SHA-256 hashes.

The current refinement logic correctly checks native feasibility, finite and
in-bound decisions, topology, schema, and objective non-regression. It must be
extended to require **objective agreement with SNOPT**, not just a one-sided
non-regression assertion. A result that appears better than SNOPT by more than
the comparison band is also a review event: it may be a genuine improvement,
but it may instead indicate different staged hardware, ephemerides, or mission
semantics.

## Tolerance Policy

There is no defensible single absolute tolerance for all EMTG missions. The
comparison policy must be versioned and case-class aware, with every tolerance
stored in code or a reviewed manifest rather than selected after a failure.

Use this progression:

1. Start with the replay tolerances above to establish input equivalence.
2. For IPOPT refinement, use a conservative initial objective agreement band:

	$$|J_{\mathrm{IPOPT}} - J_{\mathrm{SNOPT}}| \leq a_J + r_J \max(|J_{\mathrm{IPOPT}}|, |J_{\mathrm{SNOPT}}|)$$

	Begin with $r_J = 10^{-6}$ and $a_J = 10^{-10}$ for authoritative mission
	cases. Demonstration cases may have a separately reviewed looser policy,
	initially $r_J = 10^{-3}$ and $a_J = 10^{-8}$.
3. Apply similarly documented absolute/relative bands to delta-v, flight time,
	final mass, and terminal state components. Do not use a generic
	`Comparatron` tolerance for all fields.
4. Calibrate these proposed bands with a fixed, representative subset spanning
	chemical, low-thrust, coast, flyby, force-model, and state-representation
	transcriptions. Publish the observed distributions before accepting a
	tolerance change.
5. A tolerance change requires a reviewed rationale tied to solver behavior or
	physical scale. Never change a tolerance solely to convert an individual
	failure into a pass.

For a maximization objective, compare the same absolute difference. The
objective sense still matters for the separate non-regression diagnostic.

## Public Dependency Strategy

The legacy Testatron corpus references dependencies that are not all committed.
The staging layer must resolve them before EMTG runs:

| Missing legacy reference | Resolution |
| --- | --- |
| `NLSII_April2017.emtg_launchvehicleopt` and `NLSII_August2018.emtg_launchvehicleopt` | Map to `docs/0_Users/tutorial/Tutorial_EMTG_Files/Config_Files/hardware_models/LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`, while preserving the original `LaunchVehicleKey`. |
| `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` | Map to `empty.ThrottleTable` only when the engine type is table-independent. Table-dependent cases require a physically compatible public table and remain blocked until one is reviewed. |
| `de430.bsp`, Mars SPKs, Jupiter SPKs | The operator provides verified files in `testatron/universe/ephemeris_files` before preflight. Preflight verifies their filenames and checksums; it never downloads them. Do not generate or use placeholder SPICE kernels. |
| `naif0012.tls`, `pck00010.tpc` | Stage the committed copies from the tutorial universe inputs with provenance. |
| `DoesNotExist.grv` | Preserve it when gravity order is zero; it is an intentional sentinel, not a missing dependency. |

The full dependency inventory, source URL or repository source, SHA-256,
mapping reason, and final staged path must be written to `compatibility.json`.

## Implementation Plan

1. Keep IPOPT characterization artifacts below `testatron/ipopt/tests/tests`
	and benchmark artifacts below `testatron/ipopt/tests/benchmarks`. Update
	operational references and the benchmark registry without changing immutable
	source inputs, SNOPT baselines, or historical generated-evidence paths.
2. Register `ipopt_tests` and `ipopt_benchmarks` in `pytest.ini`. Apply them
	to Python tests that respectively execute or validate case and benchmark
	evidence. Keep both markers included in ordinary pytest collection.
3. Add a versioned Testatron dependency manifest for externally provided NAIF
	kernels, including canonical source URL for provenance, filename, SHA-256,
	and required destination.
4. Extend `testatron/ipopt_characterization.py` with a preflight command that
	validates all Testatron case dependencies without downloading anything. It
	must reject missing or checksum-mismatched kernels and report the exact
	required filename, expected destination, canonical source URL, and expected
	SHA-256 so an operator can provide the correct resource.
5. Refactor `prepare_case()` into dependency resolution plus staged option
	generation. Preserve its current legacy NLSII and guarded throttle-table
	mappings, and rewrite paths only in the generated option copy.
6. Extend the case result and comparison output with endpoint deltas, IPOPT
	diagnostics, and a structured SNOPT-agreement result.
7. Add comparison classifications that distinguish:
	- `matched_snopt`: native IPOPT success and every approved comparison check
	  passes.
	- `mismatch_snopt`: IPOPT completed but differs materially from the SNOPT
	  baseline.
	- `dependency_blocked`, `timed_out`, `process_failed`, `parse_failed`,
	  `infeasible`, and `topology_changed`: operational or physics/solver
	  outcomes that are not matches.
8. Add a manifest summary with counts for each classification and a direct list
	of all non-matches. The all-case acceptance condition is zero unresolved
	dependencies **and** zero unexplained SNOPT mismatches for the approved
	comparable set.
9. Add unit tests for dependency mapping, checksum behavior, path rewriting,
	zero-order gravity, comparison bands, objective direction, topology, and
	native IPOPT exit handling.
10. Add Docker-backed smoke tests for one case using public NLSII data and one
	case requiring SPICE kernels. Run complete `ipopt_tests` and
	`ipopt_benchmarks` selections as core pytest coverage; record cold and warm
	runtimes before setting CI resource limits.

## Execution Model

The legacy `testatron/testatron.py` runner remains historical tooling. It uses
direct paths and a global Comparatron tolerance and is not the IPOPT
implementation target.

The supported path is the staged runner in
`testatron/ipopt_characterization.py`:

1. Preflight public dependencies.
2. Copy each source option into an isolated writable artifact directory below
	`testatron/ipopt/tests/tests`.
3. Write the IPOPT-specific staged option and `compatibility.json`.
4. Run the IPOPT-enabled `/build/src/EMTGv9` inside the Docker toolchain.
5. Parse the generated mission, compare it directly to the adjacent immutable
	SNOPT `.emtg` baseline, and write `result.json`, comparison data, and
	`run.log`.
6. Update a resumable unreviewed manifest after each case. Benchmark stages
	write their evidence below `testatron/ipopt/tests/benchmarks`.

The repository mount is read-only in Docker. Only the selected artifact
directory is writable. This prevents a test run from modifying SNOPT baselines
or source options by accident.

## Required Artifacts

Each staged case must produce:

| Artifact | Content |
| --- | --- |
| `run.log` | EMTG and IPOPT native diagnostics |
| `compatibility.json` | Source dependencies, substitutions, hashes, and staging provenance |
| `comparison.json` | Structured SNOPT/IPOPT checks, tolerances, baseline values, IPOPT values, and deltas |
| `comparison.csv` | Tabular numerical deltas for review |
| `result.json` | Classification, exit status, timing, and artifact paths |
| `manifest.json` and `manifest.csv` | Resumable aggregate inventory and classification counts |

No generated file is a replacement truth. A reviewer must investigate every
`mismatch_snopt` before accepting IPOPT for that case.

## Success Criteria

The portable IPOPT Testatron implementation is complete when:

1. Every discovered `testatron/tests/**/*.emtgopt` case has dependency
	provenance and can pass preflight without an unresolved input.
2. The complete Docker run creates one result record per source case without
	modifying any source option or SNOPT baseline hash.
3. Each successful IPOPT case has a native IPOPT success exit, feasible result,
	and a direct structured comparison to its SNOPT baseline.
4. Every approved comparable case is classified `matched_snopt`; all remaining
	cases have a specific, reproducible issue classification and are not counted
	as solver verification passes.
5. Any new or adjusted comparison tolerance is reviewed, versioned, and backed
	by recorded cross-solver evidence.
6. `pytest -m ipopt_tests` and `pytest -m ipopt_benchmarks` both pass, and
	plain pytest collection includes both core marker groups.
