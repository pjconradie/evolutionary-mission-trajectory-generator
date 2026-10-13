
Build a fully open-source EMTG for `python:3.12-slim-bookworm` by replacing the mandatory SNOPT adapter with IPOPT, preserving EMTG's existing NLP scaling, sparse derivatives, MBH behavior, and legacy option-file compatibility. Add a headless Python subprocess interface and validate the OSIRIS-REx workflow against both committed solution files.

---
Version 2

# Plan: Open-Source EMTG Container

First establish and record the behavior of the unmodified repository that can be verified without SNOPT. Because no current executable or licensed SNOPT artifact is available, native optimizer execution is an explicit blocked check rather than an assumed pass. Then build a fully open-source EMTG for `python:3.12-slim-bookworm` by replacing the mandatory SNOPT adapter with IPOPT, preserving EMTG's existing NLP scaling, sparse derivatives, MBH behavior, and legacy option-file compatibility. Add a headless Python subprocess interface and validate the OSIRIS-REx workflow against both committed solution files.


**Phase 0 execution status (2026-09-10)**
- Verified repository branch `local-opensource-IPOPT` at commit `5e8817f7ecd51242684359ca8e23d1e55f3895c0` from Git metadata. Worktree cleanliness remains pending because this planning session has no shell executor.
- Verified no repository `EMTG-Config.cmake`, no `CMakeCache.txt`, and no native `EMTGv9` artifact. Root CMake includes `EMTG-Config.cmake` before checking `SNOPT_ROOT_DIR`; therefore an unchanged configure first fails on the missing user config. The SNOPT fatal gate is confirmed in source, while its executed diagnostic remains pending a temporary config.
- The user’s Python/Testatron run successfully imported `MissionOptions` and `Mission`, transitively exercising `JourneyOptions`, `Journey`, and `MissionEvent`; it emitted non-fatal Python invalid-escape warnings. VS Code reports no diagnostics in those five modules.
- Verified the OSIRIS source options declare mission `OSIRIS-REx`, two journeys (`Earth_to_Bennu`, `Bennu_to_Earth`), `NLP_solver_type 0`, `MBH_max_trials 1000000`, `MBH_max_run_time 60`, `seed_MBH 0`, `MBH_RNG_seed -1`, and Windows universe/hardware/output paths.
- Verified exactly 137 committed Testatron truth `.emtg` files exist. Their complete runtime parse remains pending; the previous failed Testatron run parsed options but did not execute EMTG, and its timestamped output has since been removed.
- Verified directly from the mandatory baselines: 2022 has delta-v `12.39626561567155 km/s`, total duration `4.033300166050676 years`, journey durations `457.83732226` and `284.82555470 days`, final mass `5.733518194815262 kg`, and worst violation `4.9086793289867e-7`; 2024 has delta-v `7.12363247375915 km/s`, total duration `6.735018978610118 years`, journey durations `1179.32045074` and `550.14523120 days`, final mass `59.389155681089484 kg`, and worst violation `8.77916857574499e-6`. Both have the expected two journey names and the same non-coast event types, though event counts/epochs differ.
- Pending executable gates: exact Python/platform/CMake/compiler versions, `git status`, temporary option round-trip comparison, parsing all 137 truths with `Mission`, both Comparatron self-checks, expected cross-baseline mismatch report, and controlled CMake configure. Phase 0 is not yet accepted.

**Steps**
- User decision: hand Phase 0 execution to Agent mode, but require explicit user permission before every executable/command. Before each command, present the exact command, purpose, expected filesystem effects, and cleanup; do not batch commands under one approval unless the user explicitly permits it. Repository source and committed truth files remain read-only, and `--update_truths` is forbidden.


## Phase 0: Verify and freeze current behavior
**EXECUTION: 2026-09-10 | Status: COMPLETE — GO TO PHASE 1**

1. ✓ Recorded branch `local-opensource-IPOPT`, clean final worktree, Python 3.13.1, NumPy 2.5.3, pandas 3.0.5, and absence of a native `EMTGv9`/configured CMake build.
2. ✓ Verified headless PyEMTG imports through the characterization suite.
3. ✓ Verified OSIRIS-REx options parse/write/reparse preserves mission identity, two journeys, solver/MBH settings, and paths.
4. ✓ Parsed all 137 Testatron truths and both mandatory OSIRIS baselines; froze topology and key numerical metrics.
5. ✓ Verified both Comparatron self-comparisons; documented the cross-comparison pandas 3 incompatibility as one strict xfail.
6. ✓ Native execution: **BLOCKED AS EXPECTED** because no SNOPT build/source/license is available.
7. ✓ Added and ran the reusable pytest characterization suite: `143 passed, 1 xfailed`.
8. ✓ Final worktree check is clean; Phase 0 baseline accepted. Full native Testatron execution remains deferred until the IPOPT executable exists.

