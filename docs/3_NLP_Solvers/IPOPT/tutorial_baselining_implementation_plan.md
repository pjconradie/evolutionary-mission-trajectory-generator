## Planning outcome

The tutorial work should **not** be added to the existing 137-case artifact tree as a twenty-third group. Doing that would make the existing 137-case reference treat the 33 tutorial cases as unexpected evidence and fail verification.

Instead, implement a **second, parallel baselining suite** with the same execution and review contract, while preserving the 137-case corpus unchanged.

| Suite     |                Cases | Immutable source/reference                                                                             | Evidence root                                 | Current-state reference                                       |
| --------- | -------------------: | ------------------------------------------------------------------------------------------------------ | --------------------------------------------- | ------------------------------------------------------------- |
| Corpus    |                  137 | `testatron/tests/` `.emtgopt` + adjacent historical `.emtg`                                            | `testatron/ipopt/tests/tests/baselining/`     | `baselining_verification.json`                                |
| Tutorials | 33 stages / 17 cases | `Tutorial_EMTG_Files/` inputs, reference packages, hardware, universe, ephemerides, and seed artifacts | `testatron/ipopt/tests/benchmarks/baselining` | `testatron/ipopt/tests/tutorial_baselining_verification.json` |

This gives the requested common workflow without weakening, overwriting, or conflating the completed 137-case contract.

| Concern                                  | Agreed location                                |
| ---------------------------------------- | ---------------------------------------------- |
| Replaceable tutorial baselining evidence | `testatron/ipopt/tests/benchmarks/baselining/` |
| Tutorial baselining execution policy     | `tutorial_baselining_policy.json`              |
| Tutorial current-state numeric policy    | `tutorial_baselining_verification_policy.json` |
| Accepted tutorial current-state contract | `tutorial_baselining_verification.json`        |

---

# Proposed design

## 1. Preserve the two suites as separate evidence domains

### Retain corpus paths exactly as they are

Do not rename, move, regenerate, or alter any existing corpus mechanism:

- `testatron/ipopt/tests/tests/baselining/`
- `baselining_verification.json`
- `baselining_case_decision_log.md`

The currently passing 137-case workflow remains a stable reference implementation.

### Add a tutorial-specific parallel layout

Recommended paths:

```text
testatron/ipopt/tests/benchmarks/baselining/
├── <tutorial-group>/
│   └── <tutorial-case>/
│       ├── attempt-1/
│       │   ├── replay/
│       │   └── refinement/          # when applicable
│       ├── attempt-2/
│       │   ├── replay/
│       │   └── refinement/          # when applicable
│       ├── repeatability.json
│       └── result.json
├── tutorial-baselining-summary.json
└── tutorial-baselining-verification-report.json

testatron/ipopt/tests/tutorial_baselining_verification.json
testatron/ipopt/tests/tutorial_baselining_case_decision_log.md
testatron/ipopt/tests/tutorial_baselined_checklist.md
```

The tutorial reference JSON must be independent from the 137-case reference. Therefore, a fresh tutorial verification candidate may be created and manually accepted without changing the accepted corpus contract.

---

## 2. Make tutorials use the same baselining lifecycle

The current tutorial test module, `test_tutorials.py`, is **not yet** a baselining workflow. It performs one execution per declared stage and marks the results `unreviewed`.

The implementation should add a tutorial baselining runner with the same lifecycle used by the corpus:

### Per tutorial case

1. **Stage immutable inputs safely**
   - Copy only the required tutorial `.emtgopt`, reference mission, seed/XF data, hardware models, universe files, and declared ephemeris assets into case-scoped writable staging.
   - Keep the repository mount read-only.
   - Record hashes and exact source paths in provenance.
   - Never modify files under `Tutorial_EMTG_Files/`.

2. **Run attempt 1**
   - Perform the tutorial-specific preparation already represented by `TutorialCase`.
   - Run the replay stage with the case’s declared seed source and no IPOPT solve.
   - Run refinement only when that tutorial case declares refinement as applicable.
   - Preserve special existing policies:
     - schema probes;
     - archive versus current-infeasible seeds;
     - deliberate-infeasible expected output;
     - case-specific objective policy;
     - tutorial hardware, universe, and ephemeris staging.

3. **Run a fresh attempt 2**
   - Repeat the complete applicable tutorial pipeline from fresh case-scoped staging.
   - Do not treat cached schema output, a prior generated mission, or a prior staged option file as proof of repeatability.

4. **Compare attempts**
   - Write `repeatability.json`.
   - Require equal classification and approved replay/refinement values, just as the corpus does.
   - A tutorial case is stable only when both attempts agree.

5. **Write a normalized final `result.json`**
   - Preserve the existing useful tutorial-specific checks.
   - Add the standard baselining fields that support summary generation, decision-log rendering, verification, and promotion.

### Important semantic detail

The corpus compares against an immutable **SNOPT** result, so its classifications are `matched_snopt` and `mismatch_snopt`.

