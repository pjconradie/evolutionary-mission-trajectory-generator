# IPOPT Verification Implementation Plan

## Goal

Implement [IPOPT Testatron Verification Plan](tests.readme.md) in stages without confusing pre-existing failures with regressions caused by the artifact layout change. Do not begin the Docker deployment plan until the benchmark and case suites are stable, dependency-ready, and pass their approved SNOPT/IPOPT comparison contracts.

The immutable source options and SNOPT `.emtg` results below `testatron/tests`
remain untouched throughout this work.

## Stage 0: Capture a Stable Baseline (Complete 2026-10-02)

Before moving any files, manually execute the current benchmark and case
workflows and retain their evidence outside the artifact roots that will move.

1. Record the checked-out commit, `git status --short`, Docker image tag,
   backend build-volume name, `linux/amd64` platform, IPOPT version, and tool
   versions.
2. Run the current benchmark integration probes. Retain each test's artifacts
   in a separate directory using `EMTG_TEST_ARTIFACT_DIR`:

   ```bash
   EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/track-acs-replay" \
   python -m pytest \
     tests/integration/test_ipopt_backend.py::test_track_acs_replay_matches_committed_truth \
     --integration -vv

   EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/track-acs-ipopt" \
   python -m pytest \
     tests/integration/test_ipopt_backend.py::test_track_acs_ipopt_refinement_retains_seed \
     --integration -vv

   EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/osiris-2022" \
   python -m pytest \
     tests/integration/test_ipopt_backend.py::test_osiris_2022_replay_matches_nasa_result \
     tests/integration/test_ipopt_backend.py::test_osiris_2022_ipopt_refinement_retains_nasa_seed \
     --integration -vv

   EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/osiris-2024" \
   python -m pytest \
     tests/integration/test_ipopt_backend.py::test_osiris_2024_replay_matches_nasa_result \
     tests/integration/test_ipopt_backend.py::test_osiris_2024_ipopt_refinement_retains_nasa_seed \
     --integration -vv
   ```

3. Run characterization contracts before any relocation:

   ```bash
   python -m pytest tests/test_ipopt_characterization.py -q
   ```

4. Manually run the existing case characterizer, first against one
   representative case from each Testatron group, then the complete discovered
   corpus. Use an explicit output root and retain its `manifest.json`,
   `manifest.csv`, logs, comparisons, and compatibility records.

   ```bash
   python testatron/ipopt_characterization.py --ipopt-characterization \
     --emtg /path/to/IPOPT-enabled-EMTGv9 \
     --output-root "$PWD/baseline-artifacts/cases" \
     --timeout 300
   ```

   Use `--filter` for representative groups and `--resume` only when resuming
   the same retained output root.

5. Record source-option and SNOPT-truth SHA-256 hashes before and after these
   runs. Capture all existing failures by category; they are the baseline for
   later comparison and must not be silently reclassified as path-move defects.

The Stage 0 output is a baseline report, not promoted truth data.

### Completion Record

Stage 0 completed before any regression-suite or IPOPT artifact-root move.
The retained evidence is under [baseline-artifacts](../../../baseline-artifacts):

1. The characterization contract suite passed: `58 passed`.
2. All six Docker-backed TrackACS and OSIRIS replay/refinement benchmark nodes
   passed. TrackACS uses separate replay and refinement directories. The OSIRIS
   2022 and 2024 replay/refinement invocations shared a directory per vintage,
   so each retained OSIRIS directory contains only the later refinement JSON;
   terminal results establish that both nodes passed. Future captures must use
   separate replay and refinement directories.
3. A Docker-backed representative characterization sweep and complete 137-case
   characterization sweep were retained. The complete manifest records: 69
   `reviewable`, 5 `infeasible`, 1 `timed_out`, 8 `parse_failed`, and 54
   `dependency_blocked` cases. These are current behavioral classifications,
   not SNOPT/IPOPT agreement results.
4. The 137 immutable source `.emtgopt` files and 137 adjacent SNOPT `.emtg`
   results were verified unchanged against `HEAD` before and after capture.
   The two retained SHA-256 reports contain 274 identical records.