**Phase 0 characterization-test implementation (complete)**
1. Add `pytest.ini` with `testpaths = tests` so pytest does not collect the legacy Windows-path scripts in `PyEMTG/test_PyMissionOptions.py` and `OptionsOverhaul/test_missionoptions.py`.
2. Add `tests/conftest.py` to expose repository-relative paths, PyEMTG imports, the 137 truth paths, and the two named OSIRIS baseline paths without changing package layout or production code.
3. Separate tests by function, using descriptive module docstrings, test names, parameter IDs, and assertion messages:
   - `tests/test_mission_options.py`: verify OSIRIS options parse/write/reparse preserves mission identity, solver/MBH settings, path values, and journey order using `tmp_path`.
   - `tests/test_mission_parser.py`: verify exactly 137 committed Testatron truths exist; parametrize and parse every truth independently; parse both named OSIRIS baselines and assert mission/journey topology plus the frozen delta-v, flight-time, journey-duration, final-mass, and worst-violation metrics.
   - `tests/test_comparatron.py`: parametrize the two passing self-comparisons; add one `pytest.mark.xfail(strict=True, raises=AttributeError, reason=...)` cross-comparison documenting pandas 3 removal of `DataFrame.append`.
4. Continue using the existing `testatron/requirements.txt` as the single Python dependency manifest and add pytest there. Do not create `requirements-dev.txt`. Do not add or alter native EMTG/Testatron execution, source options, truth files, or production parser code in this slice.
5. Validation result: `pytest -q` completed with `143 passed, 1 xfailed`. The strict xfail is the known pandas 3 `DataFrame.append` incompatibility in cross-baseline Comparatron; self-comparisons pass. Four non-failing pandas deprecation warnings identify `merge(..., copy=False)` cleanup for the same future Comparatron compatibility change.


## Phase 1: Probe the current build and prepare the Linux toolchain
1. In a disposable Debian 12 builder, create the repository-local `EMTG-Config.cmake` from the template with valid bundled CSPICE paths and system Boost/GSL paths but an intentionally absent `SNOPT_ROOT_DIR`. Run CMake unchanged and require the documented fatal error `SNOPT directory specified (...) does not exist`. This proves only that CMake starts and SNOPT is the first configuration gate; it is not a compile or runtime test.
2. Independently verify the non-solver Linux prerequisites in `python:3.12-slim-bookworm`: install the intended compiler/CMake, `pkg-config`, `csh`, Debian Boost filesystem/system/serialization development libraries, GSL development libraries, and `coinor-libipopt-dev`; build bundled CSPICE from its supplied Unix script; and compile/link one disposable probe against all four dependency families. The probe must call `boost::filesystem` on a temporary path, evaluate one known GSL function, call one CSPICE routine after loading a bundled kernel, and create/initialize an IPOPT application. This isolates package/ABI problems before EMTG source refactoring.
3. Accept Phase 1 only when: all expected package versions and target architecture are recorded; CSPICE produces its Unix static library; `pkg-config` resolves IPOPT; the combined probe compiles with warnings treated as errors, runs with exit code 0, and resolves every dynamic library (`ldd` contains no `not found`); a clean unchanged EMTG CMake configure reaches the expected missing-SNOPT fatal error and no earlier dependency/configuration failure; and no repository source or truth files are modified. Do not add a fake SNOPT implementation.

