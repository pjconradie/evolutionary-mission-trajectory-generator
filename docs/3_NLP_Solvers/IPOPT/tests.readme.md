# Purpose

IPOPT is not accepted merely because it produces a feasible result. For each comparable case, the IPOPT result must agree with the corresponding SNOPT result within an explicit, reviewed numerical contract. The committed SNOPT options and `.emtg` files are never overwritten, regenerated, or promoted from an IPOPT run.

Run the commands in this document from the repository root.

# EMTG clean bootstrapping

## Introduction

Can a clean machine build the EMTG Docker environment from the pinned recipe, without relying on an already-existing EMTG compiler image, CMake build tree, or cached native executable?

It verifies the **factory**, not EMTG’s mission results and not the archive.

It should establish that Docker can create the shared canonical source-builder environment containing:

- Debian 12 / Bookworm;
- the compiler toolchain;
- IPOPT and required development dependencies;
- validated CSPICE;
- the other native build dependencies.

A successful clean bootstrap says:

> “We can recreate the controlled EMTG build environment.”

It does **not** say:

> “The source code is correct.”  
> “The archive works.”  
> “The tutorial results match.”

This is a prerequisite for both source verification and archive verification.



## Testing summary

To be implemented.

# EMTG Source testing workflow

## Introduction

Given the canonical Docker build environment, does the EMTG source checkout compile and behave correctly?

It verifies the **product source code**.

It uses the source checkout and source-built executable, typically:

```
/build/src/EMTGv9
```

It covers:

- unit tests;
- regression tests;
- IPOPT characterization contracts;
- source integration tests;
- the 137-case corpus;
- the 17 tutorial replay/refinement verification;
- reviewed source/current-state references.

A successful source verification says:

> “This EMTG source revision compiles and produces the accepted solver behavior.”

It does **not** say:

> “A third party can deploy the emitted archive correctly.”

The source workflow can be perfect while the package is broken, missing files, has a bad runtime dependency list, extracts to the wrong path, or fails in a compiler-free runtime image.

## Testing summary

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
# EMTG Archive testing workflow

## Introduction

Can the built EMTG runtime archive be handed to a third-party deployment environment, extracted into a clean runtime container, and produce the same accepted tutorial behavior without source code or compilers?

It verifies the **deliverable**.

It starts from an archive containing:

```
emtg-ipopt-9.02.tar.gz
emtg-ipopt-9.02.tar.gz.sha256
```

The archive workflow verifies:

- archive payload and tar safety;
- SHA-256 checksum;
- actual runtime package requirements;
- extraction layout:

```
/opt/toolkit/emtg/bin/EMTGv9
```

- a clean compiler-free runtime image;
- no source checkout, CMake, compiler, PyEMTG, or source-builder dependency prefix;
- all 17 tutorial cases;
- all 33 required replay/refinement stages;
- repeatability;
- exact-release archive baselining.

A successful archive verification says:

> “This exact archive is a valid EMTG deliverable for a third-party deployment environment.”

It does **not** replace source verification. It proves deployment packaging and runtime behavior, not the whole source development quality process.

## Testing summary

The EMTG archive workflow validates a deployable **third-party deployment environment** runtime payload. The archive is a runtime artifact, not a source distribution.

The source-builder environment compiles EMTG from the repository checkout. The deployment runtime image contains only:

```
/opt/toolkit/emtg/bin/EMTGv9
/opt/toolkit/emtg/universe/
/opt/toolkit/emtg/hardware/
/opt/toolkit/emtg/RUNTIME_REQUIREMENTS.txt
/opt/toolkit/emtg/README.md
```

The clean runtime image must not contain EMTG source code, a CMake build directory, CMake, compilers, development headers, PyEMTG, or source-builder `/opt/emtg-deps` state.

Run all commands from the repository root.

Archive test category selectors are mutually exclusive:
```
--unit
--integration
--tutorials
```

Observed testing durations:

| Path                          |                 Observed time | Expected use                                      |
| ----------------------------- | ----------------------------: | ------------------------------------------------- |
| Unit tests                    |            23 passed in 0.12s | Every archive-toolchain change                    |
| Cold archive integration      | 1 passed in 546.22s (0:09:06) | Release candidates and cache-independent proof    |
| Hot archive integration       |            1 passed in 35.55s | Iteration on unchanged source/configuration       |
| Hot deployment tutorial gate  |             ? passed in 3.53s | Iteration after archive/deployment-runner changes |
| Cold deployment tutorial gate | 1 passed in 720.21s (0:12:00) | Final cache-independent deployment greenlight     |