See [results.md](../../../baseline-artifacts/results.md) for the execution
environment and results, and the adjacent generation and interpretation guides
for reproduction details. The retained full-case manifests include container
paths and are runtime evidence, not portable committed provenance. Do not
reclassify known blockers or change comparison semantics as part of Stage 1.

## Stage 1: Organize Regression Suites (Complete 2026-10-02)

Keep generic regression coverage separate from IPOPT-generated artifact data.
The following tests validate PyEMTG parsing, option serialization, and mission
comparison across frozen Testatron and OSIRIS data; they are not an IPOPT unit
suite:

```bash
python -m pytest \
   tests/test_comparatron.py \
   tests/test_mission_options.py \
   tests/test_mission_parser.py -q
```

After retaining the Stage 0 result, move the suites with Git history preserved:

```bash
mkdir -p tests/regression
git mv tests/test_comparatron.py tests/regression/test_comparatron.py
git mv tests/test_mission_options.py tests/regression/test_mission_options.py
git mv tests/test_mission_parser.py tests/regression/test_mission_parser.py
```

Preserve `pytest.mark.regression` on every moved module. Do not move these
files to `testatron/ipopt/tests/unit`: that root is for IPOPT-generated
evidence, while these tests cover shared parser, options, and comparison
behavior independent of the NLP backend.

Update `test_mission_parser.py` to obtain the repository root from the shared
`repository_root` fixture instead of `Path(__file__).resolve().parents[1]`;
after the move, that expression resolves to `tests/`, not the repository root.

`pytest.ini` needs no discovery change because `testpaths = tests` recursively
collects `tests/regression`. Verify the move before any IPOPT artifact-path
change:

```bash
python -m pytest tests/regression -q
python -m pytest -m regression -q
python -m pytest --collect-only -q
```

The relocated suites must have the same test outcomes and remain present in
ordinary pytest collection. Treat any difference as a regression-suite move
defect before continuing.

### Completion Record

The three modules were moved with `git mv` to `tests/regression/`, preserving
their `pytest.mark.regression` markers. The mission-parser module now resolves
its runtime paths through the shared `repository_root` fixture rather than its
own file location, while retaining one independently reported test for each of
the 137 immutable Testatron truth files.

Validation passed with the original 145 regression outcomes:

```text
pytest tests/regression -q     # 145 passed
pytest -m regression -q        # 145 passed, 116 deselected
pytest --collect-only -q       # 227/261 collected, 34 deselected
```

## Stage 2: Move IPOPT Artifact Roots (Complete 2026-10-02)

Move artifacts with Git history preserved:

```bash
git mv testatron/ipopt/cases testatron/ipopt/tests/tests
git mv testatron/ipopt/benchmarks testatron/ipopt/tests/benchmarks
```

Then update all operational references:

1. Change benchmark output-root declarations in
   [testatron/ipopt_characterization.py](ipopt_characterization.py)
   to `testatron/ipopt/tests/benchmarks/...`.
2. Update path assertions in
   [tests/test_ipopt_characterization.py](test_ipopt_characterization.py).
3. Update Testatron regeneration instructions and any artifact inspection or
   diff commands in [testatron/ipopt/README.md](testatron/ipopt/README.md).
4. Update other documentation, scripts, and generated evidence references.
   Preserve unreviewed generated content during the move; regenerate only
   path-derived evidence after focused runs prove it is necessary.
5. Do not change source `.emtgopt` files, SNOPT `.emtg` baselines, tutorial
   result packages, or NASA result packages.

`testatron/ipopt/tests/tests` is intentionally nested artifact data. It is not
Python test source; Python tests remain in the repository-level `tests/`
directory.

### Completion Record

The case artifacts now reside below `testatron/ipopt/tests/tests/cases` and
the benchmark artifacts below `testatron/ipopt/tests/benchmarks`. The moved
benchmark root contained a historical duplicate `benchmarks/` directory; it
was flattened so the registry and generated stage directories agree on the
documented paths.

