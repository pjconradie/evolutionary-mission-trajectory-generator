# Purpose



IPOPT is not accepted merely because it produces a feasible result. For each comparable case, the IPOPT result must agree with the corresponding SNOPT result within an explicit, reviewed numerical contract. The committed SNOPT options and `.emtg` files are never overwritten, regenerated, or promoted from an IPOPT run.

Run the commands in this document from the repository root.

# Testing workflow

Tests against a pinned Docker image already available.

| #   | Test                                              | Command                                                                                                        | Runtime information                                                                                  | Docker required |
| --- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------- |
| 1   | Run clean bootstrap                               |                                                                                                                |                                                                                                      | Yes             |
| 2   | Run collection sanity                             | python -m pytest --collect-only -q<br>python -m pytest --collect-only -q --tutorials                           | 327/362 tests collected (35 deselected) in 0.22s<br>34/376 tests collected (342 deselected) in 0.09s | No              |
| 3   | Run unit tests                                    | python -m pytest -m unit                                                                                       | 170 passed, 206 deselected in 10.08s                                                                 | No              |
| 4   | Run regression tests                              | python -m pytest -m regression                                                                                 | 145 passed, 231 deselected in 2.38s                                                                  | No              |
| 5   | Run IPOPT characterization contracts              | python -m pytest tests/test_ipopt_characterization.py -q                                                       | 169 passed in 9.96s                                                                                  | No              |
|     |                                                   |                                                                                                                | < 10 seconds                                                                                         |                 |
| 6   | Run focused IPOPT integration (benchmarks) checks | EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-benchmarks" \<br><br>python -m pytest -m ipopt_benchmarks -q | 12 passed, 364 deselected in 39.82s                                                                  | Yes             |
| 7   | Run focused IPOPT integration (tests) checks      | EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-tests" \<br><br>python -m pytest -m ipopt_tests -q           | 3 passed, 373 deselected in 10.60s                                                                   | Yes             |
| 8   | Run full integration suite                        | EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/integration" \<br><br>python -m pytest -m integration -q           | 26 passed, 350 deselected in 88.02s (0:01:28)                                                        | Yes             |
|     |                                                   |                                                                                                                | < 15 min                                                                                             | Yes             |
| 9   | Run 137 corpus tests                              | Manual multi step process.                                                                                     | < 60 min                                                                                             | Yes             |
| 10  | Run 33 tutorial tests                             | Manual multi step process.                                                                                     | < 60 min                                                                                             | Yes             |

1
Docker required. Manual multi step process of less than an hour from start to finish with everything passing.

2,3,4,5
Docker NOT required. Estimated runtime order of magnitude seconds.

```zsh
python -m pytest --collect-only -q
python -m pytest --collect-only -q --tutorials

python -m pytest -m unit

python -m pytest -m regression

python -m pytest tests/test_ipopt_characterization.py -q
```

6,7,8
Docker required. Estimated runtime order of magnitude minutes:

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-benchmarks" \
	python -m pytest -m ipopt_benchmarks -q

EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-tests" \
	python -m pytest -m ipopt_tests -q

EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/integration" \
	python -m pytest -m integration -q
```

9, 10
Docker required. Manual multi step process of less than an hour from start to finish with everything passing.

## 1. Run clean bootstrap

Not implemented yet.


## 2. Run collection sanity

`--collect-only` executes no tests and does not invoke Docker, EMTG, or IPOPT. It confirms that the expected test modules, markers, and test-discovery configuration are visible to pytest.

```zsh
python -m pytest --collect-only -q
```

```zsh
% python -m pytest --collect-only -q
tests/integration/test_baselining.py::test_baselining_repeatability_in_pinned_toolchain[global_mission_options/globalmissionoptions_MGALT_DLAbounds]
tests/integration/test_baselining.py::test_baselining_repeatability_in_pinned_toolchain[transcription_tests/SundmanCoastPhase_EMintercept]
...
tests/test_ipopt_characterization.py::test_benchmark_provenance_rejects_unknown_stage
tests/test_ipopt_characterization.py::test_committed_provenance_matches_registry_and_directory