Use a distinct `EMTG_TEST_ARTIFACT_DIR` for each Docker-backed test layer. Each invocation creates a unique child directory so previous retained evidence is not overwritten.


| #   | Test                                      | Command                                                                                                                                                                                                                                          | Runtime information                                                                   | Docker required |
| --- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- | --------------- |
| 1   | Run archive collection sanity             | `python -m pytest tests/emtg_toolchain/unit --unit --collect-only -q`<br>`python -m pytest tests/emtg_toolchain/integration --integration --collect-only -q`<br>`python -m pytest tests/emtg_toolchain/deployment --tutorials --collect-only -q` | 28 tests collected in 0.03s<br>1 test collected in 0.01s<br>1 test collected in 0.05s | No              |
| 2   | Run archive-toolchain unit tests          | `python -m pytest tests/emtg_toolchain/unit --unit -q`                                                                                                                                                                                           | 28 passed in 0.08s                                                                    | No              |
| 3   | Run cold archive integration test         | `EMTG_ARCHIVE_COLD=1 \`<br>`EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-cold" \`<br>`python -m pytest tests/emtg_toolchain/integration --integration -q`                                                                            | 1 passed in 2751.88s (0:45:51)                                                        | Yes             |
| 3   | Run hot archive integration test          | `EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-hot" \`<br>`python -m pytest tests/emtg_toolchain/integration --integration -q`                                                                                                        | 1 passed in 504.63s (0:08:24)                                                         | Yes             |
| 4   | Run cold deployment tutorial gate         | `EMTG_ARCHIVE_COLD=1 \`<br>`EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-deployment-cold" \`<br>`python -m pytest tests/emtg_toolchain/deployment --tutorials -q -s`                                                                 | 1 passed in 694.96s (0:11:34)                                                         | Yes             |
| 4   | Run hot deployment tutorial gate          | `EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-deployment-hot" \`<br>`python -m pytest tests/emtg_toolchain/deployment --tutorials -q -s`                                                                                             | 1 passed in 244.27s (0:04:04)                                                         | Yes             |
| 4   | Inspection command                        | `python -m json.tool "<artifact-directory>/verification.json"`                                                                                                                                                                                   | 0.01s                                                                                 | No              |
| 5   | Create the versioned EMTG release archive |                                                                                                                                                                                                                                                  | 10-20 min                                                                             | Yes             |
| 5   | Verify the release archive checksum       |                                                                                                                                                                                                                                                  | 10-20 min                                                                             | No              |
| 5   | Baseline the exact release archive        |                                                                                                                                                                                                                                                  | 10-20 min                                                                             | Yes             |

1, 2
```zsh
python -m pytest tests/emtg_toolchain/unit --unit --collect-only -q
python -m pytest tests/emtg_toolchain/integration --integration --collect-only -q
python -m pytest tests/emtg_toolchain/deployment --tutorials --collect-only -q
python -m pytest tests/emtg_toolchain/unit --unit -q
```

3
```zsh
EMTG_ARCHIVE_COLD=1 \
	EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-cold" \
	python -m pytest tests/emtg_toolchain/integration --integration -q
```

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-hot" \
	python -m pytest tests/emtg_toolchain/integration --integration -q
```

4
```zsh
EMTG_ARCHIVE_COLD=1 \
	EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-deployment-cold" \
	python -m pytest tests/emtg_toolchain/deployment --tutorials -q -s
```

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-deployment-hot" \
	python -m pytest tests/emtg_toolchain/deployment --tutorials -q -s
```

```zsh
python -m json.tool "<artifact-directory>/verification.json"
```

5 - Test existing baseline

5 - Generate a new baseline
```zsh
% rm -f \
	"$PWD/releases/emtg-ipopt-9.02.tar.gz" \
	"$PWD/releases/emtg-ipopt-9.02.tar.gz.sha256"
```

```zsh
EMTG_VERSION="9.02"
mkdir -p releases

python -m emtg_toolchain package \
	--cold \
	--emtg-repo "$PWD" \
	--output "$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz"
```

```zsh
archive="$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz"
checksum="${archive}.sha256"
expected="$(awk 'NR == 1 { print $1 }' "$checksum")"
actual="$(shasum -a 256 "$archive" | awk '{ print $1 }')"

if [[ "$actual" == "$expected" ]]; then
	print "SHA-256 verified: $archive"
else
	print -u2 "SHA-256 verification failed: $archive"
	exit 1