The benchmark registry, default characterization output root, unit path
assertions, regeneration commands, and governing layout policy were updated.
Historical generated evidence still retains its original runtime path strings;
those records were deliberately not regenerated or rewritten. The focused
contract suite passed with `59 passed`, including provenance checks against the
moved benchmark stage directories. A repository search found no remaining live
references to the former artifact paths; the Stage 2 `git mv` commands above
remain as the historical migration procedure.

## Stage 3: Register Core Pytest Suites (Complete 2026-10-02)

Add these markers to [pytest.ini](pytest.ini):

```ini
ipopt_tests: Testatron IPOPT case characterization and validation
ipopt_benchmarks: IPOPT benchmark replay, refinement, and validation
```

Apply `ipopt_tests` only to the future Docker-backed, per-case suite that
replays each immutable SNOPT baseline and refines it with IPOPT. That suite
must compare the result directly against its adjacent SNOPT `.emtg` baseline.
Do not apply this marker to unit contracts for the runner itself. Apply
`ipopt_benchmarks` to tests that own TrackACSProp and OSIRIS benchmark
replay/refinement artifacts below `testatron/ipopt/tests/benchmarks`.

Keep existing markers such as `unit`, `integration`, `docker`,
`ipopt_backend`, and `solver_runtime`. The new markers express suite ownership;
they do not replace runtime requirements.

Both suites are core coverage. Do not add them to the opt-in deselection logic
in [tests/conftest.py](tests/conftest.py); only `tutorials` and
`clean_bootstrap` retain that behavior.

Focused commands are:

```bash
python -m pytest -m ipopt_tests
python -m pytest -m ipopt_benchmarks
```

Plain `pytest` must continue to collect both marker groups.

### Completion Record

`pytest.ini` now registers `ipopt_tests` and `ipopt_benchmarks` as additive
suite-ownership markers. The 59 characterization-runner contracts remain
`unit` tests only. They validate staging, parsing, classification, manifests,
and current benchmark helper behavior; they do not run EMTG across the
Testatron corpus and do not establish SNOPT/IPOPT agreement.

This distinction corrects an earlier misunderstanding: the runner contracts
were temporarily marked `ipopt_tests`, as though validating the runner meant
they exercised the Testatron IPOPT suite. They do not. The marker was removed
from those unit tests. `pytest -m ipopt_tests` intentionally selects no tests
until the per-case IPOPT-to-SNOPT runtime suite exists.

The six benchmark provenance/path guards and six Docker-backed TrackACS and
OSIRIS replay/refinement nodes carry `ipopt_benchmarks` in addition to their
existing unit, integration, Docker, IPOPT-backend, and solver-runtime markers.
The `ipopt_tests` marker is registered and reserved for its intended suite.
Its runtime implementation is explicitly owned by Stage 7, after Stages 5 and
6 establish dependency preflight and SNOPT/IPOPT agreement semantics.

Validation passed:

```text
pytest -m ipopt_benchmarks --collect-only -q # 12 selected
pytest -m ipopt_benchmarks -q                # 12 passed, 250 deselected
pytest --collect-only -q                      # 228/262 collected, 34 deselected
```

Stage 3 is complete: it establishes correct marker ownership without
misclassifying unit contracts as IPOPT-to-SNOPT corpus tests. Stage 7 completes
the deferred per-case `ipopt_tests` runtime suite.

## Stage 4: Prove the Layout Change Is Stable (Complete 2026-10-02)

Before adding dependency resolution or changing comparison semantics, repeat
the Stage 0 commands against the moved paths.

1. Confirm Git recognizes the directory changes as renames rather than copies.
2. Search the repository for operational references to the old paths:

   ```bash
   rg 'testatron/ipopt/(cases|benchmarks)' \
     --glob '!testatron/ipopt/tests/**'
   ```

3. Confirm collection behavior:

   ```bash
   python -m pytest --collect-only -q
   python -m pytest --collect-only -m ipopt_tests -q
   python -m pytest --collect-only -m ipopt_benchmarks -q
   ```