## Phase 2: Make the optimizer boundary solver-neutral
4. Extend `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/NLP_interface.h` with a solver-neutral convergence status enum/accessor and any iteration-result data MBH needs; preserve `run_NLP()`, incumbent vectors, EMTG scaling, and feasibility metrics. Correct `getFupperbounds()` so it returns `Fupperbounds` rather than `Flowerbounds`.
5. Change `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/monotonic_basin_hopping.h`, `.cpp`, `/src/InnerLoop/FilamentWalker.h`, and `.cpp` to depend on `NLP_interface*`, rename SNOPT-specific members/messages/artifacts to NLP-neutral terms, and replace `getInform() < 10` with the new convergence status. Preserve EMTG's own post-evaluation feasibility checks as the authoritative MBH acceptance rule.
6. Add an NLP solver factory under `/src/InnerLoop/` and update the three hard-coded construction sites in `/src/Core/problem.cpp` (MBH, direct NLP, and FilamentWalker) to request an `NLP_interface` implementation. Add CMake solver feature selection in the same slice; until IPOPT exists, an IPOPT selection may stop with an explicit `adapter not implemented` configure error, while unknown solver names must be rejected.
7. Accept Phase 2 only when: `monotonic_basin_hopping.*`, `FilamentWalker.*`, and `problem.cpp` no longer name or include `SNOPT_interface`; all solver consumers hold `NLP_interface` or factory-owned polymorphic objects; no consumer interprets numeric SNOPT inform codes; `getFupperbounds()` has a focused test proving distinct lower/upper vectors are returned correctly; a fake recording implementation of `NLP_interface` proves generic `setX0`, `run_NLP`, result retrieval, and each convergence-status branch without linking SNOPT/IPOPT; the three factory call sites compile in a solver-independent object-library target; and unsupported solver selection fails during CMake configuration with a clear diagnostic. Full `EMTGv9` linkage is not required until Phase 3.

## Phase 3: Implement and test IPOPT
8. Add `/src/InnerLoop/IPOPT_interface.h` and `.cpp` implementing IPOPT's `TNLP` callbacks: variable/constraint bounds, objective, objective gradient, constraints, combined linear/nonlinear sparse Jacobian, initial point, and final solution. Translate IPOPT's scaled variables to EMTG's unscaled `problem::evaluate()` inputs, preserve analytical derivatives and incumbent tracking, use limited-memory Hessian approximation, and map IPOPT statuses into the solver-neutral enum.
9. Map existing `NLPoptions` values to IPOPT: feasibility tolerance to `constr_viol_tol`, optimality tolerance to `tol`, major iteration limit to `max_iter`, runtime to `max_cpu_time`, quiet mode to `print_level`, and derivative checks to IPOPT/EMTG derivative validation. Disable IPOPT's extra NLP scaling initially so EMTG remains the sole scaling authority.
10. Complete root `/CMakeLists.txt` IPOPT discovery using `pkg-config` or an imported target; update `/src/InnerLoop/CMakeLists.txt` to compile the IPOPT adapter and factory. Make IPOPT the default open-source solver and keep legacy `snopt_*` mission-option names as compatibility aliases; do not rewrite all generated option schemas in the first milestone.
11. Add a deterministic adapter fixture with EMTG rows `F[0]` objective, `F[1]` linear equality, and `F[2]` nonlinear inequality:
    - minimize `(x - 1)^2 + (y - 2)^2`
    - subject to `x + y = 3`, represented in `A`
    - subject to `x*y >= 2`, represented in `G`
    - bounds `0 <= x <= 10`, `0 <= y <= 4`; scale factors `10` and `4`; deliberately infeasible starting point `(8, 0.25)`
    - exact optimum `(x, y) = (1, 2)`, objective `0`, with both constraints active.
12. Test the adapter callbacks directly before asking IPOPT to solve: assert dimensions `n=2`, `m=2`; scaled variable bounds `[0,1]` for both variables; constraint bounds equality `[3,3]` and inequality `[2,+inf)`; linear entries at rows/columns `(F1,x)` and `(F1,y)` both `1`; nonlinear sparsity entries for objective `(F0,x),(F0,y)` and product `(F2,x),(F2,y)` exactly once each; at `(1,2)`, objective gradient `(0,0)` and product derivatives `(2,1)`; all values agree with central finite differences to relative/absolute tolerance `1e-7`; and callback counters prove objective, gradient, constraints, and Jacobian paths were invoked.
13. Accept the successful solve when IPOPT returns `Solve_Succeeded` or `Solved_To_Acceptable_Level`, the solver-neutral status is `Converged`, `|x-1|` and `|y-2| <= 1e-6`, objective `<= 1e-10`, equality residual `<= 1e-8`, inequality violation `<= 1e-8`, returned scaled/unscaled vectors are mutually consistent to `1e-12`, and the final values copied into `NLP_interface`/incumbent storage match IPOPT's final solution. Add two status tests: make the fixture infeasible with `x+y=3` and `x*y>=3` and require the solver-neutral `Infeasible` classification; set a zero/one-iteration limit and require `IterationLimit` without accepting the point as converged.
14. Build the complete IPOPT-only `EMTGv9`; require `ldd` to resolve all libraries and contain IPOPT but no SNOPT symbols/libraries. Run one deterministic direct-NLP Testatron case first, requiring process exit 0, a parseable `.emtg`, reported worst constraint violation `<=1e-5`, and no NaN/Inf in X/F/G. Then run a bounded fixed-seed MBH case, requiring at least two completed NLP attempts, deterministic repeated summary metrics, retained best feasible incumbent, clean timeout/iteration termination, and a parseable feasible `.emtg`. Only after these pass run all 137 Testatron cases and OSIRIS-REx.