285/319 tests collected (34 deselected) in 0.12s
```

Tutorial collection

```zsh
python -m pytest --collect-only -q --tutorials
```

```zsh
% python -m pytest --collect-only -q --tutorials
tests/integration/test_tutorial_baselining.py::test_tutorial_baselining_cli_writes_fixed_mirrored_layout
tests/integration/test_tutorials.py::test_tutorial_replay[Config_Files/LowSIRIS-REx]
...
tests/integration/test_tutorials.py::test_tutorial_ipopt_refinement[Flybys/HighFidelity]
tests/integration/test_tutorials.py::test_tutorial_ipopt_refinement[Flybys/EVM_singlePhase]

34/376 tests collected (342 deselected) in 0.16s
```

The **34 deselected tests are exactly:**

| Opt-in group             | Count | Why excluded by default                                                   |
| ------------------------ | ----: | ------------------------------------------------------------------------- |
| `clean_bootstrap`        |     1 | Rebuilds the Docker toolchain with `--no-cache`; intentionally expensive. |
| `tutorials` replay tests |    34 | 17 Tutorial baselining tests.                                             |

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

The 137 corpus tests in [[baselining_commands#Corpus tests|Corpus tests]].

### Run the 137 cases under the [[baselining_commands#Complete list of tests]]

#### Create the terminal function

```zsh
baselining_case() {
	EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/tests" \
	python -m pytest tests/integration/test_baselining.py -q \
	-k baselining_cli_writes_fixed_mirrored_layout \
	--baselining-filter "$1"
}
```

#### Complete test case list

See [[baselining_commands#Complete list of tests]].

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

### Generate the corpus summary

```zsh
python testatron/ipopt_characterization.py \
	--summarize-baselining \
	--output-root "$PWD/testatron/ipopt/tests/tests"
```

```zsh
% python testatron/ipopt_characterization.py \
	--summarize-baselining \
	--output-root "$PWD/testatron/ipopt/tests/tests"
Wrote baselining summary for 137 case(s): repo/testatron/ipopt/tests/tests/baselining/baselining-summary.json
```

#### Classification summary

```zsh
python -c 'import json; from collections import Counter; summary=json.load(open("testatron/ipopt/tests/tests/baselining/baselining-summary.json")); print(summary["case_count"]); print(dict(sorted(Counter(case["classification"] for case in summary["cases"]).items())))'
```

```zsh
% python -c 'import json; from collections import Counter; summary=json.load(open("testatron/ipopt/tests/tests/baselining/baselining-summary.json")); print(summary["case_count"]); print(dict(sorted(Counter(case["classification"] for case in summary["cases"]).items())))'
137
{'matched_snopt': 5, 'mismatch_snopt': 132}
```

### Regenerate the human-readable decision-log report from the new artifacts

```zsh
python testatron/ipopt_characterization.py \
	--write-baselining-decision-log \
	--output-root "$PWD/testatron/ipopt/tests/tests"
```

```zsh
% python testatron/ipopt_characterization.py \
        --write-baselining-decision-log \
        --output-root "$PWD/testatron/ipopt/tests/tests"
Wrote baselining decision log for 137 case(s): repo/testatron/ipopt/tests/baselining_case_decision_log.md
```

To inspect the generated decision log

```zsh
git --no-pager diff -- \
	testatron/ipopt/tests/baselining_case_decision_log.md
```

No output means the regenerated report matches the checked-in/generated prior version exactly. A diff shows which case evidence, mappings, mismatch values, or refinement record changed.

The narrative decision record should remain separate: do **not** overwrite `baselining_decision_log.md` merely because the generated companion report was refreshed.

### Verify the fresh 137-case results against the **existing** reviewed current-state reference

#### Verification command

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

#### Verification report

```zsh
python -c 'import json; from collections import Counter; report=json.load(open("testatron/ipopt/tests/tests/baselining/baselining_verification_report.json")); print(report["case_count"]); print(dict(sorted(Counter(case["status"] for case in report["cases"]).items()))); print(report["acceptable"])'
```

```zsh
% python -c 'import json; from collections import Counter; report=json.load(open("testatron/ipopt/tests/tests/baselining/baselining_verification_report.json")); print(report["case_count"]); print(dict(sorted(Counter(case["status"] for case in report["cases"]).items()))); print(report["acceptable"])'
137
{'matched': 137}
True
```
#### Verification override command

> [!warning] When you want to OVERRIDE an existing `baselining_verification.json`
> It overwrites the accepted 137-case current-state contract: `baselining_verification.json`. Use it only after manually reviewing a complete fresh 137-case corpus run, including its summary and generated decision log, and intentionally accepting the new current-state behavior.
> 
> ```zsh
> python testatron/ipopt_characterization.py \
  --write-baselining-verification \
  --output-root "$PWD/testatron/ipopt/tests/tests" \
  --verification-output \
  "$PWD/testatron/ipopt/tests/baselining_verification.json"