4. Repeat all Stage 0 benchmark probes. Compare exit status, native IPOPT
   diagnostics, accepted checks, numerical comparison values, and source/truth
   hashes with the baseline report.
5. Repeat representative and full case characterization runs. Compare case
   identifiers, manifest counts, classifications, result content, and hashes
   with Stage 0.
6. Rerun characterization contracts:

   ```bash
   python -m pytest tests/test_ipopt_characterization.py -q
   ```

A path-only migration must not change numerical results. Treat any difference
as a relocation regression until its root cause is demonstrated.

### Completion Record

Git retained the moved IPOPT artifact roots as renames, and no live code or
documentation reference remains to the former roots. The six benchmark stages
passed after relocation through `pytest -m ipopt_benchmarks -q` (`12 passed`,
including six fast artifact guards). A fresh representative and full 137-case
characterization capture ran from the relocated artifact root using the Stage 0
image and build volume. Immutable source options and SNOPT truths retained
matching SHA-256 hashes before and after both captures (274 records).

The representative capture differed only at the 300-second timeout boundary:
`solveroptions_ACEfeasibility` completed in 297.47 seconds rather than timing
out at 300.01 seconds. The full capture retained the Stage 0 timeout category
totals except `transcription_tests/SundmanCoastPhase_EMintercept`, which changed
from `reviewable` to `infeasible`. Its staged options and compatibility records
were byte-identical to Stage 0, and a fresh one-case retry reproduced the
infeasible result. This is solver reproducibility behavior, not an artifact
layout defect; Stage 6 owns its resolution.

## Stage 5: Make Dependencies Explicit

After layout stability is established:

1. Add a versioned dependency manifest for externally supplied NAIF kernels.
   Each record contains required filename, canonical source URL for provenance,
   SHA-256, and expected path under `testatron/universe/ephemeris_files`.
2. Add a no-network preflight command to
   [testatron/ipopt_characterization.py](ipopt_characterization.py).
   It validates every dependency before EMTG executes and reports missing or
   checksum-mismatched resources with exact remediation details.
3. Do not download kernels automatically. Operators provide verified resources
   at their documented paths.
4. Refactor `prepare_case()` into resolve, stage, and write steps. Preserve:
   - Legacy NLSII mapping while retaining `LaunchVehicleKey`.
   - The table-independent throttle-table mapping guard.
   - `DoesNotExist.grv` for zero-order gravity.
   - Repository-relative, portable provenance in `compatibility.json`.
5. Add contracts for manifest parsing, absent/corrupt resources, mapping
   eligibility, path rewriting, gravity behavior, and aggregate preflight
   status.
6. Run preflight for all cases. Resolve resources legitimately; do not invent
   hardware or use placeholders. The gate is zero `dependency_blocked` cases
   for the approved portable corpus.

### 5.1: Initial Dependency Preflight (Complete 2026-10-06)

Versioned kernel manifest, no-network kernel and per-case preflight, and
portable preflight evidence were implemented for all 137 Testatron cases. The
approved compatibility policy maps only the Testatron default library's
`Falcon_9_FT_(RTLS)` request to the tracked public
`HardwareModels/default.emtg_launchvehicleopt` definition while retaining the
requested key. Prepared general-case options serialize repository paths through
Docker's `/repo` mount, avoiding host-path and whitespace dependencies.

Validation completed with `pytest tests/test_ipopt_characterization.py -q`
(`64 passed`) and `python testatron/ipopt_characterization.py --preflight`,
which reported 137 acceptable cases and zero blocked cases.

| Classification       |                    Stage 0 | Recent run |   Change |
| -------------------- | -------------------------: | ---------: | -------: |
| `reviewable`         |                         69 |         81 |      +12 |
| `infeasible`         |                          5 |         25 |      +20 |
| `parse_failed`       |                          8 |         10 |       +2 |
| `dependency_blocked` |                         54 |         15 |      -39 |
| `topology_changed`   |                 not listed |          6 |       +6 |
| `timed_out`          | present, count unspecified |          0 | improved |
### 5.2: Runtime Dependency Closure (Open)