## Phase 4: Add the Debian 12 container
8. Add a root `/Dockerfile` using `python:3.12-slim-bookworm` for both builder and runtime stages. The builder installs `build-essential`, `cmake`, `pkg-config`, `csh`, `coinor-libipopt-dev`, Debian Boost development components, and GSL development files; builds bundled CSPICE; configures EMTG in Release/background mode; and compiles `EMTGv9`. Prefer Debian Boost/GSL packages over repository prebuilt binaries to avoid architecture/ABI assumptions.
9. In the final `python:3.12-slim-bookworm` stage, install only IPOPT, Boost, GSL, C++/Fortran runtime libraries and required headless Python packages; copy `EMTGv9`, PyEMTG parsing modules, and required tutorial data. Add `/Dockerfile` health/smoke checks using `ldd` and `EMTGv9` invocation, and add `/.dockerignore` to exclude build products, Windows binaries, result churn, and unrelated large artifacts without excluding OSIRIS inputs/baselines.
10. Define stable paths: executable `/opt/emtg/bin/EMTGv9`, package/data root `/opt/emtg`, mission input `/missions`, generated portable options `/work`, and output `/output`. Run as a non-root user and make `/missions` read-only by convention while `/output` remains writable.

## Phase 5: Add the Python CLI boundary
11. Add `/PyEMTG/EMTGRunner.py` (or the nearest repository naming convention) with a typed runner that loads `MissionOptions`, rewrites `universe_folder`, `HardwarePath`, gravity-file paths, working-directory/subfolder flags, and background mode, writes a generated portable `.emtgopt`, invokes `EMTGv9` with `subprocess.run([...], shell=False)`, applies timeout/error handling, locates the produced `.emtg`, and parses it with `Mission.Mission`.
12. Provide a Python CLI around that runner accepting input options, output directory, executable, universe, hardware, timeout, optional RNG seed, and comparison baselines. Return nonzero status for process failure, missing/unparseable output, or failed validation, and emit a machine-readable JSON summary suitable for a later service layer. Do not add an HTTP API in this milestone.
13. Add focused Python tests for path rewriting (including Windows backslashes), command construction, timeout/failure propagation, output discovery, and parsing. Use a fake executable for unit tests and the built EMTG binary only for integration tests.

## Phase 6: Reproduce and compare OSIRIS-REx
14. Use `/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/OSIRIS-REx.emtgopt` as immutable source input. At runtime, rewrite its Windows universe, hardware, and result paths to container paths; retain the tutorial's mission definition, SplineEphem setup, hardware models, and SPICE kernels from `/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS_universe/`.
15. Add an OSIRIS comparison command/test that always parses the new result and both mandatory baselines:
   - `/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/results/OSIRIS-REx_11272022_144557/OSIRIS-REx_Sun(EEB)_Sun(BE).emtg`
   - `/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/results/OSIRIS-REx_412024_11530/OSIRIS-REx_Sun(EEB)_Sun(BE).emtg`
16. Require exact mission/journey names and non-coast event topology, a parseable feasible result, and worst normalized constraint violation no greater than the tutorial tolerance `1e-5`. Generate deltas to each baseline for total deterministic delta-v, total flight time, each journey flight time, final mass, launch/arrival epochs, and key boundary events; do not compare intermediate coast states point-for-point.
17. Use the two known solutions as the initial numerical acceptance envelope, expanded by 5%: positive total delta-v no worse than `13.0161 km/s`; Journey 0 duration `434.95–1238.29 days`; Journey 1 duration `270.58–577.65 days`; total duration `3.8316–7.0718 years`; final mass `5.4468–62.3586 kg`. Always report distance to both baselines even when the envelope passes. Recalibrate only after collecting repeatable IPOPT runs, with any threshold change documented rather than silently updating truth data.
18. Run an unseeded tutorial-equivalent integration to demonstrate the documented workflow, plus a fixed-seed bounded-runtime variant for repeatable CI diagnostics. The fixed-seed run verifies determinism of the containerized pipeline; it is not expected to reproduce either stochastic SNOPT solution byte-for-byte.

