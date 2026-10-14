
How to baseline?

# Purpose

This plan makes the complete `testatron/tests` corpus executable with the open-source IPOPT backend and uses the committed SNOPT-generated `.emtg` files as the immutable numerical baseline.

IPOPT is not accepted merely because it produces a feasible result. For each comparable case, the IPOPT result must agree with the corresponding SNOPT result within an explicit, reviewed numerical contract. The committed SNOPT options and `.emtg` files are never overwritten, regenerated, or promoted from an IPOPT run.

Run the commands in this document from the repository root.

# Testing workflow

Tests against a pinned Docker image already available.

| #   | Test                                              | Command                                                                                                        | Runtime information                              | Docker required |
| --- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | --------------- |
| 1   | Run clean bootstrap                               |                                                                                                                |                                                  | Yes             |
| 2   | Run collection sanity                             | python -m pytest --collect-only -q                                                                             | 285/319 tests collected (34 deselected) in 0.13s | No              |
| 3   | Run unit tests                                    | python -m pytest -m unit                                                                                       | 114 passed, 205 deselected in 2.82s              | No              |
| 4   | Run regression tests                              | python -m pytest -m regression                                                                                 | 145 passed, 174 deselected in 1.49s              | No              |
| 5   | Run IPOPT characterization contracts              | python -m pytest tests/test_ipopt_characterization.py -q                                                       | 113 passed in 1.22s                              | No              |
|     |                                                   |                                                                                                                | < 10 seconds                                     |                 |
| 6   | Run focused IPOPT integration (benchmarks) checks | EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-benchmarks" \<br><br>python -m pytest -m ipopt_benchmarks -q | 12 passed, 307 deselected in 33.78s              | Yes             |
| 7   | Run focused IPOPT integration (tests) checks      | EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-tests" \<br><br>python -m pytest -m ipopt_tests -q           | 3 passed, 316 deselected in 19.22s               | Yes             |
| 8   | Run full integration suite                        | EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/integration" \<br><br>python -m pytest -m integration -q           | 26 passed, 293 deselected in 658.13s (0:10:58)   | Yes             |
|     |                                                   |                                                                                                                | < 15 min                                         | Yes             |
| 9   | Run 137 corpus tests                              | Manual multi step process.                                                                                     | < 60 min                                         | Yes             |
| 10  | Run 33 tutorial tests                             | Manual multi step process.                                                                                     | < 60 min                                         | Yes             |

1
Docker required. Manual multi step process of less than an hour from start to finish with everything passing.

2,3,4,5
Docker NOT required. Estimated runtime order of magnitude seconds.

```zsh
python -m pytest --collect-only -q

python -m pytest -m unit

python -m pytest -m regression

python -m pytest tests/test_ipopt_characterization.py -q
```

6,7,8
Docker required. Estimated runtime order of magnitude minutes:

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-benchmarks" \ python -m pytest -m ipopt_benchmarks -q

EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-tests" \ python -m pytest -m ipopt_tests -q

EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/integration" \ python -m pytest -m integration -q
```

9, 10
Docker required. Manual multi step process of less than an hour from start to finish with everything passing.

## 2. Run collection sanity

`--collect-only` executes no tests and does not invoke Docker, EMTG, or IPOPT. It confirms that the expected test modules, markers, and test-discovery configuration are visible to pytest.

Run it at the beginning to detect missing coverage and again at the end to record the final collection state.

Terminal command:

```zsh
python -m pytest --collect-only -q
```

Example output:
```zsh
% python -m pytest --collect-only -q
tests/integration/test_baselining.py::test_baselining_repeatability_in_pinned_toolchain[global_mission_options/globalmissionoptions_MGALT_DLAbounds]
tests/integration/test_baselining.py::test_baselining_repeatability_in_pinned_toolchain[transcription_tests/SundmanCoastPhase_EMintercept]
tests/integration/test_baselining.py::test_baselining_cli_writes_fixed_mirrored_layout
.
.
.
tests/test_ipopt_characterization.py::test_benchmark_provenance_hashes_current_sources
tests/test_ipopt_characterization.py::test_benchmark_provenance_rejects_unknown_stage
tests/test_ipopt_characterization.py::test_committed_provenance_matches_registry_and_directory