> ```

### Promote tests if matched

See [[baselining_commands#Promotion]].

## 10. Run 17 tutorial tests

The 17 tutorial tests in [[tutorial_baselining_commands#Complete Tutorial Case List]].

### Run the 17 cases under  [[tutorial_baselining_commands#Complete tutorial case list]].

#### Create the terminal function

```zsh
tutorial_baselining_case() {
	EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/benchmarks" \
	python -m pytest tests/integration/test_tutorial_baselining.py -q \
	--tutorials \
	--tutorial-baselining-filter "$1"
}
```

#### Complete tutorial case list

See [[tutorial_baselining_commands#Complete Tutorial Case List]].

```zsh
tutorial_baselining_case 'Config_Files/LowSIRIS-REx'
tutorial_baselining_case 'Config_Files/LowSIRIS-REx_high_thrust'
...
tutorial_baselining_case 'Flybys/HighFidelity'
tutorial_baselining_case 'Flybys/EVM_singlePhase'
```


```zsh
.                                                                                                                                                                                                                                                             [100%]
1 passed, 2 deselected in 5.63s
.                                                                                                                                                                                                                                                             [100%]
1 passed, 2 deselected in 6.63s
.                                                                                                                                                                                                                                                             [100%]
1 passed, 2 deselected in 5.46s
```

### Generate the tutorial summary

```zsh
python testatron/ipopt_characterization.py \
	--summarize-tutorial-baselining \
	--output-root "$PWD/testatron/ipopt/tests/benchmarks"
```

```zsh
% python testatron/ipopt_characterization.py \
        --summarize-tutorial-baselining \
        --output-root "$PWD/testatron/ipopt/tests/benchmarks"
Wrote tutorial baselining summary for 17 case(s): repo/testatron/ipopt/tests/benchmarks/baselining/tutorial-baselining-summary.json
```

#### Classification summary

```zsh
python -c 'import json; summary=json.load(open("testatron/ipopt/tests/benchmarks/baselining/tutorial-baselining-summary.json")); print(summary["case_count"]); print(summary["stage_count"]); print(dict(sorted(summary["classification_counts"].items())))'
```

```zsh
% python -c 'import json; summary=json.load(open("testatron/ipopt/tests/benchmarks/baselining/tutorial-baselining-summary.json")); print(summary["case_count"]); print(summary["stage_count"]); print(dict(sorted(summary["classification_counts"].items())))'
17
33
{'dependency_blocked': 0, 'matched_tutorial_reference': 9, 'mismatch_tutorial_reference': 5, 'parse_failed': 0, 'process_failed': 0, 'timed_out': 0, 'topology_changed': 3, 'unstable': 0}
```


### Regenerate the human-readable decision-log report from the new artifacts

```zsh
python testatron/ipopt_characterization.py \
	--write-tutorial-baselining-decision-log \
	--output-root "$PWD/testatron/ipopt/tests/benchmarks"
```

```zsh
% python testatron/ipopt_characterization.py \
        --write-tutorial-baselining-decision-log \
        --output-root "$PWD/testatron/ipopt/tests/benchmarks"
Wrote tutorial baselining decision log for 17 case(s): repo/testatron/ipopt/tests/tutorial_baselining_case_decision_log.md
```


To inspect the generated decision log

```zsh
git --no-pager diff -- \
	testatron/ipopt/tests/tutorial_baselining_case_decision_log.md