## Phase 7: Documentation and release checks
19. Update `/README.opensource` with Debian 12 Docker build/run instructions, IPOPT substitution and expected numerical differences, Python CLI examples, volume layout, and both OSIRIS baseline paths. Update SNOPT-centric developer documentation under `/docs/shared_latex_inputs/` and `/docs/1_Developers/software_design_document/inner_loop/` to describe the new solver-neutral architecture and IPOPT defaults.
20. Produce a clean-image verification record: build from a fresh checkout, inspect dynamic linkage for absence of SNOPT, run unit tests, run a short solver integration, execute OSIRIS-REx, compare against both baselines, and confirm generated outputs are owned by the host-compatible container user.

**Relevant files**
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/CMakeLists.txt` — remove mandatory SNOPT configuration; discover IPOPT and system dependencies.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/Core/problem.cpp` — replace three concrete SNOPT constructions with the solver factory.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/NLP_interface.h` — solver-neutral status contract and upper-bound accessor fix.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/NLP_interface.cpp` — shared scaling/incumbent behavior reused by IPOPT.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/SNOPT_interface.h` and `.cpp` — behavioral reference for callbacks and incumbent tracking; excluded/removed from open-source build.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/monotonic_basin_hopping.h` and `.cpp` — remove direct SNOPT type and inform-code dependency.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/FilamentWalker.h` and `.cpp` — consume generic NLP interface.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/CMakeLists.txt` — register IPOPT adapter/factory sources.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/PyEMTG/MissionOptions.py` — existing portable option reader/writer.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/PyEMTG/Mission.py` — existing result parser; reuse rather than inventing a second `.emtg` parser.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/testatron/testatron.py` — reference path-rewrite and regression execution pattern.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/OSIRIS-REx.emtgopt` — immutable tutorial mission source.
- Both OSIRIS-REx `.emtg` result files specified in Step 15 — mandatory numerical and structural baselines.

**Verification**
1. Before edits, run the Phase 0 parser/data baseline and save a report containing environment metadata, option round-trip results, all truth-file parse results, both OSIRIS metric manifests, self-comparison passes, the expected 2022-vs-2024 comparison failure, and the explicit native-execution blocker.
2. Configure a clean Debian builder with no `SNOPT_ROOT_DIR`; CMake must succeed with IPOPT and `ldd bin/EMTGv9` must show no `snopt` library.
3. Run focused Python unit tests for the runner and baseline comparator.
4. Run one direct NLP regression and one bounded MBH regression, checking return status, feasibility `<=1e-5`, and parseable `.emtg` output.
5. Build `docker build --target runtime` from a clean context and run the image with read-only mission inputs and a writable output mount.
6. Run OSIRIS-REx in tutorial-equivalent and fixed-seed modes; compare every produced result to both mandatory baselines and archive the JSON comparison report.
7. Repeat the fixed-seed run twice and verify identical decision/summary metrics within floating-point serialization tolerance.

**Decisions**
- Current-state verification comes first. Python parsers, options, committed truths, and comparators can be executed now; native optimizer execution is blocked because no current EMTG binary or SNOPT artifact is available.
- Base and final image: official `python:3.12-slim-bookworm` (Debian 12).
- Open-source NLP solver: IPOPT; SNOPT is proprietary and has no open-source edition.
- Python interface: CLI/subprocess wrapper using existing PyEMTG option/output classes; no in-process Boost Python or HTTP service initially.
- Both committed OSIRIS-REx `.emtg` files are mandatory baselines.
- Numerical equality with SNOPT is not expected; feasibility and mission topology are hard gates, with aggregate metrics compared against the explicit two-baseline envelope.
- Legacy `snopt_*` option names remain accepted in the first milestone to preserve existing `.emtgopt` compatibility.

**Scope boundaries**
- Included: IPOPT replacement, Debian container, headless Python runner, OSIRIS reproduction, dual-baseline comparison, and build/run documentation.
- Excluded: PyEMTG wxPython GUI, HTTP/job service, plotting, exact SNOPT trajectory reproduction, broad option-schema renaming, and unrelated refactors.


---
Version 1

# Plan: Open-Source EMTG Container

Target `python:3.12-slim-bookworm`, replace proprietary SNOPT with IPOPT, expose EMTG through a Python CLI wrapper, and validate OSIRIS-REx against both committed solutions.

## Implementation Phases

### 1. Solver-Neutral Interface