Tutorial reference packages should not be labelled SNOPT unless their provenance proves that they are SNOPT baselines. The recommended terminology is:

```text
matched_tutorial_reference
mismatch_tutorial_reference
```

That preserves the identical operational flow—replay, eligible IPOPT refinement, two attempts, evidence, verification, and promotion eligibility—without falsely asserting the tutorial references’ solver provenance.

A deliberate-infeasible tutorial remains a valid replay-only case. Its intentional absence of refinement must be explicit evidence, not a failed or skipped second phase.

---

# Implementation plan

The tutorial suite is **33 executable stages across 17 tutorial cases**:

- 17 replay stages;
- 16 refinement stages;
- 1 intentional replay-only deliberate-infeasible case.

The operator-facing baselining unit should be a **tutorial case**, not an isolated stage. A selected case command executes its applicable stages within each of two fresh attempts.

Therefore, the final command list should contain **17 tutorial case commands** which together produce and verify **33 tutorial stage outcomes**. This preserves the existing baselining meaning of a case:

```
attempt 1: replay -> eligible refinement
attempt 2: replay -> eligible refinement
repeatability comparison
final case result
```

A list of 33 independent stage commands would split replay/refinement evidence from its case, weaken promotion safety, and depart from the established 137-case workflow.

## Phase 1 — Define the tutorial baselining contract

**Goal:** establish a durable data model before writing the Docker launcher.

1. Extend the existing tutorial case registry in `ipopt_characterization.py` with explicit baselining metadata:
   - immutable source/reference identities;
   - applicable stages;
   - seed and schema requirements;
   - expected output taxonomy;
   - acceptance/comparison policy;
   - promotion eligibility.

2. Add a generic suite discriminator, for example `corpus` versus `tutorials`, to the internal baselining evidence model.
   - Existing corpus JSON must remain valid and unchanged in meaning.
   - New tutorial evidence explicitly identifies itself as tutorial-suite evidence.

3. Define the tutorial classification vocabulary and promotion rule.
   - Recommendation: only stable `matched_tutorial_reference` cases may be promoted.
   - Stable mismatches remain retained diagnostic evidence, exactly as corpus `mismatch_snopt` evidence does.

4. Define tutorial current-state verification schema and policies.
   - Keep the existing corpus verification reference format and reference file unchanged.
   - Add a tutorial-specific reference file and, if needed, a tutorial-specific numeric policy.
   - Reuse the existing policy only where tutorial metrics and semantics are actually equivalent.

**Acceptance criteria:** unit tests prove the tutorial registry contains 17 cases, 33 declared stages, unique IDs, valid immutable paths, and complete policy metadata.

---

## Phase 2 — Extract shared baselining primitives

**Goal:** prevent a forked second implementation from drifting away from the corpus workflow.

1. Identify reusable pieces currently dedicated to corpus baselining:
   - attempt-directory lifecycle;
   - replacement of prior selected evidence;
   - `result.json`/`repeatability.json` layout;
   - two-attempt comparison;
   - summary rendering;
   - verification-reference build/write/verify;
   - decision-log rendering;
   - promotion approval and immutable-source-hash checks.

2. Extract suite-neutral helpers where the behavior truly matches.
   - Do **not** force the existing corpus-specific `discover_cases(testatron/tests)` logic onto tutorials.
   - Add an explicit tutorial discovery/selection path based on `TUTORIAL_CASES`.

3. Keep tutorial-only preparation and comparisons separate but feed their results into the same normalized evidence protocol.

4. Preserve the existing corpus API and command behavior as a regression constraint.

**Acceptance criteria:** focused unit tests demonstrate that corpus evidence is byte/shape compatible with current behavior and tutorial evidence gets the required two-attempt layout.

---

## Phase 3 — Add the Docker-backed tutorial baselining launcher

**Goal:** make a selected tutorial case run through the exact same operational pathway as a selected corpus case.

1. Add a tutorial-specific pytest launcher alongside `test_baselining.py`, or add a clearly separated tutorial launcher in that module if shared setup remains clean.

2. Add a dedicated command-line selector, such as:

```text
--tutorial-baselining-filter <group/case>
```

3. Use the same Docker contracts:
   - pinned reusable toolchain image;
   - normal named `/build` volume;
   - disposable `docker run --rm` containers;
   - read-only repository inputs;
   - writable host evidence mount;
   - explicit per-case timeout;
   - no concurrent corpus/tutorial baselining runs against the same build volume.

4. Stage tutorial input dependencies outside the repository only if Docker Desktop bind-mount behavior requires it; otherwise preserve the direct immutable read-only mount. Any staging must copy the complete declared input dependency set and verify hashes.

5. Validate output structure in the launcher:
   - `attempt-1/result.json`;
   - `attempt-2/result.json`;
   - `repeatability.json`;
   - final `result.json`;
   - replay/refinement logs and generated mission artifacts;
   - provenance and compatibility records.