The 2026-10-06 Docker characterization smoke run completed all 137 cases but
exposed a gap in the original preflight scope. Its manifest contained 15
`dependency_blocked` results despite preflight reporting 137 acceptable cases:

- `Earth_MAGIC.emtg_universe`: 2 cases.
- `Sun_SaturnOrientation.emtg_universe`: 6 cases.
- `snapier_multistage.emtg_spacecraftopt`: 2 cases.
- `default.emtg_powersystemsopt`: 2 cases.
- `spacecraft_LT_multiStage_spacecraftFile.emtg_spacecraftopt`: 2 cases.
- `spacecraft_LT_spacecraftFile.emtg_spacecraftopt`: 1 case.

Extend the no-network preflight and staged preparation path to validate every
journey's `<journey_central_body>.emtg_universe` resource and every nested
spacecraft, power-system, propulsion-system, and throttle dependency actually
loaded by EMTG. The full 137-case corpus remains the verification target; do
not exclude cases solely because their historical runtime resources are absent.
Preserve immutable source options and SNOPT baselines. A replacement may link
to an existing tracked input or be newly created, but it must be case-scoped,
versioned, hashed, and recorded in `compatibility.json` with its source or
construction rationale. Never silently substitute hardware or universe data.

Treat every replacement as provisional until Stage 6 replay and refinement
evidence demonstrates that it preserves the immutable SNOPT baseline's
decision schema, topology, feasibility, and approved comparison values. A
replacement that cannot meet those comparisons remains a documented
`mismatch_snopt` or `dependency_blocked` outcome, not a verification pass.

### Full-Corpus Execution Policy

Every preflight and Docker characterization run selects all 137 cases. The
Stage 5.2 characterization established that five unavailable resource paths
blocked 13 cases: `Earth_MAGIC.emtg_universe` blocked 2,
`Sun_SaturnOrientation.emtg_universe` blocked 6,
`snapier_multistage.emtg_spacecraftopt` blocks 2,
`spacecraft_LT_multiStage_spacecraftFile.emtg_spacecraftopt` blocks 2, and
`spacecraft_LT_spacecraftFile.emtg_spacecraftopt` blocks 1. Their preflight
records retain the owning case, missing source dependency, and remediation
status, but they are never omitted from a 137-case run.

Rerun the full Docker characterization after every dependency change. Stage 5
is complete only when preflight and runtime agree for all 137 cases: every case
has resolved staged dependencies and the characterization manifest reports zero
`dependency_blocked` cases.

The latest full characterization, retained at
`/tmp/emtg-ipopt-137-stage52-rerun`, validated the key-aware composite
hardware mapping with 83 `reviewable` cases, 25 `infeasible`, 10
`parse_failed`, 13 `dependency_blocked`, 6 `topology_changed`, and zero
`process_failed` or `timed_out` cases. The previous fresh all-137 run had 82
`reviewable` and 11 `parse_failed` cases; `spacecraft_LT_powerFile` changed
from `parse_failed` to `reviewable`, which is a Stage 6 reproducibility item.
The focused Docker smoke run for `spacecraft_LT_powerFile` and
`spacecraft_LT_propFile` classified both as `reviewable` with no dependency,
parse, timeout, or process failures. The runner contracts passed with 67 tests
and all six `ipopt_benchmarks` stages passed.

| Classification       |                    Stage 0 | Recent run |
| -------------------- | -------------------------: | ---------: |
| `reviewable`         |                         69 |         83 |
| `infeasible`         |                          5 |         25 |
| `parse_failed`       |                          8 |         10 |
| `dependency_blocked` |                         54 |         13 |
| `topology_changed`   |                 not listed |          6 |
| `timed_out`          | present, count unspecified |          0 |

### 5.3: Resolve Historical Resources

Keep the full 137-case corpus mandatory for every preflight and Docker
characterization; do not create an execution filter or exclusion selection.