- Add generic convergence statuses to `NLP_interface.h`.
- Change MBH and FilamentWalker from `SNOPT_interface*` to `NLP_interface*`.
- Replace SNOPT inform-code checks.
- Fix `getFupperbounds()` incorrectly returning lower bounds.

### 2. IPOPT Integration

- Add `IPOPT_interface` implementing objective, constraint, gradient, and sparse Jacobian callbacks.
- Preserve EMTG scaling, feasibility checks, incumbent tracking, and MBH behavior.
- Add a solver factory and update the three constructions in `problem.cpp`.
- Keep legacy `snopt_*` option names as compatibility aliases.

### 3. Build System

- Remove mandatory SNOPT detection from `CMakeLists.txt`.
- Discover Debian's `coinor-libipopt-dev`.
- Use Debian Boost and GSL packages while continuing to build bundled CSPICE.

### 4. Docker

- Add a multi-stage `Dockerfile` based entirely on `python:3.12-slim-bookworm`.
- Install only runtime libraries in the final stage.
- Use `/opt/emtg`, `/missions`, `/work`, and `/output`.
- Run as a non-root user.
- Confirm with `ldd` that the executable has no SNOPT dependency.

### 5. Python Interface

- Add a runner around `MissionOptions.py` and `Mission.py`.
- Rewrite Windows paths without changing the source tutorial file.
- Execute `EMTGv9` using `subprocess.run(..., shell=False)`.
- Produce a machine-readable JSON result and comparison report.

### 6. OSIRIS-REx Validation

- Preserve the tutorial mission, hardware, SplineEphem configuration, and SPICE data.
- Compare every run against both mandatory baselines:
  - `docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/results/OSIRIS-REx_11272022_144557/OSIRIS-REx_Sun(EEB)_Sun(BE).emtg`
  - `docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/results/OSIRIS-REx_412024_11530/OSIRIS-REx_Sun(EEB)_Sun(BE).emtg`

## Acceptance Criteria

- Exact mission and journey names.
- Exact non-coast event topology.
- Worst constraint violation less than or equal to `1e-5`.
- Parseable and feasible `.emtg` output.
- Report differences from both baselines for:
  - Total delta-v
  - Journey and total flight times
  - Final mass
  - Launch and arrival epochs
  - Key boundary events

### Initial Acceptance Envelope

| Metric | Accepted range |
|---|---:|
| Total delta-v | `0 < delta-v <= 13.0161 km/s` |
| Journey 0 duration | `434.95–1238.29 days` |
| Journey 1 duration | `270.58–577.65 days` |
| Total duration | `3.8316–7.0718 years` |
| Final mass | `5.4468–62.3586 kg` |

Both a tutorial-equivalent stochastic run and a fixed-seed repeatability run will be tested.

---

# Implementation Plan: Open-Source EMTG Container

**Steps**

## Phase 1: Make the optimizer boundary solver-neutral
1. Extend `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/NLP_interface.h` with a solver-neutral convergence status enum/accessor and any iteration-result data MBH needs; preserve `run_NLP()`, incumbent vectors, EMTG scaling, and feasibility metrics. Correct `getFupperbounds()` so it returns `Fupperbounds` rather than `Flowerbounds`.
2. Change `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/monotonic_basin_hopping.h`, `.cpp`, `/src/InnerLoop/FilamentWalker.h`, and `.cpp` to depend on `NLP_interface*`, rename SNOPT-specific members/messages/artifacts to NLP-neutral terms, and replace `getInform() < 10` with the new convergence status. Preserve EMTG's own post-evaluation feasibility checks as the authoritative MBH acceptance rule.
3. Add an NLP solver factory under `/src/InnerLoop/` and update the three hard-coded construction sites in `/src/Core/problem.cpp` (MBH, direct NLP, and FilamentWalker) to request an `NLP_interface` implementation. This blocks Phase 2 and is independently verified by compiling the refactor before SNOPT removal.