fi
```

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-release-baseline-${EMTG_VERSION}" \
python -m pytest tests/emtg_toolchain/deployment \
	--tutorials \
	--release-archive "$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz" \
	-q -s
```

## 1. Run collection sanity

Unit test collection

```zsh
python -m pytest tests/emtg_toolchain/unit --unit --collect-only -q
```

```zsh
% python -m pytest tests/emtg_toolchain/unit --unit --collect-only -q
tests/emtg_toolchain/unit/test_cli.py::test_parser_rejects_non_archive_output
tests/emtg_toolchain/unit/test_cli.py::test_parser_rejects_literal_release_version_placeholder
...
tests/emtg_toolchain/unit/test_runtime.py::test_runtime_requirements_parser_reads_generated_package_list
tests/emtg_toolchain/unit/test_runtime.py::test_runtime_requirements_parser_rejects_missing_package_list

28 tests collected in 0.03s
```

Integration test collection

```zsh
python -m pytest tests/emtg_toolchain/integration --integration --collect-only -q
```

```zsh
% python -m pytest tests/emtg_toolchain/integration --integration --collect-only -q
tests/emtg_toolchain/integration/test_emtg_archive_integration.py::test_archive_extracts_into_clean_bookworm_runtime

1 test collected in 0.01s
```

Deployment test collection

```
python -m pytest tests/emtg_toolchain/deployment --tutorials --collect-only -q
```

```zsh
% python -m pytest tests/emtg_toolchain/deployment --tutorials --collect-only -q
tests/emtg_toolchain/deployment/test_emtg_archive_tutorials.py::test_extracted_archive_passes_all_tutorial_verification

1 test collected in 0.05s
```

## 2. Run unit tests

```zsh
python -m pytest tests/emtg_toolchain/unit --unit -q
```

```zsh
% python -m pytest tests/emtg_toolchain/unit --unit -q

............................                                                                                                                                                                 [100%]
28 passed in 0.08s
```

These tests require no Docker daemon and validate the archive-toolchain logic without compiling EMTG.

They cover:

- CLI argument validation:
- Runtime-linkage validation:
- Runtime dependency manifest generation and parsing.
- Archive payload allowlisting:
- Archive safety:
- SHA-256 manifest generation and validation.
- Content-addressed hot-cache identity and invalidation behavior.

A passing unit run proves archive-toolchain behavior, but does not compile EMTG or invoke Docker.

## 3. Run integration tests

### Run cold archive build and fresh runtime-image integration tests

```zsh
EMTG_ARCHIVE_COLD=1 \
	EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-cold" \
	python -m pytest tests/emtg_toolchain/integration --integration -q
```

```zsh
% EMTG_ARCHIVE_COLD=1 \                   
    EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-cold" \
    python -m pytest tests/emtg_toolchain/integration --integration -q
.                                                                                                                                                                                                                                                    [100%]
1 passed in 2751.88s (0:45:51)
```

The cold archive-build path compiles EMTG in a command-owned temporary CMake build directory. It does not reuse the package CMake build cache or prior compiled EMTG objects.

The clean archive-runtime image is also built with:
```zsh
--no-cache
--platform linux/amd64
```

Use the cold path when:

- preparing a release candidate;
- validating a new archive for deployment;
- changing CMake/build policy;
- changing compiler/IPOPT assumptions;
- requiring cache-independent evidence.

This is the slower path. It validates that the archive can be produced without a previously compiled EMTG build tree.

> The archive cold path does not replace the separate source-builder Docker cold-bootstrap workflow. Source-builder image hardening remains a separate workflow.

### Run hot archive build integration tests

The hot package CMake cache is a persistent Docker volume. It survives pytest process exit and is reused only when its content-addressed identity matches the current source and build configuration.

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-hot" \
	python -m pytest tests/emtg_toolchain/integration --integration -q
```

```zsh
% EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-hot" \
        python -m pytest tests/emtg_toolchain/integration --integration -q