285/319 tests collected (34 deselected) in 0.12s
```

The **34 deselected tests are exactly:**

| Opt-in group                       |  Count | Why excluded by default                                                                |
| ---------------------------------- | -----: | -------------------------------------------------------------------------------------- |
| `clean_bootstrap`                  |      1 | Rebuilds the Docker toolchain with `--no-cache`; intentionally expensive.              |
| `tutorials` replay tests           |     17 | Docker-backed verification of the current tutorial input/reference packages.           |
| `tutorials` IPOPT-refinement tests |     16 | Docker-backed IPOPT refinement verification for tutorial cases that permit refinement. |
| **Total**                          | **34** |                                                                                        |
|                                    |        |                                                                                        |
## 3. Run unit tests

This checks isolated Python/C++ contract behavior without deliberately running the Docker mission corpus.

Terminal command:
```zsh
python -m pytest -m unit
```

Example output:
```zsh
% python -m pytest -m unit
======================================================================================================================== test session starts ========================================================================================================================
platform darwin -- Python 3.13.1, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator
configfile: pytest.ini
testpaths: tests
collected 319 items / 205 deselected / 114 selected                                                                                                                                                                                                                 

tests/test_cpp_contracts.py .                                                                                                                                                                                                                                 [  0%]
tests/test_ipopt_characterization.py .................................................................................................................                                                                                                        [100%]

================================================================================================================ 114 passed, 205 deselected in 2.82s ================================================================================================================
```

## 4. Run regression tests

This is the important source/baseline integrity suite. It exercises frozen Testatron and mission parsing/comparison behavior, including the immutable corpus.

Terminal command:

```zsh
python -m pytest -m regression
```

Example output:

```zsh
% python -m pytest -m regression
======================================================================================================================== test session starts ========================================================================================================================
platform darwin -- Python 3.13.1, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator
configfile: pytest.ini
testpaths: tests
collected 319 items / 174 deselected / 145 selected                                                                                                                                                                                                                 

tests/regression/test_comparatron.py ...                                                                                                                                                                                                                      [  2%]
tests/regression/test_mission_options.py ..                                                                                                                                                                                                                   [  3%]
tests/regression/test_mission_parser.py ............................................................................................................................................                                                                          [100%]

================================================================================================================ 145 passed, 174 deselected in 1.49s ================================================================================================================

```

## 5. Run IPOPT characterisation contracts

This checks staging, compatibility mappings, result serialization, comparison policy, promotion eligibility, and current-state verification logic.

Terminal command:

```zsh
python -m pytest tests/test_ipopt_characterization.py -q
```

Example output:

```zsh
% EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-benchmarks" \

python -m pytest -m ipopt_benchmarks -q
............                                                                                                                                                                                                                                                  [100%]
12 passed, 307 deselected in 33.78s
```

## 6,7. Run focused IPOPT integration checks

### Run `ipopt_benchmarks`

`ipopt_benchmarks` runs the established TrackACS and OSIRIS replay/refinement checks in the pinned Linux IPOPT toolchain. It confirms that known, curated mission packages still execute and preserve their expected solver and mission-comparison behavior. Use a separate artifact root because these are benchmark diagnostics, not Testatron corpus evidence.

Terminal command:

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-benchmarks" \

python -m pytest -m ipopt_benchmarks -q
```

Example output:

```zsh
% python -m pytest tests/test_ipopt_characterization.py -q
.................................................................................................................                                                                                                                                             [100%]
113 passed in 1.22s
(.venv) jacoconradie@Panda-Mac evolutionary-mission-trajectory-generator % EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-benchmarks" \

python -m pytest -m ipopt_benchmarks -q
............                                                                                                                                                                                                                                                  [100%]
12 passed, 307 deselected in 33.78s
```

### Run `ipopt_tests`

The `ipopt_tests` marker includes Docker-backed repeatability and launcher coverage, so it can be slower:

Terminal command:

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-tests" \

python -m pytest -m ipopt_tests -q
```

Example output:

```zsh
% EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-tests" \

python -m pytest -m ipopt_tests -q
...                                                                                                                                                                                                                                                           [100%]
3 passed, 316 deselected in 19.22s
```

## 8. Run full integration suite

### Run `integration`

`integration` exercises the complete Docker/toolchain boundary: image availability, dependency discovery, CMake policy, native compilation, EMTG execution, and selected mission workflows. It provides deployment-level confidence that a third party can build and operate EMTG/IPOPT in the pinned container environment. Run it only after the baselining corpus is complete, and keep its artifacts separate from corpus evidence.

Terminal command:

Only run this after the above pass, and keep artifacts separate:

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/integration" \

python -m pytest -m integration -q
```

