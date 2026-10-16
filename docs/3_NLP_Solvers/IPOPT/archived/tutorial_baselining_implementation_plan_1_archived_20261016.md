## Review of updates

Your updates are sound and improve the separation from the completed 137-case corpus.

### Accepted tutorial suite locations

| Concern | Agreed location |
|---|---|
| Replaceable tutorial baselining evidence | `testatron/ipopt/tests/benchmarks/baselining/` |
| Tutorial baselining execution policy | `tutorial_baselining_policy.json` |
| Tutorial current-state numeric policy | `tutorial_baselining_verification_policy.json` |
| Accepted tutorial current-state contract | `tutorial_baselining_verification.json` |

The three JSON files are currently empty placeholders. That is appropriate during planning: they must remain unwritten until their schemas, policies, and acceptance workflow are implemented and reviewed.

Using `benchmarks/baselining` is valid because it is a distinct child of the existing benchmark artifact area; it does not collide with the corpus evidence under `testatron/ipopt/tests/tests/baselining/`.

One correction is needed in the copied plan before implementation: its “tutorial-specific parallel layout” still describes the superseded `testatron/ipopt/tests/tutorials/` destination. The implementation must use your `benchmarks/baselining` destination everywhere instead.

---

# Revised implementation plan

## Core invariant

The tutorial suite is **33 executable stages across 17 tutorial cases**:

- 17 replay stages;
- 16 refinement stages;
- 1 intentional replay-only deliberate-infeasible case.

The operator-facing baselining unit should be a **tutorial case**, not an isolated stage. A selected case command executes its applicable stages within each of two fresh attempts.

Therefore, the final command list should contain **17 tutorial case commands** which together produce and verify **33 tutorial stage outcomes**. This preserves the existing baselining meaning of a case:

```text
attempt 1: replay -> eligible refinement
attempt 2: replay -> eligible refinement
repeatability comparison
final case result
```

A list of 33 independent stage commands would split replay/refinement evidence from its case, weaken promotion safety, and depart from the established 137-case workflow.

---

## Phase 0 — Lock the suite boundary and output contract

**Purpose:** prevent accidental mixing of the corpus, benchmark artifacts, and tutorial evidence.

### Decisions to implement

1. Leave every existing corpus path and command unchanged:
   - `testatron/ipopt/tests/tests/baselining/`;
   - `baselining_policy.json`;
   - `baselining_verification_policy.json`;
   - `baselining_verification.json`.