.                                                                                                                                                                                                                                                    [100%]
1 passed in 504.63s (0:08:24)
```

The hot archive-build path reuses only a validated, content-addressed package CMake build volume.

The cache identity includes:

```
EMTG source-tree content fingerprint
canonical source-builder image identity
linux/amd64 target platform
EMTG_NLP_SOLVER=IPOPT
CSPICE, GSL, and Boost CMake configuration
```

Every invocation still reruns:

```zsh
CMake configure
cmake --build
archive generation
checksum validation
fresh clean runtime-image construction
runtime linkage validation
```

For unchanged source and configuration, `cmake --build` should be incremental or a no-op, avoiding the full native recompilation.

The hot path is appropriate for development iteration. It is not a substitute for the cold archive-build path required for a release/deployment greenlight.

> The runtime deployment image is never hot-reused. Each integration run creates a fresh clean runtime image from the newly generated archive.

### Archive integration evidence

When `EMTG_TEST_ARTIFACT_DIR` is set, each integration run retains evidence under a unique directory such as:

```
test-artifacts/emtg-archive-hot/emtg-toolchain-*/
├── emtg-ipopt.tar.gz
├── emtg-ipopt.tar.gz.sha256
├── source-build.log
├── source-EMTGv9.ldd
├── source-runtime-packages.tsv
├── runtime-image-build.log
├── runtime-image.txt
└── runtime-ldd.log
```

2026-10-19 cont.
## 4. Run deployment tests

Run cold deployment tutorial gate

```zsh
EMTG_ARCHIVE_COLD=1 \
	EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-deployment-cold" \
	python -m pytest tests/emtg_toolchain/deployment --tutorials -q -s
```

```zsh
% EMTG_ARCHIVE_COLD=1 \
        EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-deployment-cold" \
        python -m pytest tests/emtg_toolchain/deployment --tutorials -q -s
[1/5] Building IPOPT EMTG (cold build)
[2/5] Validating EMTG runtime linkage
...
[17/17] Starting Flybys/EVM_singlePhase
[17/17] Completed Flybys/EVM_singlePhase in 12.8s
.
1 passed in 694.96s (0:11:34)
```

Run hot deployment tutorial gate

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-deployment-hot" \
	python -m pytest tests/emtg_toolchain/deployment --tutorials -q -s
```


```zsh
% 
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-deployment-hot" \
        python -m pytest tests/emtg_toolchain/deployment --tutorials -q -s
[1/5] Building IPOPT EMTG (hot build)
[2/5] Validating EMTG runtime linkage
...
[17/17] Starting Flybys/EVM_singlePhase
[17/17] Completed Flybys/EVM_singlePhase in 13.1s
.
1 passed in 244.27s (0:04:04)
```

This is the archive deployment-greenlight gate.

The test:

1. Uses the cold archive-build path to create an archive without reusable CMake objects.
2. Cold-builds a fresh compiler-free Bookworm runtime image from the archive and declared runtime dependencies.
3. Extracts EMTG at:

```
/opt/toolkit/emtg/bin/EMTGv9
```

4. Stages tutorial-specific options, universe data, hardware data, and required external kernels into isolated per-case directories.
5. Starts a new disposable `--rm` clean runtime container for every tutorial stage.
6. Mounts only the corresponding staged case directory at /artifacts.

```
/opt/toolkit/emtg/bin/EMTGv9 /artifacts/<prepared-options>.emtgopt
```

`/artifacts` is deliberate: the established tutorial staging contract rewrites legacy hardware references to `/artifacts/hardware_models/...`. This is an archive-test adapter convention; it does not modify source tutorial inputs or baseline behavior.

7. Captures stdout, stderr, exit status, generated `.emtg` output, comparisons, and provenance.
8. Runs each tutorial case twice to verify repeatability.
9. Compares the generated evidence to the reviewed tutorial verification reference.

The repository checkout is used by the pytest test orchestrator to prepare tutorial inputs and compare generated outputs. It is never mounted into the clean runtime container.

The reviewed tutorial contract contains:

```zsh
17 tutorial cases
33 required replay/refinement stages
2 attempts per case
at least 66 packaged-binary stage executions
```

Schema-probe executions may add further packaged-binary invocations.

Deployment is greenlit only when:

- all 17 tutorial cases have complete evidence;
- all 33 required stages match the reviewed verification reference;
- both attempts for every case are stable;
- no case is missing, skipped, timed out, process-failed, parse-failed, dependency-blocked, or numerically mismatched;
- the final verification report has:

```zsh
{
	"case_count": 17,
	"stage_count": 33,
	"acceptable": true
}
```

### Deployment evidence

Each deployment invocation retains a unique evidence directory:

```
test-artifacts/<chosen-artifact-root>/emtg-toolchain-*/
```