1. Create a tracked, versioned replacement-resource manifest for
   `Earth_MAGIC.emtg_universe`, `Sun_SaturnOrientation.emtg_universe`,
   `snapier_multistage.emtg_spacecraftopt`,
   `spacecraft_LT_multiStage_spacecraftFile.emtg_spacecraftopt`, and
   `spacecraft_LT_spacecraftFile.emtg_spacecraftopt`. Each record identifies
   affected case IDs, the original requested path, replacement path or
   construction source, SHA-256, rationale, and review status.
2. For each missing universe file, link an existing tracked model or construct
   a case-scoped replacement that preserves required body lists, central-body
   parameters, gravity/ephemeris references, and state/frame semantics.
3. For each missing spacecraft file, link or construct a case-scoped model
   from explicitly identified tracked power, propulsion, throttle, tank, and
   stage definitions. Validate and hash every nested dependency.
4. Extend the shared resolution path used by `preflight_case_dependencies()`
   and `prepare_case()` so they apply the same case-scoped replacement manifest
   and write every substitution to `compatibility.json`. Source `.emtgopt`
   files and immutable SNOPT `.emtg` baselines remain unchanged.
5. Add unit contracts for replacement eligibility, checksums, nested
   dependencies, preflight records, and staged `/repo` execution paths. Add
   Docker smoke coverage for each replacement family before the broad rerun.
6. After every replacement change, run runner contracts, all six benchmark
   stages, no-network all-137 preflight, and the full all-137 Docker
   characterization. Retain artifacts and compare classifications with
   `/tmp/emtg-ipopt-137-stage52-rerun`.
7. Do not promote a replacement because EMTG runs. Stage 5.3 completes only
   when all 137 cases have resolved staged dependencies and the full manifest
   has zero `dependency_blocked` outcomes. Stage 6 must still establish replay
   and IPOPT-refinement agreement with immutable SNOPT baselines.

The first case-scoped universe replacement is
`Earth_MAGIC_AerodynamicDrag.emtg_universe`, SHA-256
`2cf5480819e33847fae018dcd86afdd77cf120bae2b29c5b891707ff182ed1dc`.
It is reconstructed from the tracked `Earth_v9` body menu with the immutable
AerodynamicDrag baseline's Earth constants, and is staged under the requested
`Earth_MAGIC.emtg_universe` name only for
`journey_options/AerodynamicDrag_EarthOrbit_Maneuver`. The focused resolver
contracts passed (`3 passed`; full runner suite: `69 passed`), and the
2026-10-06 Docker smoke retained at
`baseline-artifacts/stage5-earth-magic-aerodynamic` classified that case as
`reviewable`. It remains provisional pending Stage 6 comparison to immutable
SNOPT truth.

`journey_options/park_to_SOI_FBLT` remains unresolved. Its original universe
requires `GatewayNRHO` SPICE ID `-60000`, which is absent from the pinned
kernel pool; it must not inherit the AerodynamicDrag replacement. Consequently
the current case-scoped manifest has one resolved provisional Earth-MAGIC case
and one Earth-MAGIC dependency-blocked case. No all-137 rerun has yet been
recorded after this narrow replacement; the required complete rerun remains
pending resolution of every historical resource family.

## Stage 6: Enforce IPOPT-to-SNOPT Agreement

Implement and enforce the two stages defined in
[tests.readme.md](tests.readme.md):

1. **Replay:** evaluate the decision vector archived in the immutable SNOPT
   baseline with `run_inner_loop 0`. Neither SNOPT nor IPOPT executes. The
   replay validates the current transcription, staged dependencies, and schema.
2. **Refinement:** after replay succeeds, run IPOPT from that aligned seed and
   compare directly against the immutable SNOPT baseline.

Comparison evidence must include objective, total delta-v, flight time, final
mass, departure/arrival state deltas, topology, decision schema, feasibility,
native IPOPT exit, iteration count, terminal constraint violation, tolerances,
and input provenance.

Introduce and enforce these classifications:

