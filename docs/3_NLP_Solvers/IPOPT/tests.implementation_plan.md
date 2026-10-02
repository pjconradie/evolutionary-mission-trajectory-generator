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

## Stage 2: Move IPOPT Artifact Roots

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

## Stage 3: Register Core Pytest Suites

Add these markers to [pytest.ini](pytest.ini):

```ini
ipopt_tests: Testatron IPOPT case characterization and validation
ipopt_benchmarks: IPOPT benchmark replay, refinement, and validation
```

Apply `ipopt_tests` to Python tests that prepare, run, classify, compare, or
validate data below `testatron/ipopt/tests/tests`. Apply `ipopt_benchmarks` to
tests that own TrackACSProp and OSIRIS benchmark replay/refinement artifacts
below `testatron/ipopt/tests/benchmarks`.

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

## Stage 4: Prove the Layout Change Is Stable

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

Add unit contracts for comparison dimensions, objective sense, tolerance
boundaries, native exits, and manifest aggregation. Add Docker-backed smoke
coverage for a public-NLSII case and a SPICE-dependent case.

## Stage 7: Final Verification Gate

Run the complete core selections after all implementation work:

```bash
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