It contains:
```
├── emtg-ipopt.tar.gz
├── emtg-ipopt.tar.gz.sha256
├── source-build.log
├── source-EMTGv9.ldd
├── source-runtime-packages.tsv
├── runtime-image-build.log
├── runtime-image.txt
├── archive-build-mode.txt
├── verification.json
└── evidence/
    └── baselining/
        └── <tutorial-case>/
            ├── attempt-1/
            ├── attempt-2/
            ├── repeatability.json
            └── result.json
```

The deployment result is accepted only when verification.json states:

- case_count is 17;
- stage_count is 33;
- acceptable is true;
- every entry in stages has status "matched";
- reference identifies the reviewed tutorial verification reference:
  testatron/ipopt/tests/tutorial_baselining_verification.json.


A useful inspection command to document:

```zsh
python -m json.tool "<artifact-directory>/verification.json"
```

example:
```zsh
% python -m json.tool "test-artifacts/emtg-archive-deployment-cold/emtg-toolchain-mqzlsfut/verification.json"
{
    "version": 1,
    "reference": "/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/testatron/ipopt/tests/tutorial_baselining_verification.json",
    "case_count": 17,
    "stage_count": 33,
    "stages": [
        {
            "case_id": "Config_Files/LowSIRIS-REx",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Config_Files/LowSIRIS-REx",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Config_Files/LowSIRIS-REx_high_thrust",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Config_Files/LowSIRIS-REx_high_thrust",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Config_Files/LowSIRIS-REx_high_thrust_low_c3",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Config_Files/LowSIRIS-REx_high_thrust_low_c3",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Constraint_Scripting/EVM_freepoint",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Constraint_Scripting/EVM_freepoint",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Constraint_Scripting/EVM_freepoint_boundary_constraint",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Constraint_Scripting/EVM_freepoint_boundary_constraint",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Constraint_Scripting/EVM_freepoint_maneuver_constraint",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Constraint_Scripting/EVM_freepoint_maneuver_constraint",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Flybys/EVM",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Flybys/EVM",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Flybys/EVM_singlePhase",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Flybys/EVM_singlePhase",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Flybys/HighFidelity",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Flybys/HighFidelity",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Force_Models/LowSIRIS-REx",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Force_Models/LowSIRIS-REx",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Force_Models/LowSIRIS-REx_forcemodel",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Force_Models/LowSIRIS-REx_forcemodel_nlp",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Force_Models/LowSIRIS-REx_forcemodel_nlp",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Journey_Boundaries/EVM",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Journey_Boundaries/EVM",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "Journey_Boundaries/EVM_freepoint",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "Journey_Boundaries/EVM_freepoint",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "LowSIRIS-REx/LowSIRIS-REx",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "LowSIRIS-REx/LowSIRIS-REx",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "LowSIRIS-REx/LowSIRIS-REx_FBLT",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "LowSIRIS-REx/LowSIRIS-REx_FBLT",
            "stage": "replay",
            "status": "matched"
        },
        {
            "case_id": "OSIRIS-REx/OSIRIS-REx",
            "stage": "refinement",
            "status": "matched"
        },
        {
            "case_id": "OSIRIS-REx/OSIRIS-REx",
            "stage": "replay",
            "status": "matched"
        }
    ],
    "acceptable": true
}
```

## 5. Baseline an existing release archive

### Test an existing baseline

Verify the baselined archive:

```zsh
archive="$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz"
checksum="${archive}.sha256"
expected="$(awk 'NR == 1 { print $1 }' "$checksum")"
actual="$(shasum -a 256 "$archive" | awk '{ print $1 }')"

if [[ "$actual" == "$expected" ]]; then
	print "SHA-256 verified: $archive"
else
	print -u2 "SHA-256 verification failed: $archive"
	exit 1
fi
```

```zsh
% archive="$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz"
checksum="${archive}.sha256"
expected="$(awk 'NR == 1 { print $1 }' "$checksum")"
actual="$(shasum -a 256 "$archive" | awk '{ print $1 }')"

if [[ "$actual" == "$expected" ]]; then
        print "SHA-256 verified: $archive"
else
        print -u2 "SHA-256 verification failed: $archive"
        exit 1
fi
SHA-256 verified: /Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/releases/emtg-ipopt-9.02.tar.gz
```

### Generate a new baseline

Remove the named archive and checksum:

```zsh
rm -f \
	"$PWD/releases/emtg-ipopt-9.02.tar.gz" \
	"$PWD/releases/emtg-ipopt-9.02.tar.gz.sha256"
```

Create the release archive with a cold build:

```zsh
EMTG_VERSION="9.02"
mkdir -p releases

python -m emtg_toolchain package \
	--cold \
	--emtg-repo "$PWD" \
	--output "$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz"
```