## Phase 2: Implement IPOPT and remove the proprietary build requirement
4. Add `/src/InnerLoop/IPOPT_interface.h` and `.cpp` implementing IPOPT's `TNLP` callbacks: variable/constraint bounds, objective, objective gradient, constraints, combined linear/nonlinear sparse Jacobian, initial point, and final solution. Translate IPOPT's scaled variables to EMTG's unscaled `problem::evaluate()` inputs, preserve analytical derivatives and incumbent tracking, use limited-memory Hessian approximation, and map IPOPT statuses into the solver-neutral enum.
5. Map existing `NLPoptions` values to IPOPT: feasibility tolerance to `constr_viol_tol`, optimality tolerance to `tol`, major iteration limit to `max_iter`, runtime to `max_cpu_time`, quiet mode to `print_level`, and derivative checks to IPOPT/EMTG derivative validation. Disable IPOPT's extra NLP scaling initially so EMTG remains the sole scaling authority.
6. Replace unconditional SNOPT discovery/linkage in the root `/CMakeLists.txt` with Debian-compatible IPOPT discovery, preferably `pkg-config`/an imported target for `ipopt`; update `/src/InnerLoop/CMakeLists.txt` to compile the IPOPT adapter and factory. Remove proprietary SNOPT from the default/open-source target. Keep parsing the legacy `snopt_feasibility_tolerance`, `snopt_optimality_tolerance`, and related fields in mission options as compatibility aliases; do not rewrite all generated option schemas in the first milestone.
7. Build and run a small direct-NLP/testatron case before MBH. Then run a bounded MBH case to verify repeated IPOPT solves, status mapping, incumbent retention, sparse Jacobian indexing, timeout behavior, and feasible-solution output.

## Phase 3: Add the Debian 12 container
8. Add a root `/Dockerfile` using `python:3.12-slim-bookworm` for both builder and runtime stages. The builder installs `build-essential`, `cmake`, `pkg-config`, `csh`, `coinor-libipopt-dev`, Debian Boost development components, and GSL development files; builds bundled CSPICE; configures EMTG in Release/background mode; and compiles `EMTGv9`. Prefer Debian Boost/GSL packages over repository prebuilt binaries to avoid architecture/ABI assumptions.
9. In the final `python:3.12-slim-bookworm` stage, install only IPOPT, Boost, GSL, C++/Fortran runtime libraries and required headless Python packages; copy `EMTGv9`, PyEMTG parsing modules, and required tutorial data. Add `/Dockerfile` health/smoke checks using `ldd` and `EMTGv9` invocation, and add `/.dockerignore` to exclude build products, Windows binaries, result churn, and unrelated large artifacts without excluding OSIRIS inputs/baselines.
10. Define stable paths: executable `/opt/emtg/bin/EMTGv9`, package/data root `/opt/emtg`, mission input `/missions`, generated portable options `/work`, and output `/output`. Run as a non-root user and make `/missions` read-only by convention while `/output` remains writable.

## Phase 4: Add the Python CLI boundary
11. Add `/PyEMTG/EMTGRunner.py` (or the nearest repository naming convention) with a typed runner that loads `MissionOptions`, rewrites `universe_folder`, `HardwarePath`, gravity-file paths, working-directory/subfolder flags, and background mode, writes a generated portable `.emtgopt`, invokes `EMTGv9` with `subprocess.run([...], shell=False)`, applies timeout/error handling, locates the produced `.emtg`, and parses it with `Mission.Mission`.
12. Provide a Python CLI around that runner accepting input options, output directory, executable, universe, hardware, timeout, optional RNG seed, and comparison baselines. Return nonzero status for process failure, missing/unparseable output, or failed validation, and emit a machine-readable JSON summary suitable for a later service layer. Do not add an HTTP API in this milestone.
13. Add focused Python tests for path rewriting (including Windows backslashes), command construction, timeout/failure propagation, output discovery, and parsing. Use a fake executable for unit tests and the built EMTG binary only for integration tests.

## Phase 5: Reproduce and compare OSIRIS-REx
14. Use `/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/OSIRIS-REx.emtgopt` as immutable source input. At runtime, rewrite its Windows universe, hardware, and result paths to container paths; retain the tutorial's mission definition, SplineEphem setup, hardware models, and SPICE kernels from `/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS_universe/`.
15. Add an OSIRIS comparison command/test that always parses the new result and both mandatory baselines:
   - `/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/results/OSIRIS-REx_11272022_144557/OSIRIS-REx_Sun(EEB)_Sun(BE).emtg`
   - `/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/results/OSIRIS-REx_412024_11530/OSIRIS-REx_Sun(EEB)_Sun(BE).emtg`