```

No output means the regenerated report matches the checked-in/generated prior version exactly. A diff shows which case evidence, mappings, mismatch values, or refinement record changed.

The narrative decision record should remain separate: do **not** overwrite `baselining_decision_log.md` merely because the generated companion report was refreshed.
### Verify the fresh 17-case results against the **existing** reviewed current-state reference

#### Verification command

```zsh
python testatron/ipopt_characterization.py \
  --verify-tutorial-baselining \
  --output-root "$PWD/testatron/ipopt/tests/benchmarks" \
  --tutorial-verification-reference \
  "$PWD/testatron/ipopt/tests/tutorial_baselining_verification.json" \
  --tutorial-verification-report-output \
  "$PWD/testatron/ipopt/tests/benchmarks/baselining/tutorial_baselining_verification_report.json"
```

```zsh
% python testatron/ipopt_characterization.py \
  --verify-tutorial-baselining \
  --output-root "$PWD/testatron/ipopt/tests/benchmarks" \
  --tutorial-verification-reference \
  "$PWD/testatron/ipopt/tests/tutorial_baselining_verification.json" \
  --tutorial-verification-report-output \
  "$PWD/testatron/ipopt/tests/benchmarks/baselining/tutorial_baselining_verification_report.json"
Tutorial baselining verification passed for 33 stage(s): /Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/testatron/ipopt/tests/benchmarks/baselining/tutorial_baselining_verification_report.json
```

#### Verification report

```zsh
python -c 'import json; from collections import Counter; report=json.load(open("testatron/ipopt/tests/benchmarks/baselining/tutorial_baselining_verification_report.json")); print(report["case_count"]); print(report["stage_count"]); print(dict(sorted(Counter(stage["status"] for stage in report["stages"]).items()))); print(report["acceptable"])'
```

```zsh
% python -c 'import json; from collections import Counter; report=json.load(open("testatron/ipopt/tests/benchmarks/baselining/tutorial_baselining_verification_report.json")); print(report["case_count"]); print(report["stage_count"]); print(dict(sorted(Counter(stage["status"] for stage in report["stages"]).items()))); print(report["acceptable"])'
17
33
{'matched': 33}
True
```

#### Verification override command

> [!warning] When you want to OVERRIDE an existing `tutorial_baselining_verification.json`
> It rebuilds the 33-stage current-state contract from the current tutorial evidence. Use it **only** after manually reviewing a completed tutorial run and intentionally accepting a new contract.
> 
> ```zsh
python testatron/ipopt_characterization.py \
  --write-tutorial-baselining-verification \
  --output-root "$PWD/testatron/ipopt/tests/benchmarks" \
  --tutorial-verification-output \
  "$PWD/testatron/ipopt/tests/tutorial_baselining_verification.json"
> ```


### Promote tutorial if matched

See [[tutorial_baselining_commands#Promotion]].

---

# Baselining workflow

The IPOPT Testatron Baselining workflow executes the immutable `testatron/tests` corpus with the open-source IPOPT backend while preserving each adjacent SNOPT-generated `.emtg` file as immutable historical evidence. The workflow answers two separate questions:

1. **Immutable-SNOPT comparison:** does a staged replay and, when eligible,
	IPOPT refinement agree with the historical SNOPT result?

2. **Current-state regression verification:** does fresh evidence reproduce the
	reviewed behavior of the current EMTG/IPOPT environment?

The first (Replay) is a diagnostic comparison to historical truth. The second (Refinement) is the regression gate for the currently supported Docker toolchain. A stable `mismatch_snopt` can be expected current-state behavior; it is not a solver pass against SNOPT, nor a regression by itself.
## Immutable Inputs and Evidence Layout

| Root | Contents |
| --- | --- |
| `testatron/tests/<group>/<case>.emtgopt` | Immutable Testatron mission-options source. |
| `testatron/tests/<group>/<case>.emtg` | Immutable historical SNOPT baseline. |
| `testatron/ipopt/tests/tests/baselining/<group>/<case>/` | Replaceable staged runtime evidence, attempts, logs, comparisons, and summaries. |
| `testatron/ipopt/tests/tests/tests-promoted-baselines/<group>/<case>/` | Curated promoted output for an explicitly approved stable `matched_snopt` case. |
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