```zsh
% EMTG_VERSION="9.02"
mkdir -p releases

python -m emtg_toolchain package \
        --cold \
        --emtg-repo "$PWD" \
        --output "$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz"
[1/5] Building IPOPT EMTG (cold build)
[2/5] Validating EMTG runtime linkage
[3/5] Staging archive runtime payload
[4/5] Creating archive and SHA-256 checksum
[5/5] Publishing validated archive
Published EMTG archive: /Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/releases/emtg-ipopt-9.02.tar.gz
Published SHA-256 checksum: /Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/releases/emtg-ipopt-9.02.tar.gz.sha256
Next: baseline this exact archive with --release-archive after verifying its checksum.
```

Verify that exact archive and its adjacent checksum:

> [!Warning] HERE

```zsh
EMTG_VERSION="9.02"
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-release-baseline-${EMTG_VERSION}" \
python -m pytest tests/emtg_toolchain/deployment \
	--tutorials \
	--release-archive "$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz" \
	-q -s
```

```zsh
% EMTG_VERSION="9.02"
% EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-release-baseline-${EMTG_VERSION}" \
python -m pytest tests/emtg_toolchain/deployment \
        --tutorials \
        --release-archive "$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz" \
        -q -s
Verifying archive tutorials: 17 cases, 33 required stages, two attempts per case
[1/17] Starting Config_Files/LowSIRIS-REx
[1/17] Completed Config_Files/LowSIRIS-REx in 4.1s
...
[17/17] Starting Flybys/EVM_singlePhase
[17/17] Completed Flybys/EVM_singlePhase in 12.5s
.
1 passed in 202.17s (0:03:22)
```


Verify the baselined archive:

```zsh
EMTG_VERSION="9.02"
archive="$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz"
checksum="${archive}.sha256"
expected="$(awk 'NR == 1 { print $1 }' "$checksum")"
actual="$(shasum -a 256 "$archive" | awk '{ print $1 }')"

if [[ "$actual" == "$expected" ]]; then
	print "SHA-256 verified: $archive"
else
	print -u2 "SHA-256 verification failed: $archive"
	exit 1
fi
```

```zsh
% EMTG_VERSION="9.02"
archive="$PWD/releases/emtg-ipopt-${EMTG_VERSION}.tar.gz"
checksum="${archive}.sha256"
expected="$(awk 'NR == 1 { print $1 }' "$checksum")"
actual="$(shasum -a 256 "$archive" | awk '{ print $1 }')"

if [[ "$actual" == "$expected" ]]; then
        print "SHA-256 verified: $archive"
else
        print -u2 "SHA-256 verification failed: $archive"
        exit 1
fi
SHA-256 verified: /Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/releases/emtg-ipopt-9.02.tar.gz
```


The release baseline:

1. requires `<archive>.sha256` next to the supplied archive;
2. validates the archive layout and checksum before reading it;
3. requires the archive's `RUNTIME_REQUIREMENTS.txt` to record
   `Build mode: cold`;
4. builds the clean runtime image from the supplied archive, without invoking
   `emtg_toolchain package`;
5. performs the same 17-case, 33-stage, two-attempt tutorial verification; and
6. writes `verification.json` and `release-baseline.json` under the unique
   evidence directory.

`release-baseline.json` binds the accepted result to the archive filename and
SHA-256, archive build mode, source commit recorded in the archive manifest,
runtime-requirements checksum, tutorial-reference checksum, final verification
decision, and evidence-directory path.

Release approval requires both files to report an accepted result:

```zsh
python -m json.tool "<artifact-directory>/verification.json"
python -m json.tool "<artifact-directory>/release-baseline.json"
```

The archive and `<archive>.sha256` are the handoff payload. The third-party
deployment environment must verify the checksum, install the packages declared
in `emtg/RUNTIME_REQUIREMENTS.txt`, extract the archive into `/opt/toolkit`,
and invoke `/opt/toolkit/emtg/bin/EMTGv9` from its isolated writable run
directory.

Also state that a green pytest result is the primary gate, while `verification.json` is the retained, inspectable evidence of that decision.

# Case and Tutorial testing workflow

The IPOPT Testatron Case and Tutorial workflow describes the Case and Tutorial testing framework and thinking.

It describes the execution of immutable `testatron/tests` corpus with the open-source IPOPT backend while preserving each adjacent SNOPT-generated `.emtg` file as immutable historical evidence. The workflow answers two separate questions:

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