16. Require exact mission/journey names and non-coast event topology, a parseable feasible result, and worst normalized constraint violation no greater than the tutorial tolerance `1e-5`. Generate deltas to each baseline for total deterministic delta-v, total flight time, each journey flight time, final mass, launch/arrival epochs, and key boundary events; do not compare intermediate coast states point-for-point.
17. Use the two known solutions as the initial numerical acceptance envelope, expanded by 5%: positive total delta-v no worse than `13.0161 km/s`; Journey 0 duration `434.95–1238.29 days`; Journey 1 duration `270.58–577.65 days`; total duration `3.8316–7.0718 years`; final mass `5.4468–62.3586 kg`. Always report distance to both baselines even when the envelope passes. Recalibrate only after collecting repeatable IPOPT runs, with any threshold change documented rather than silently updating truth data.
18. Run an unseeded tutorial-equivalent integration to demonstrate the documented workflow, plus a fixed-seed bounded-runtime variant for repeatable CI diagnostics. The fixed-seed run verifies determinism of the containerized pipeline; it is not expected to reproduce either stochastic SNOPT solution byte-for-byte.

## Phase 6: Documentation and release checks
19. Update `/README.opensource` with Debian 12 Docker build/run instructions, IPOPT substitution and expected numerical differences, Python CLI examples, volume layout, and both OSIRIS baseline paths. Update SNOPT-centric developer documentation under `/docs/shared_latex_inputs/` and `/docs/1_Developers/software_design_document/inner_loop/` to describe the new solver-neutral architecture and IPOPT defaults.
20. Produce a clean-image verification record: build from a fresh checkout, inspect dynamic linkage for absence of SNOPT, run unit tests, run a short solver integration, execute OSIRIS-REx, compare against both baselines, and confirm generated outputs are owned by the host-compatible container user.

**Relevant files**
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/CMakeLists.txt` — remove mandatory SNOPT configuration; discover IPOPT and system dependencies.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/Core/problem.cpp` — replace three concrete SNOPT constructions with the solver factory.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/NLP_interface.h` — solver-neutral status contract and upper-bound accessor fix.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/NLP_interface.cpp` — shared scaling/incumbent behavior reused by IPOPT.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/SNOPT_interface.h` and `.cpp` — behavioral reference for callbacks and incumbent tracking; excluded/removed from open-source build.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/monotonic_basin_hopping.h` and `.cpp` — remove direct SNOPT type and inform-code dependency.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/FilamentWalker.h` and `.cpp` — consume generic NLP interface.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/src/InnerLoop/CMakeLists.txt` — register IPOPT adapter/factory sources.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/PyEMTG/MissionOptions.py` — existing portable option reader/writer.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/PyEMTG/Mission.py` — existing result parser; reuse rather than inventing a second `.emtg` parser.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/testatron/testatron.py` — reference path-rewrite and regression execution pattern.
- `/Users/jacoconradie/Documents/GitHub/Surreal Technologies/evolutionary-mission-trajectory-generator/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/OSIRIS-REx.emtgopt` — immutable tutorial mission source.
- Both OSIRIS-REx `.emtg` result files specified in Step 15 — mandatory numerical and structural baselines.

**Verification**
1. Configure a clean Debian builder with no `SNOPT_ROOT_DIR`; CMake must succeed with IPOPT and `ldd bin/EMTGv9` must show no `snopt` library.
2. Run focused Python unit tests for the runner and baseline comparator.
3. Run one direct NLP regression and one bounded MBH regression, checking return status, feasibility `<=1e-5`, and parseable `.emtg` output.
4. Build `docker build --target runtime` from a clean context and run the image with read-only mission inputs and a writable output mount.
5. Run OSIRIS-REx in tutorial-equivalent and fixed-seed modes; compare every produced result to both mandatory baselines and archive the JSON comparison report.
6. Repeat the fixed-seed run twice and verify identical decision/summary metrics within floating-point serialization tolerance.

**Decisions**
- Base and final image: official `python:3.12-slim-bookworm` (Debian 12).
- Open-source NLP solver: IPOPT; SNOPT is proprietary and has no open-source edition.
- Python interface: CLI/subprocess wrapper using existing PyEMTG option/output classes; no in-process Boost Python or HTTP service initially.
- Both committed OSIRIS-REx `.emtg` files are mandatory baselines.
- Numerical equality with SNOPT is not expected; feasibility and mission topology are hard gates, with aggregate metrics compared against the explicit two-baseline envelope.
- Legacy `snopt_*` option names remain accepted in the first milestone to preserve existing `.emtgopt` compatibility.

**Scope boundaries**
- Included: IPOPT replacement, Debian container, headless Python runner, OSIRIS reproduction, dual-baseline comparison, and build/run documentation.
- Excluded: PyEMTG wxPython GUI, HTTP/job service, plotting, exact SNOPT trajectory reproduction, broad option-schema renaming, and unrelated refactors.


---