2. Define the tutorial evidence layout as:

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
   └── tutorial_baselining_verification_report.json
   ```

3. Place tutorial JSON contracts exactly as you specified under `testatron/ipopt/tests/`.

4. Place the generated human-readable tutorial decision report under the same IPOPT artifact/configuration area:

   ```text
   testatron/ipopt/tests/tutorial_baselining_case_decision_log.md
   ```

   The existing corpus decision-log report under [`docs/3_NLP_Solvers/IPOPT/`]() remains untouched.

5. Keep the manual tutorial review checklist in documentation, recommended at:

   ```text
   docs/3_NLP_Solvers/IPOPT/tutorial_baselined_checklist.md
   ```

   The report is generated evidence; the checklist is a human-maintained acceptance ledger.

### Required tests

- Unit test that corpus and tutorial roots are distinct.
- Unit test that a tutorial command cannot write under the corpus evidence root.
- Unit test that corpus verification ignores tutorial evidence and still expects exactly 137 corpus cases.
- Unit test that tutorial verification reads only tutorial evidence.

---

## Phase 1 — Build a case-by-case immutable dependency inventory

**Purpose:** treat tutorial inputs as a controlled third-party deployment corpus, rather than assuming all reference-package dependencies are complete.

The existing `TutorialCase` registry in [`ipopt_characterization.py`]() identifies the 17 selected tutorial cases, their source options, reference packages, seed data, hardware roots, universe roots, special seed policies, and stage applicability.

Before baselining behavior is implemented for any case, formalize a per-case immutable inventory containing:

- tutorial case ID;
- source `.emtgopt` hash;
- reference `.emtg` hash;
- seed/XF artifact hash;
- mission package path;
- hardware-model root and every resolved dependency;
- universe root and every resolved dependency;
- required SPICE kernel and ephemeris path;
- expected output name;
- replay and refinement seed source;
- expected taxonomy:
  - authoritative;
  - demonstration;
  - deliberate infeasible;
- applicable stage set;
- any schema-probe requirement;
- per-case timeout;
- dependency status and exact missing-path diagnosis.

### Required dependency behavior

For every case:

1. Resolve dependencies before EMTG is invoked.
2. Copy only declared immutable inputs to the case staging directory.
3. Hash every staged immutable input and preserve source-path provenance.
4. If a required hardware file, universe asset, or SPICE kernel is absent, classify the stage as `dependency_blocked`.
5. Write explicit `compatibility.json` and `result.json` evidence for a blocked case.
6. Never substitute a different universe/kernel/hardware model silently.
7. Do not “fix” a missing reference by modifying files in [`Tutorial_EMTG_Files/`]().

### Required tests

- Parameterized unit tests for all 17 case declarations.
- Unit tests that every declared path is repository-relative and immutable.
- Tests for missing hardware, missing universe, missing ephemeris, and missing seed artifacts.
- Tests that an unresolved dependency yields `dependency_blocked`, never a false solver mismatch or success.
- Tests that provenance records every staged immutable file and its SHA-256.

---

## Phase 2 — Define tutorial-specific policy and normalized evidence

**Purpose:** provide the same durability and auditability as corpus baselining, without claiming unsupported SNOPT provenance.

### Tutorial baselining policy

Implement and validate [`tutorial_baselining_policy.json`]() before it is used.

It should declare at least:

- policy version;
- accepted IPOPT exits;
- deterministic execution environment;
- seeded-refinement settings;
- decision-vector in-bound tolerance;
- replay/refinement timeout and iteration boundaries;
- tutorial comparison policy by taxonomy;
- explicit eligible stage rules;
- calibration/representative cases, if required.

It must be loaded by a tutorial-specific loader, rather than silently reusing the corpus policy.

### Tutorial current-state verification policy

Implement and validate [`tutorial_baselining_verification_policy.json`]().

It should declare the current-state numeric comparison tolerances appropriate to tutorial outputs. It must remain distinct from:

- immutable tutorial-reference acceptance;
- corpus immutable-SNOPT comparison policy;
- corpus current-state verification tolerances.

### Classifications

Retain the accepted terminology:

```text
matched_tutorial_reference
mismatch_tutorial_reference
dependency_blocked
topology_changed
parse_failed
process_failed
timed_out
unstable
```

Only a stable, fully accepted `matched_tutorial_reference` case can be promotion-eligible.

A `mismatch_tutorial_reference` is retained evidence, not an execution failure. A deliberately infeasible replay-only tutorial is valid only when its declared infeasible behavior is reproduced and repeatable.

### Required tests

- Reject empty, malformed, incomplete, or unsupported policy versions.
- Ensure tutorial policy changes do not alter corpus policy loading.
- Test every final tutorial classification.
- Test that a replay-only tutorial cannot be misreported as a missing refinement.
- Test that a refinement-required tutorial cannot be accepted without refinement evidence.

---

## Phase 3 — Implement one normalized two-attempt tutorial runner

**Purpose:** make the actual tutorial execution lifecycle equivalent to the 137-case baselining lifecycle.

The current tutorial test path in [`test_tutorials.py`]() is a one-pass `unreviewed` verifier. It must not simply be relabelled as baselining.

Implement a tutorial baselining runner that, for a selected tutorial case:

### Attempt 1

1. Creates fresh attempt-local staging.
2. Resolves and records dependencies.
3. Runs any required schema probe.
4. Prepares the replay configuration from the declared tutorial seed source.
5. Executes replay without IPOPT.
6. Parses and compares replay output against the immutable tutorial reference.
7. If replay is acceptable and refinement is applicable:
   - prepare refinement from the required seed;
   - run IPOPT refinement;
   - parse the IPOPT log;
   - compare objective, feasibility, topology, state, and declared tutorial-specific checks.
8. Writes attempt-local evidence.

### Attempt 2

Repeat the full applicable pipeline from a fresh staging area. The following must not be treated as reusable proof of repeatability:

- prepared options;
- generated mission files;
- prior schema output;
- prior result files;
- prior seed output.

Reuse of the ordinary compiled EMTG binary in the named Docker build volume remains allowed; that is the normal supported Docker toolchain behavior.

### Finalization

1. Compare the two attempts.
2. Write `repeatability.json`.
3. Derive the final classification.
4. Write normalized final `result.json`.
5. Include:
   - suite ID;
   - case ID;
   - applicable stages;
   - source/reference hashes;
   - dependency compatibility;
   - attempts;
   - replay/refinement states;
   - classification;
   - promotion eligibility.

### Required tests

- Mock/unit tests for attempt lifecycle, result layout, repeatability comparison, and classification derivation.
- Integration-test one representative selected case through the exact Docker launcher.
- Integration-test the special cases:
  - ordinary replay + refinement;
  - deliberate-infeasible replay-only;
  - schema-probe case;
  - current-infeasible-seed case.
- Regression-test that existing corpus attempt layout and classifications remain unchanged.

---

## Phase 4 — Add the tutorial pytest/Docker launcher

**Purpose:** make individual tutorial cases operationally runnable exactly like `baselining_case`.

Add a dedicated pytest option:

```text
--tutorial-baselining-filter <group/case>
```

Add a tutorial launcher test marked consistently with the existing Docker/IPOPT categories. It must:

- build/reuse the normal content-addressed toolchain image;
- reuse the normal build volume;
- run in a disposable container;
- mount repository inputs read-only;
- mount only the selected tutorial evidence root writable;
- use explicit timeout behavior;
- reject a filter matching no tutorial case;
- replace only the selected tutorial case evidence directory;
- preserve all other tutorial evidence;
- not run concurrently with corpus baselining against the same build volume.

The terminal function will follow the existing corpus pattern:

```zsh
tutorial_baselining_case() {
  EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/benchmarks" \
  python -m pytest <tutorial-baselining-launcher> -q \
    --tutorial-baselining-filter "$1"
}
```

The precise test target is an implementation detail; the important contract is that evidence lands under `benchmarks/baselining`, not under the ordinary benchmark result directories.

### Required tests

- A selected tutorial case creates exactly the required two-attempt tree.
- A selected case replacement removes stale files in only that case root.
- A nonmatching filter fails explicitly.
- The launcher cannot write to corpus evidence.
- Existing `pytest -m tutorials` behavior remains available until it is deliberately migrated or retired by a separately reviewed decision.

---

## Phase 5 — Implement tutorial reporting and verification

**Purpose:** create the required full reporting and current-state regression contract.

### Summary

Add tutorial summary generation with output:

```text
testatron/ipopt/tests/benchmarks/baselining/tutorial-baselining-summary.json
```

It must report:

- 17 tutorial case count;
- 33 expected stage count;
- classification counts;
- missing/incomplete case and stage detection;
- separate count of replay-only deliberate-infeasible cases;
- source/reference/dependency provenance status.

### Generated decision log

Generate:

```text
testatron/ipopt/tests/tutorial_baselining_case_decision_log.md
```

It must render every tutorial case, each applicable stage, both attempts, repeatability conclusion, dependency compatibility, classification, and promotion eligibility.

### Verification candidate and gate

Add explicit operations analogous to corpus baselining:

```text
--write-tutorial-baselining-verification
--verify-tutorial-baselining
```

The first command writes the candidate to:

```text
testatron/ipopt/tests/tutorial_baselining_verification.json
```

It must **never** run automatically after a tutorial batch.

The verifier must compare fresh evidence to the accepted tutorial reference and reject:

- missing or unexpected case/stage evidence;
- incomplete stage layout;
- source/reference hash changes;
- dependency-compatibility changes;
- replay/refinement execution changes;
- topology changes;
- repeatability failures;
- numeric drift beyond tutorial verification policy.

### Required tests

- Candidate generation requires explicit action.
- A 33-stage reference cannot be mistaken for a 17-record-only reference.
- Every accepted verification record identifies both tutorial case and stage.
- One changed number, hash, stage exit, topology item, or dependency mapping fails verification.
- Corpus verification still yields 137-case behavior unchanged.

---

## Phase 6 — Add suite-specific promotion

**Purpose:** allow reviewed tutorial evidence to be curated without altering immutable tutorial packages.

Recommended curated tutorial destination:

```text
testatron/ipopt/tests/benchmarks/tutorial-promoted/<group>/<case>/
```

This is deliberately separate from:

- immutable inputs/references in [`Tutorial_EMTG_Files/`]();
- replaceable execution evidence in [`benchmarks/baselining/`]();
- existing non-tutorial benchmark results.

Promotion must require:

```text
explicit suite selection
+ explicit --approve-baseline
+ stable repeatability
+ matched_tutorial_reference
+ approved immutable hashes/provenance
```

It must refuse:

- mismatches;
- unstable results;
- blocked cases;
- replay-only cases unless their promotion policy explicitly permits them;
- silent replacement of an existing curated result.

### Required tests

- Promotion eligibility only for stable tutorial matches.
- Immutable tutorial files remain hash-identical before and after promotion.
- Existing corpus promotion behavior remains unchanged.
- Replacing a curated tutorial result requires explicit replacement authorization.

---

## Phase 7 — Update operator documentation and provide all-170 orchestration

Update [`baselining_commands.md`]() with two clearly separated sections:

1. **137-case Testatron corpus**
2. **17 tutorial case commands / 33 tutorial stages**

The tutorial section will include:

1. terminal function;
2. complete ordered list of 17 tutorial case commands;
3. statement that they execute 33 stage results;
4. tutorial summary command;
5. decision-log command;
6. candidate-reference creation command and manual acceptance warning;
7. ordinary verification command;
8. promotion command;
9. artifact locations;
10. review checklist procedure.

Update Step 10 in [`tests.readme.md`]() from “Not implemented yet.”

“All 170” is then documented as:

```text
137 corpus case results
+ 33 tutorial stage results
= 170 baselining execution units
```

It is an operator orchestration of two independently verified suites—not one shared output root, one verification reference, or one promotion namespace.

---

# Case-by-case implementation and acceptance order

To match your requested controlled rollout, do **not** jump directly to the 33-stage tutorial run.

For each tutorial case, in registry order:

1. implement/validate its static dependency inventory;
2. add the focused unit tests for its special requirements;
3. run its selected tutorial baselining launcher only after implementation review;
4. inspect staged options, provenance, replay/refinement output, logs, and hashes;
5. resolve missing dependency handling explicitly;
6. record its expected classification and promotion eligibility;
7. move to the next case only after the preceding case’s behavior is understood.

After all 17 cases are implemented and individually reviewed:

1. run the complete 17-command / 33-stage tutorial sequence;
2. generate the tutorial summary and decision log;
3. inspect all evidence;
4. explicitly create the tutorial verification candidate;
5. review and accept it as the committed tutorial current-state contract;
6. rerun the complete sequence;
7. require tutorial verification to pass against that accepted contract.

Only after that second complete, verified run should tutorial promotion be enabled as an operational workflow.