- `matched_snopt`: native IPOPT success and every approved comparison passes.
- `mismatch_snopt`: IPOPT ran but differs materially from the SNOPT baseline.
- `dependency_blocked`, `timed_out`, `process_failed`, `parse_failed`,
  `infeasible`, and `topology_changed`: non-pass outcomes requiring specific
  investigation.

Do not accept a chaperone-restored incumbent as native IPOPT success. Do not
weaken a tolerance for an individual case. Calibrate tolerance policies using a
fixed representative subset and record every approved change in code or a
versioned manifest.

Before accepting any per-case result, make the IPOPT pipeline reproducible
under the pinned toolchain. Investigate and eliminate or explicitly control
solver-state inputs that can change a seeded run, including MBH seed handling,
threading, random-device initialization, and iteration/time-limit behavior.
Add a repeat-run contract for a representative seeded case and for
`transcription_tests/SundmanCoastPhase_EMintercept`; it must demonstrate stable
classification and agreed comparison values across fresh artifact directories.
Do not classify a run as `matched_snopt` while identical staged inputs can
produce materially different outcomes.

Add unit contracts for comparison dimensions, objective sense, tolerance
boundaries, native exits, and manifest aggregation. Add Docker-backed smoke
coverage for a public-NLSII case and a SPICE-dependent case.

Add a Docker-backed pytest module with one parameterized node for each approved
`testatron/tests/<group>/<case>.emtgopt` input. Mark every node with
`ipopt_tests`, `integration`, `docker`, `ipopt_backend`, and `solver_runtime`.
`pytest -m ipopt_tests -q` must execute the complete approved corpus, report
each case independently, and fail for any outcome other than `matched_snopt`.
The 59 runner contracts remain selected only by `unit`.

## Stage 7: Complete the Deferred Stage 3 IPOPT Test Suite

After Stages 5 and 6 provide dependency preflight and direct SNOPT/IPOPT
comparison semantics, complete the outstanding Stage 3 requirement:

1. Register the parameterized per-case Docker test module as the sole owner of
   `ipopt_tests`; do not add the marker to runner unit contracts.
2. Parameterize one independently reported pytest node for every approved
   `testatron/tests/<group>/<case>.emtgopt` source and its adjacent immutable
   SNOPT `.emtg` baseline.
3. Mark every node `ipopt_tests`, `integration`, `docker`, `ipopt_backend`,
   and `solver_runtime`.
4. Each node must preflight dependencies, replay the SNOPT seed, refine it with
   IPOPT, write unreviewed artifacts under `testatron/ipopt/tests/tests`, and
   fail unless the final classification is `matched_snopt`.
5. Validate the completed suite:

   ```bash
   pytest -m ipopt_tests --collect-only -q
   pytest -m ipopt_tests -q
   pytest --collect-only -q
   ```

Stage 3 is complete only after `pytest -m ipopt_tests -q` runs the complete
approved Testatron corpus as independently reported IPOPT-to-SNOPT comparisons.

## Stage 8: Final Verification Gate

Run the complete core selections after all implementation work:

```bash
python -m pytest -m unit
python -m pytest -m regression
python -m pytest -m ipopt_benchmarks
python -m pytest -m ipopt_tests
python -m pytest --collect-only -q
```

Run the full manually driven benchmark and case corpus as well. Archive final
manifests, commands, image identities, timings, source/truth hashes, and
comparison evidence.

This plan is complete only when:

1. Moved benchmark and case roots are stable relative to Stage 0.
2. Plain pytest includes both core marker groups.
3. Approved portable cases pass preflight with no unresolved dependencies.
4. Each approved comparable case is `matched_snopt`.
5. Immutable SNOPT sources and baselines retain their original hashes.

Only after these conditions hold may work begin on
[docker_deployment.readme.md](docker_deployment.readme.md). Do not
combine Docker lifecycle refactoring with this verification work.

## Runtime Expectations

Collection checks and unit contracts should complete in seconds to minutes.
Warm single Docker probes can take several minutes. Cold runs also provision an
image and native build and can take tens of minutes. Establish actual full-suite
duration in Stage 0, use `--resume` only for retained case outputs, and set CI
limits only after the measured baseline is available.