Example output:

```zsh
% EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/integration" \

python -m pytest -m integration -q
..........................                                                                                                                                                                                                                                    [100%]
26 passed, 293 deselected in 658.13s (0:10:58)
```



## 9. Run 137 corpus tests

The 137 corpus tests in [[baselining_commands#Corpus tests|Corpus tests]]. Run the following terminal commands
### Create the terminal function

```zsh
baselining_case() {
	EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/tests" \
	python -m pytest tests/integration/test_baselining.py -q \
	-k baselining_cli_writes_fixed_mirrored_layout \
	--baselining-filter "$1"
}
```

### Run the 137 cases under the [[baselining_commands#Complete list of tests| complete list of 137 corpus baselining tests]].

```zsh
baselining_case 'global_mission_options/globalmissionoptions_MGALT_DLAbounds'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_RLAbounds'
...
baselining_case 'transcription_tests/PSFB_EMintercept'
baselining_case 'transcription_tests/SundmanCoastPhase_EMintercept'
```

```zsh
.                                                                                                                                                                                                                                                             [100%]
1 passed, 2 deselected in 5.63s
.                                                                                                                                                                                                                                                             [100%]
1 passed, 2 deselected in 6.63s
.                                                                                                                                                                                                                                                             [100%]
1 passed, 2 deselected in 5.46s
```

Classification summary.
```zsh
python -c 'import json; from collections import Counter; summary=json.load(open("testatron/ipopt/tests/tests/baselining/baselining-summary.json")); print(summary["case_count"]); print(dict(sorted(Counter(case["classification"] for case in summary["cases"]).items())))'
```

```zsh
% python -c 'import json; from collections import Counter; summary=json.load(open("testatron/ipopt/tests/tests/baselining/baselining-summary.json")); print(summary["case_count"]); print(dict(sorted(Counter(case["classification"] for case in summary["cases"]).items())))'
137
{'matched_snopt': 5, 'mismatch_snopt': 132}
```

### Generate the corpus summary

```zsh
python testatron/ipopt_characterization.py --summarize-baselining --output-root "$PWD/testatron/ipopt/tests/tests"
```

```zsh
% python testatron/ipopt_characterization.py --summarize-baselining --output-root "$PWD/testatron/ipopt/tests/tests"

Wrote baselining summary for 137 case(s): */evolutionary-mission-trajectory-generator/testatron/ipopt/tests/tests/baselining/baselining-summary.json
```

### Regenerate the human-readable decision-log report from the new artifacts

```zsh
python testatron/ipopt_characterization.py \
	--write-baselining-decision-log \
	--output-root "$PWD/testatron/ipopt/tests/tests" \
	--decision-log-output \
	"$PWD/docs/3_NLP_Solvers/IPOPT/baselining_case_decision_log.md"
```

```zsh
% python testatron/ipopt_characterization.py \
        --write-baselining-decision-log \
        --output-root "$PWD/testatron/ipopt/tests/tests" \
        --decision-log-output \
        "$PWD/docs/3_NLP_Solvers/IPOPT/baselining_case_decision_log.md"
Wrote baselining decision log for 137 case(s): */evolutionary-mission-trajectory-generator/docs/3_NLP_Solvers/IPOPT/baselining_case_decision_log.md
```

To inspect the generated decision log

```zsh
git --no-pager diff -- \
	docs/3_NLP_Solvers/IPOPT/baselining_case_decision_log.md
```

No output means the regenerated report matches the checked-in/generated prior version exactly. A diff shows which case evidence, mappings, mismatch values, or refinement record changed.

The narrative decision record should remain separate: do **not** overwrite `baselining_decision_log.md` merely because the generated companion report was refreshed.

#### If you want an exact before-versus-after summary diff next time

Before rerunning the corpus, snapshot the old generated output somewhere outside the canonical evidence tree:

```zsh
mkdir -p test-artifacts/baselining-comparisons

cp testatron/ipopt/tests/tests/baselining/baselining-summary.json \
	test-artifacts/baselining-comparisons/baselining-summary.before.json
```

After the rerun and summary generation:

```zsh
diff -u \
	test-artifacts/baselining-comparisons/baselining-summary.before.json \
	testatron/ipopt/tests/tests/baselining/baselining-summary.json
```
### Verify the fresh 137-case results against the **existing** reviewed current-state reference.

```zsh
python testatron/ipopt_characterization.py \
	--verify-baselining \
	--output-root "$PWD/testatron/ipopt/tests/tests" \
	--verification-reference \
	"$PWD/testatron/ipopt/tests/baselining_verification.json" \
	--verification-report-output \
	"$PWD/testatron/ipopt/tests/tests/baselining/baselining_verification_report.json"
```

```zsh
% python testatron/ipopt_characterization.py \
        --verify-baselining \
        --output-root "$PWD/testatron/ipopt/tests/tests" \
        --verification-reference \
        "$PWD/testatron/ipopt/tests/baselining_verification.json" \
        --verification-report-output \
        "$PWD/testatron/ipopt/tests/tests/baselining/baselining_verification_report.json"
Baselining verification passed for 137 case(s): */evolutionary-mission-trajectory-generator/testatron/ipopt/tests/tests/baselining/baselining_verification_report.json
```

To inspect the report explicitly after running verification:

```zsh
python - <<'PY'
import json
from collections import Counter
from pathlib import Path

path = Path("testatron/ipopt/tests/tests/baselining/baselining_verification_report.json")
report = json.loads(path.read_text(encoding="utf-8"))
statuses = Counter(case["status"] for case in report["cases"])

print(f'case_count: {report["case_count"]}')
print(f'acceptable: {report["acceptable"]}')
print(f"statuses: {dict(sorted(statuses.items()))}")

for case in report["cases"]:
	if case["status"] != "matched":
		print(f'{case["case_id"]}: {case["status"]}')
PY
```

```zsh
% python - <...
case_count: 137
acceptable: True
statuses: {'matched': 137}
```

## 10. Run 33 tutorial tests


Terminal command:

```zsh

```

Example output:

```zsh

```

# Baselining workflow

See [[baselining_commands]].

The IPOPT Testatron Baselining workflow executes the immutable `testatron/tests` corpus with the open-source IPOPT backend while preserving each adjacent SNOPT-generated `.emtg` file as immutable historical evidence. The workflow answers two separate questions:

1. **Immutable-SNOPT comparison:** does a staged replay and, when eligible,
	IPOPT refinement agree with the historical SNOPT result?

2. **Current-state regression verification:** does fresh evidence reproduce the
	reviewed behavior of the current EMTG/IPOPT environment?

The first is a diagnostic comparison to historical truth. The second is the regression gate for the currently supported Docker toolchain. A stable `mismatch_snopt` can be expected current-state behavior; it is not a solver pass against SNOPT, nor a regression by itself.
## Immutable Inputs and Evidence Layout

| Root | Contents |
| --- | --- |
| `testatron/tests/<group>/<case>.emtgopt` | Immutable Testatron mission-options source. |
| `testatron/tests/<group>/<case>.emtg` | Immutable historical SNOPT baseline. |
| `testatron/ipopt/tests/tests/baselining/<group>/<case>/` | Replaceable staged runtime evidence, attempts, logs, comparisons, and summaries. |
| `testatron/ipopt/tests/tests/<group>/<case>/` | Curated promoted output for an explicitly approved stable `matched_snopt` case. |
| `testatron/ipopt/tests/baselining_verification.json` | Reviewed current-state reference for all 137 cases. |
| `testatron/ipopt/tests/baselining_verification_policy.json` | Versioned numeric policy used only for current-state verification. |

The nested `tests/tests` path is artifact data, not Python test source. Python
tests remain below the repository-level `tests/` directory.

## Runtime Staging

The Docker runner mounts the repository read-only and writes only staged,
case-scoped artifacts. `prepare_case()` copies and adapts runtime options and
dependencies below the evidence root; it never alters the immutable source
pair.

Legacy resources may need public runtime mappings. Every mapping, replacement
resource, and seed-bound exception is recorded in the case
`compatibility.json`, including source, replacement, reason, and provenance.
The completed corpus has no final dependency-blocked cases, but that does not
mean staged public resources are declared numerically equivalent to historical
SNOPT resources. Their observable effect remains part of the recorded replay
comparison.

## Replay and Refinement

Each case has two fresh attempts. `repeatability.json` compares them and a case
is accepted as stable only when its recorded classification and approved values
agree.

### SNOPT-seed replay

The runner extracts the immutable SNOPT decision vector, aligns it to the
current schema, injects it into staged options, and uses `run_inner_loop=0`.
Neither SNOPT nor IPOPT executes in this stage. Replay tests the current EMTG
transcription, staged resources, decision schema, topology, and numerical
state against the immutable SNOPT result.

Replay records objective, deterministic delta-v, flight time, final mass,
journey endpoints, topology, and schema checks. A replay mismatch is evidence
that current runtime behavior differs from the historical baseline; refinement
is not run for that case.

### IPOPT refinement

Only an acceptable replay proceeds to IPOPT refinement with
`run_inner_loop=3`, using the same aligned decision seed. Refinement records
the native IPOPT exit, iterations, feasibility, objective, totals, endpoint
states, topology, and decision schema.

`matched_snopt` requires stable accepted replay, accepted native IPOPT
refinement, and all approved immutable-SNOPT comparisons. `mismatch_snopt`
means the staged case completed but does not meet that historical agreement;
it remains retained diagnostic evidence rather than a promoted result.

## Tolerance Boundaries

Immutable-SNOPT replay and refinement use their own reviewed comparison
policies. The replay contract compares scalar mission metrics, topology,
schema, and endpoint states. Refinement additionally requires native IPOPT
success and objective agreement using a relative $10^{-6}$ and absolute
$10^{-10}$ band.

The refinement decision vector has a separate $10^{-11}$ absolute in-bound
check. It is not a universal equality tolerance for objectives, totals, or
endpoint states.

Current-state verification does not reuse or relax any immutable-SNOPT policy.
It uses the independent, versioned numeric tolerances in
`testatron/ipopt/tests/baselining_verification_policy.json` to compare fresh
evidence with the reviewed current-state reference.

## Completed Corpus State

The reviewed corpus contains 137 immutable source/SNOPT pairs. The two-attempt
baselining run is stable for every case:

| Classification | Count | Meaning |
| --- | ---: | --- |
| `matched_snopt` | 5 | Replay and IPOPT refinement meet the immutable-SNOPT agreement policy. |
| `mismatch_snopt` | 132 | Replay differs from the immutable SNOPT baseline; refinement is not run. |
| `topology_changed`, `parse_failed`, `dependency_blocked`, `process_failed`, `timed_out` | 0 | No final classifications in the completed corpus. |

The recurring long Earth-Mars endpoint difference remains an unresolved
historical-environment diagnostic, most likely involving ephemeris, kernel, or
toolchain provenance. Do not change SPICE, propagation, or numerical
tolerances to force immutable-SNOPT agreement.

The generated per-case record is
[`baselining_case_decision_log.md`](baselining_case_decision_log.md). The
manual review ledger is [`baselined_checklist.md`](baselined_checklist.md).

## Current-State Verification

The reference records the expected present EMTG/IPOPT result for every case,
including expected `mismatch_snopt` outcomes. It contains immutable input
hashes, repeatability, runtime compatibility records, replay state, and,
where refinement ran, native IPOPT exit and numerical snapshots.

Ordinary baselining must never overwrite the reference. Writing or refreshing
`baselining_verification.json` is an explicit review and acceptance action.
Verification is artifact-only: it does not run EMTG and exits nonzero for
numeric drift, changed topology, changed execution state, missing evidence, or
unstable attempts.

See [`baselining_commands.md`](baselining_commands.md) for the reference-write
and verification commands, and
[`ipopt.readme.md`](ipopt.readme.md) for the Docker toolchain.

## Promotion and Review
 Promotion is a separate manual operation. It may copy only reviewed, stable `matched_snopt` evidence into the curated case root; it never replaces the immutable SNOPT pair. A completed or current-state-matched `mismatch_snopt` case is not eligible for promotion.

The baselining summary is a compact generated index. The decision log and verification reference are the authoritative detailed records. Do not infer promotion or README approval merely from an evidence directory existing.

## Python Test Coverage
 `ipopt_benchmarks` covers benchmark artifact behavior. The runner contracts are ordinary unit tests and validate staging, comparison, serialization, promotion eligibility, and current-state verification behavior.

`ipopt_tests` remains reserved for a future Docker-backed per-case pytest suite. Its absence does not weaken the completed artifact-based current-state verification workflow. Any future runtime suite must verify against the reviewed current-state reference and retain immutable-SNOPT comparison as a separate diagnostic.
# Readme

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