**Acceptance criteria:** a small representative integration set covers:
- normal replay + refinement;
- replay-only deliberate infeasibility;
- schema-probe case;
- current-infeasible-seed case.

No 33-case execution is required until this implementation is reviewed and accepted.

---

## Phase 4 — Add reporting, decision logs, and tutorial verification

**Goal:** give tutorials the same auditability as the corpus.

1. Add tutorial summary generation:
   - `tutorial-baselining-summary.json`;
   - explicit case/stage count;
   - classification count;
   - selected-case completeness checks.

2. Add tutorial decision-log generation:
   - dedicated generated report:
     `tutorial_baselining_case_decision_log.md`;
   - separate manual checklist:
     `tutorial_baselined_checklist.md`.

3. Add tutorial verification operations:
   - write a candidate tutorial reference only through an explicit acceptance command;
   - verify fresh tutorial evidence against the accepted reference;
   - reject missing, added, unstable, execution-changed, topology-changed, source-hash-changed, and numeric-drift evidence.

4. Keep the existing corpus report and verification commands unmodified.

**Acceptance criteria:** unit tests prove:
- a candidate reference cannot be written accidentally as part of ordinary baselining;
- a modified value or stage result yields a failed tutorial verification report;
- a tutorial verification report distinguishes all 33 expected stages/case outcomes;
- corpus verification still reports exactly 137 matched cases.

---

## Phase 5 — Add reviewed promotion for tutorials

**Goal:** make promotion possible without overwriting immutable tutorial references.

1. Extend promotion with an explicit suite choice:
   - corpus promotion remains the current behavior;
   - tutorial promotion reads only tutorial-suite evidence.

2. Require:
   - explicit `--approve-baseline`;
   - stable two-attempt evidence;
   - eligible `matched_tutorial_reference` classification;
   - matching immutable source/reference hashes and provenance;
   - no silent replacement of existing curated tutorial artifacts.

3. Use a tutorial curated-output root separate from both:
   - immutable tutorial inputs/references;
   - replaceable tutorial baselining evidence.

4. Record promotion status in the tutorial checklist/decision log.

**Acceptance criteria:** promotion succeeds only for an approved stable tutorial match, refuses mismatches or unstable evidence, and never modifies tutorial source/reference files.

---

## Phase 6 — Document the command workflow

**Goal:** make the operator experience parallel, predictable, and complete.

Update `baselining_commands.md` to include:

1. corpus terminal functions and complete 137-case list;
2. tutorial terminal functions and complete 33-stage list;
3. tutorial artifact locations;
4. tutorial summary command;
5. tutorial decision-log command;
6. explicit candidate-reference creation and manual acceptance boundary;
7. tutorial verification command;
8. tutorial promotion command;
9. a combined “all 170” operator sequence.

Update Step 10 in `tests.readme.md` from “Not implemented yet” to the actual tutorial procedure.

Document that “all 170” is an orchestration of two isolated suites, not one mixed evidence tree:

```text
137 corpus cases
+ 33 tutorial stages
= 170 executed baselining units
```

Combined reporting may present 170 total units, but suite-specific summary, verification reference, decision log, and promotion eligibility remain distinct.

---

# Operator workflow after implementation

## Tutorial first-time acceptance

1. Define `tutorial_baselining_case`.
2. Run the complete list of 33 tutorial stage/case commands.
3. Generate tutorial summary.
4. Generate tutorial decision-log report.
5. Review every result and the generated report.
6. Explicitly write the **candidate** tutorial verification JSON.
7. Review and commit/accept that JSON as the tutorial current-state contract.
8. Do not promote any case until its classification and evidence are manually approved.

## Tutorial ordinary regression rerun

1. Run the same 33 commands.
2. Regenerate tutorial summary and decision log.
3. Verify against the already accepted tutorial reference.
4. Investigate any non-matched report entry; do not refresh the reference merely to make verification pass.
5. Promote only reviewed, stable eligible matches.

## All-170 run

1. Run the 137 corpus list into the corpus evidence root.
2. Run the 33 tutorial list into the tutorial evidence root.
3. Generate both suite reports.
4. Verify each suite against its own reviewed reference.
5. Generate an optional combined dashboard/report only after both independent verifications pass.
6. Promote only with the explicit suite-specific promotion command.

---

# Decisions confirm

1. **Separate evidence and reference domains:** retain the 137-case paths unchanged; use a new tutorial root/reference/log/checklist.
2. **Honest tutorial classifications:** use `matched_tutorial_reference` / `mismatch_tutorial_reference`, not `*_snopt`, unless tutorial provenance establishes the historical reference solver.
3. **Two full fresh attempts:** replay plus eligible refinement runs twice per tutorial case; the replay-only deliberate-infeasible case remains intentionally replay-only in both attempts.
4. **Combined reporting, not combined verification references:** “170 total” is a top-level operational report; acceptance remains two independent suite-specific verification contracts.
