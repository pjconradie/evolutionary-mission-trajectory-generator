# Meta-kernel capability implementation plan

## 1. Purpose and scope

Enhance the `EMTGv9` executable itself so that a third party can supply a SPICE
`meta_kernel.tm` (an ordered CSPICE furnishable text kernel, per the example in
[meta_kernel_capabilities.requirements.md](./meta_kernel_capabilities.requirements.md))
alongside its referenced kernel files, and have `EMTGv9` load that meta-kernel
directly through CSPICE instead of (or in preference to) the existing flat
`<universe_folder>/ephemeris_files/*.bsp` convention.

This supersedes the earlier external-launcher approach. The previous plan
(a separate `emtg-meta-kernel-runner` Python/SpiceyPy process that staged a
synthetic flat universe and re-derived kernel precedence itself) is void and
must not be used as a reference. `EMTGv9` is modified directly; no external
staging process is introduced.

**On "no C source may change":** the requirements doc's original constraint
against modifying C code referred to the vendored CSPICE toolkit. This plan's
C++ changes under `src/` (EMTG's own code, in `EMTG_v9.cpp` and
`missionoptions.h/.cpp`) are intentional and in scope. No file under
`depend/cspice/` (the vendored CSPICE C library itself) is modified.

**On "no core EMTG capability may change":** `src/` is organized into clear
layers — the trajectory/optimization engine proper (`Astrodynamics/`,
`Mission/`, `InnerLoop/`, `Propagation/`, `Integration/`, `Propulator/`,
`Math/`, `SplineEphem/`, `HardwareModels/`) versus the interface/boundary/
support layers (`Core/` configuration data model, `Executable/` process entry
point, `Utilities/`). This plan touches exactly three files, all in the latter
category, and none in the former:

| File | Layer | Nature of change |
|---|---|---|
| `src/Core/missionoptions.h` | Configuration data model | Additive only: one new `std::string SPICE_meta_kernel;` field declared beside the two existing sibling fields `SPICE_leap_seconds_kernel`/`SPICE_reference_frame_kernel`. No existing field, method signature, or class behavior changes. |
| `src/Core/missionoptions.cpp` | Configuration parser/writer | Additive only: a default-value assignment, one `linecell[0] ==` parse branch, and one guarded `.write()` branch, each mirroring the existing `SPICE_leap_seconds_kernel` pattern. No existing option's parse/write logic is altered. |
| `src/Executable/EMTG_v9.cpp` | Executable entry point (`main()`), pre-flight SPICE setup/teardown | Confined to the kernel load block (~lines 134-166) and unload block (~lines 757-768) — both run strictly before `EMTG::Mission TrialMission(...)` is constructed (~line 720) and strictly after `TrialMission.optimize()` completes. The change is an `if`/`else` branch selecting meta-kernel vs. existing flat-file discovery/teardown. No line of `Mission`, optimizer, propagation, or body/ephemeris-evaluation code is touched. |

`missionoptions` is a passive data container consumed by the core engine —
adding a field to it does not change any algorithm that reads other fields.
`EMTG_v9.cpp`'s SPICE load/unload block is I/O/environment setup (analogous to
argument parsing or working-directory creation elsewhere in the same
function), not part of the trajectory-optimization capability itself: `Mission`
and everything it calls remain completely unmodified.

Core requirements carried over from the requirements doc:

- (i) EMTG shall support loading kernels either from a provided `meta_kernel.tm`
  or from the existing flat `*/universe/ephemeris_files/...` layout.
- (ii) The flat layout continues to work unchanged when no meta-kernel is
  present (full backward compatibility).
- (iii) When a `meta_kernel.tm` is present, it takes priority over the flat
  layout — the flat `ephemeris_files/*.bsp` scan must not also run.
- (iv) A compatible meta-kernel is a standard CSPICE `KPL/MK` text kernel using
  `PATH_SYMBOLS`/`PATH_VALUES`/`KERNELS_TO_LOAD`, as shown in the requirements
  doc's OSIRIS-REx example.

## 2. Current behavior (baseline, do not regress)

In [EMTG_v9.cpp](/Users/jacoconradie/Documents/GitHub/Surreal%20Technologies/evolutionary-mission-trajectory-generator/src/Executable/EMTG_v9.cpp) (load block ~lines 134-166, unload block ~lines 757-768), when
`options.ephemeris_source >= 1`:

1. `EMTG::file_utilities::get_all_files_with_extension(universe_folder + "/ephemeris_files/", ".bsp", ...)`
   recursively collects every `.bsp` file under that folder and `furnsh_c`'s each.
2. `options.SPICE_leap_seconds_kernel` and `options.SPICE_reference_frame_kernel`
   (plain filenames, defaulting to `naif0012.tls` / `pck00010.tpc`) are
   individually `furnsh_c`'d from the same folder.
3. At teardown, every loaded file is individually `unload_c`'d.

This behavior must remain the default and unchanged when no meta-kernel is
supplied.

## 3. Design

### 3.1 New option

Add a new string option to `missionoptions`, following the exact pattern of
`SPICE_leap_seconds_kernel`:

```cpp
// src/Core/missionoptions.h
std::string SPICE_meta_kernel; // optional SPICE meta-kernel (.tm) filename; empty = disabled
```

- Default: `""` (empty = feature disabled, preserving existing behavior exactly).
- Parsed/written in `missionoptions.cpp` identically to the two existing
  `SPICE_*_kernel` options (read in the `linecell[0] ==` block, written in the
  `.write()` method guarded by `!= default || writeAll`).
- Mirrored in [PyEMTG/MissionOptions.py](/Users/jacoconradie/Documents/GitHub/Surreal%20Technologies/evolutionary-mission-trajectory-generator/PyEMTG/MissionOptions.py) (`__init__`, file read, file write)
  so round-tripping an `.emtgopt` through the GUI preserves the setting.

The option accepts two forms, resolved as follows:

- A **bare filename** (e.g. `meta_kernel.tm`, no directory component) is
  resolved relative to `<universe_folder>/ephemeris_files/`, exactly like the
  two existing SPICE filename options. This preserves tutorial-style
  compatibility with the current delivery contract — drop the file into
  `ephemeris_files/`.
- An **absolute or explicitly relative path** (e.g.
  `/opt/emtg/input/kernel-set/meta_kernel.tm` or `./kernel-set/meta_kernel.tm`,
  i.e. having a directory component) is used directly, unmodified. This
  supports third-party deployments that mount a reviewed kernel-set tree
  outside the universe folder.

The two forms must **not** be distinguished by scanning the string for a
literal `/` or `\` character. This repository explicitly supports Windows
builds (see the `#ifdef _WIN32` branch already in
[EMTG_v9.cpp](/Users/jacoconradie/Documents/GitHub/Surreal%20Technologies/evolutionary-mission-trajectory-generator/src/Executable/EMTG_v9.cpp)),
and a manual separator-character check mis-classifies Windows-style paths
(`\` is not `/`) and drive-letter forms (`C:\...`). `boost::filesystem` is
already linked and used in this exact file, so the resolution helper should
test `boost::filesystem::path(options.SPICE_meta_kernel).has_parent_path()`:
`false` means a bare filename (resolve under `ephemeris_files/`); `true`
means the value already has a directory component, whether absolute or
relative, and is used as-is. This is portable across both separator
conventions and correctly handles drive letters, with no manual string
scanning.

Either way, the meta-kernel's own `PATH_SYMBOLS`/`PATH_VALUES` are free to
point anywhere on disk (e.g. a sibling `kernels/` tree) for the individual
kernel files it lists — only the `.tm` file itself needs to be locatable via
one of the two forms above.

### 3.2 Detection and priority

`using_meta_kernel` and `meta_kernel_path` are declared once, in `main()`'s
outer scope alongside the existing `SPICE_files_*` vectors, so the same values
are available unchanged in the teardown/unload block later in the function —
not re-derived or re-declared there.

```cpp
// declared with the existing SPICE_files_* vectors, outer main() scope
bool using_meta_kernel = false;
std::string meta_kernel_path;

if (options.ephemeris_source >= 1)
{
    if (!options.SPICE_meta_kernel.empty())
    {
        meta_kernel_path = resolve_spice_kernel_path(options.universe_folder, options.SPICE_meta_kernel); // §3.1 bare-filename vs. absolute/relative resolution
        using_meta_kernel = true;

        if (!boost::filesystem::exists(meta_kernel_path))
        {
            throw std::runtime_error("SPICE_meta_kernel was set to '" + options.SPICE_meta_kernel
                + "' (resolved to '" + meta_kernel_path + "') but no such file exists.");
        }
    }

    if (using_meta_kernel)
    {
        // CSPICE must be in RETURN mode *before* the furnsh_c call that might fail
        erract_c((SpiceChar*)"SET", 100, (SpiceChar*)"RETURN");

        furnsh_c(meta_kernel_path.c_str());

        if (failed_c())
        {
            SpiceChar cspice_message[1841];
            getmsg_c((SpiceChar*)"LONG", 1841, cspice_message);
            reset_c();
            throw std::runtime_error("CSPICE failed to load meta-kernel '" + meta_kernel_path
                + "': " + std::string(cspice_message));
        }

        // log what CSPICE actually loaded, in order (see §3.6)
        log_loaded_spice_kernels();

        std::cout << "Loaded SPICE meta-kernel: " << meta_kernel_path << std::endl;
    }
    else
    {
        // existing flat *.bsp + leap-second + reference-frame loading, unchanged
    }

    std::cout << "Completed loading SPICE kernels." << std::endl;
}
```

Priority rule (iii) is satisfied structurally: the flat-file branch simply does
not execute when a meta-kernel is configured. **A configured-but-missing
`SPICE_meta_kernel` is always a hard failure** — it must never silently fall
back to the flat layout, since a supplied meta-kernel is required to take
priority, not merely be preferred when conveniently present. The "no option
set" case (the default, empty string) remains the only path that uses flat
discovery, so existing behavior is fully preserved.

### 3.3 Unload

```cpp
if (options.ephemeris_source >= 1)
{
    if (using_meta_kernel)
    {
        unload_c(meta_kernel_path.c_str());
    }
    else
    {
        // existing per-file unload loop, unchanged
    }
}
```

`unload_c` on a meta-kernel unloads every kernel that meta-kernel caused to be
loaded, in one call — CSPICE tracks this internally, so no bookkeeping of the
individual resolved kernel paths is needed on the EMTG side.

Note: the existing flat-mode load/unload code in
[EMTG_v9.cpp](/Users/jacoconradie/Documents/GitHub/Surreal%20Technologies/evolutionary-mission-trajectory-generator/src/Executable/EMTG_v9.cpp)
has a latent path-string asymmetry — the load block builds paths with a
leading slash (`universe_folder + "/ephemeris_files/..."`) while the unload
block omits it (`universe_folder + "ephemeris_files/..."`). That is
out-of-scope baseline behavior and is not being fixed here, but it is the
reason `meta_kernel_path` is computed exactly once, at load time, and reused
verbatim at teardown, rather than being re-resolved from
`options.SPICE_meta_kernel` in the unload block: reusing the identical string
avoids introducing the same class of load/unload mismatch for the new
feature.

### 3.4 Error handling (resolved)

Both failure modes are hard errors, not fallbacks:

- **Configured-but-missing file**: `SPICE_meta_kernel` non-empty but the
  resolved path (§3.1) does not exist on disk → throw before any CSPICE call is
  made (checked with `boost::filesystem::exists`). This is a pure EMTG-side
  check, independent of CSPICE's own error state.
- **Malformed `.tm` / CSPICE furnsh failure** (e.g. unresolved `PATH_SYMBOLS`,
  a `KERNELS_TO_LOAD` entry pointing at a missing or unreadable kernel): CSPICE
  is switched to `erract_c(..., "RETURN")` *before* the `furnsh_c` call (not
  after, as an earlier draft of this plan showed), then `failed_c()` is checked
  immediately after; on failure, `getmsg_c("LONG", ...)` retrieves the CSPICE
  diagnostic, `reset_c()` clears CSPICE's error state, and EMTG throws a
  `std::runtime_error` embedding that diagnostic text — surfacing a clear
  EMTG-level error rather than a raw CSPICE abort or an unexplained downstream
  failure.

In both cases EMTG terminates the run rather than silently reverting to flat
discovery, per the hard-fail decision in §3.2.

### 3.5 Third-party delivery contract

```text
<universe_folder>/
├── ephemeris_files/
│   ├── meta_kernel.tm          <- new, name given by options.SPICE_meta_kernel
│   ├── naif0012.tls            <- still present if referenced, or resolved
│   └── ...                     <- existing flat *.bsp files, now unused if
│                                   meta-kernel is active, but harmless if left
├── kernels/                    <- arbitrary location, resolved via the
│   ├── lsk/                       meta-kernel's own PATH_SYMBOLS/PATH_VALUES;
│   ├── pck/                       does not need to live under
│   └── spk/...                    ephemeris_files/ at all
```

No change to `universe_folder` resolution or the `.emtg_universe` file format
is needed — only the kernel-loading step inside `EMTGv9` changes.

### 3.6 Runtime inventory logging

After a successful `furnsh_c(meta_kernel_path)`, log what CSPICE actually
resolved and loaded rather than only the `.tm` path itself — this is the
primary diagnostic a third-party integrator has when their `PATH_VALUES`/
`PATH_SYMBOLS` or `KERNELS_TO_LOAD` don't resolve the way they expect:

```cpp
void log_loaded_spice_kernels()
{
    SpiceInt count = 0;
    ktotal_c((SpiceChar*)"ALL", &count);

    std::cout << "SPICE kernel pool after meta-kernel load (" << count << " files):" << std::endl;

    for (SpiceInt i = 0; i < count; ++i)
    {
        SpiceChar file[256], filtyp[32], source[256];
        SpiceInt handle;
        SpiceBoolean found;
        kdata_c(i, (SpiceChar*)"ALL", 256, 32, 256, file, filtyp, source, &handle, &found);

        if (found)
            std::cout << "  [" << i << "] " << file << " (" << filtyp << ")" << std::endl;
    }
}
```

This is strictly additive logging (no behavior change) and applies only on the
meta-kernel branch; the existing flat-file branch already logs each file as it
loads it.

## 4. Step-by-step implementation plan

### Step 1 — `missionoptions` plumbing
1. Add `SPICE_meta_kernel` field, default, parser entry, and writer entry in
   `src/Core/missionoptions.h` / `.cpp`.
2. Mirror in `PyEMTG/MissionOptions.py` (`__init__`, read loop, write method).

### Step 2 — `EMTG_v9.cpp` load/unload changes
1. Introduce `using_meta_kernel` / `meta_kernel_path` as locals in `main()`'s
   outer scope, declared alongside the existing `SPICE_files_*` vectors —
   **not** re-declared inside the load block — so the teardown/unload block
   later in the function reads the same values set during loading.
2. Branch the load block per §3.2; keep the existing flat-file loop intact in
   the `else` branch (no logic changes to it).
3. Branch the unload block per §3.3, using the outer-scope `using_meta_kernel`
   to select between `unload_c(meta_kernel_path)` and the existing per-file loop.
4. Implement path resolution (§3.1: bare filename vs. absolute/relative path,
   using `boost::filesystem::path(...).has_parent_path()`, not manual
   separator-character scanning) as a small helper, e.g.
   `resolve_spice_kernel_path(...)`.
5. Set `erract_c(..., "RETURN")` **before** the meta-kernel `furnsh_c` call
   (not after), then check `failed_c()` / `getmsg_c()` / `reset_c()` per §3.4
   and throw a `std::runtime_error` with the CSPICE diagnostic on failure.
6. Implement `log_loaded_spice_kernels()` (§3.6) using `ktotal_c`/`kdata_c` and
   call it after a successful meta-kernel load.

### Step 3 — Documentation
1. There is currently **no existing hand-written user-facing reference** for
   `SPICE_leap_seconds_kernel` / `SPICE_reference_frame_kernel` or
   `ephemeris_source` under `docs/` (confirmed by search — these options
   appear only in generated `.emtgopt` dumps and PyEMTG docstrings/autogen
   output, never in a hand-authored options guide). So item 2 below is not an
   addition to a pre-existing reference — it is the first user-facing
   reference for this family of options, and should be written as a
   self-contained explanation rather than assuming surrounding context exists.
2. Add a short "Using a SPICE meta-kernel" subsection near the existing
   SPICE/ephemeris documentation, including the delivery contract from §3.5,
   the priority rule, the hard-fail behavior from §3.4, and both path-
   resolution forms from §3.1.
3. Note in the changelog/release notes that this is additive and backward
   compatible.

### Step 4 — Fixtures

Split into two independent fixtures, since a minimal kernel set sufficient to
*load* is not necessarily sufficient to *solve a mission*:

1. **Kernel-load probe fixture**: a small, redistributable `meta_kernel.tm`
   (e.g. under `testatron/universe/` or a new `tests/` fixture) referencing
   only the already-available `naif0012.tls` / `pck00010.tpc` plus one small
   `.bsp`. Used purely to exercise load/log/unload behavior (§5 items 3–4, 6)
   without needing to actually run an optimizer to completion.
2. **Executable mission fixture**: a separately prepared, self-contained
   universe + `.emtgopt` with full body/ephemeris coverage for a real
   (small/fast) mission, restructured to be driven via a meta-kernel instead of
   its current flat `ephemeris_files/` layout. Used for §5 item 3's "mission
   still solves" check and the archive verification test (§5 item 7).

### Step 5 — Automated pytest coverage

Add two new pytest files mapping to the unit/integration split already used by
this repo's test suite (`tests/test_*.py` for unit, `tests/integration/test_*.py`
for integration — see `tests/test_ipopt_characterization.py`,
`tests/integration/test_tutorials.py`):

- `tests/test_meta_kernel.py` — `pytestmark = pytest.mark.unit`. Covers §5
  items 1 (missionoptions round-trip), 4 (teardown/unload via `ktotal_c`), 5
  (error path: missing file / malformed `.tm`), and 6 (PyEMTG round-trip).
  These do not require building/running `EMTGv9` end-to-end — they exercise
  CSPICE directly (e.g. via the C++ `missionoptions_tests` driver invoked as a
  subprocess, or a thin Python/ctypes or SpiceyPy probe against the fixture
  `.tm`) or the pure-Python `MissionOptions.py` read/write path.
- `tests/integration/test_meta_kernel.py` — `pytestmark = [pytest.mark.integration,
  pytest.mark.docker, pytest.mark.solver_runtime]`, matching the exact marker
  pairing every existing file in `tests/integration/` uses (`integration` is
  never applied alone — see `test_baselining.py`, `test_cmake_policy.py`,
  `test_ipopt_backend.py`, etc. — and `solver_runtime` because this test runs
  `EMTGv9` to completion, the same reason `test_baselining.py`/
  `test_tutorials.py` carry it). It reuses the existing session-scoped Docker
  fixtures from `tests/integration/conftest.py`/`_docker_support.py`
  (`toolchain_image` or `clean_toolchain_image`, `repository_root`,
  `artifact_directory`) rather than reimplementing container orchestration, so
  it automatically honors `EMTG_TEST_ARTIFACT_DIR` like every sibling file.
  Covers §5 item 3 (meta-kernel load + mission solve, built from source in the
  pinned Linux toolchain image — see the workflow-verification note below for
  why item 2 and item 7 are *not* placed here as originally drafted).

Both files are confirmed to use the singular `test_` prefix —
`tests/test_meta_kernel.py` and `tests/integration/test_meta_kernel.py` — matching
pytest's default collection patterns (`test_*.py` / `*_test.py`, unmodified by
`pytest.ini`) and every other test file in this repo, so they will be
collected and run under CI once populated.

### Workflow verification against `docs/3_NLP_Solvers/IPOPT/tests.readme.md`

Checked this plan's test placement against the established workflow
documented in
[tests.readme.md](/Users/jacoconradie/Documents/GitHub/Surreal%20Technologies/evolutionary-mission-trajectory-generator/docs/3_NLP_Solvers/IPOPT/tests.readme.md).
Two corrections and one open question came out of that review:

1. **Marker pairing, fixed above.** Every file under `tests/integration/`
   pairs `pytest.mark.integration` with `pytest.mark.docker` (confirmed by
   inspecting all eight existing files — none uses `integration` alone), plus
   whichever domain marker applies. The earlier draft's "`integration`, plus
   whichever of `solver_runtime`/`docker`/`ipopt_backend` apply" was too vague;
   §5 item 3 now specifies the exact triplet.
2. **§5 item 7 ("clean-runtime archive verification") was scoped to the wrong
   workflow and is removed from the two-file plan.** `tests.readme.md`
   distinguishes two separate workflows: the **source workflow**
   (`tests/integration/`, selected with `-m integration`/`--integration`,
   building `EMTGv9` from the repository checkout inside the pinned Docker
   toolchain) versus the **archive workflow**
   (`tests/emtg_toolchain/{unit,integration,deployment}`, selected with the
   *separate* mutually-exclusive `--unit`/`--integration`/`--tutorials` flags
   defined in `tests/conftest.py`, verifying the packaged, compiler-free,
   extracted `emtg-ipopt-*.tar.gz` runtime deliverable). "Mounts a nested
   meta-kernel tree in a clean runtime image" describes the archive workflow,
   not `tests/integration/test_meta_kernel.py`. Since only
   `tests/test_meta_kernel.py` and `tests/integration/test_meta_kernel.py`
   have been created, genuine third-party-archive meta-kernel verification
   (a new test under `tests/emtg_toolchain/integration/` or
   `tests/emtg_toolchain/deployment/`, following the `EMTG_TEST_ARTIFACT_DIR`/
   `EMTG_ARCHIVE_COLD` conventions in that section of `tests.readme.md`) is
   deferred as an open question (§7) rather than silently folded into the
   source-workflow integration test.
3. **§5 item 2 ("flat-layout regression") is arguably a `tests/regression/`
   concern, not `tests/integration/`.** `tests.readme.md` describes
   `tests/regression/` (marker `pytest.mark.regression`) as "the important
   source/baseline integrity suite" for exactly this kind of
   "does existing behavior still match" check, distinct from the Docker-backed
   compile-and-run checks in `tests/integration/`. Left as an open question
   (§7) rather than introducing a third file unilaterally, since the two test
   files already created by the user are the scope confirmed so far.

## 5. Verification plan

Since this repo's C++ "tests" are small standalone driver executables (see
`src/Testing/missionoptions_tests/missionoptions_testbed_driver.cpp`) rather
than a gtest-style unit framework, verification is primarily:

1. **Missionoptions round-trip** (`tests/test_meta_kernel.py`): extend the
   `missionoptions_tests` driver (or add a focused one) to set
   `SPICE_meta_kernel`, write an `.emtgopt`, re-read it, and assert the value
   round-trips.
2. **Flat-layout regression** (placement open — see Workflow verification
   note #3 above; candidate: `tests/integration/test_meta_kernel.py` tagged
   additionally with `pytest.mark.regression`, or a new
   `tests/regression/test_meta_kernel.py`): run
   an existing tutorial `.emtgopt`
   (e.g. one under `docs/0_Users/tutorial/...`) with `SPICE_meta_kernel` unset
   and confirm it passes the project's existing tutorial comparison/replay
   checks (whatever mechanism the repo already uses to validate tutorial runs
   — e.g. mission-feasibility/objective comparison, not a raw byte-for-byte
   diff, since output directories, timestamps, and optimizer internals make
   byte equivalence an inappropriate bar). This proves (ii) and confirms no
   regression.
3. **Meta-kernel load** (`tests/integration/test_meta_kernel.py`): run
   `EMTGv9` against the Step 4 executable-mission
   fixture with `SPICE_meta_kernel` set, confirm via the §3.6 inventory log
   that the flat `.bsp` loop was skipped and the expected kernel set was
   loaded through the meta-kernel, and confirm the mission still solves.
4. **Teardown/unload verification** (`tests/test_meta_kernel.py`): using the
   kernel-load probe fixture, load
   the `.tm`, call `unload_c(meta_kernel_path)`, then call `ktotal_c("ALL")`
   and assert the count returns to whatever it was before the load (zero in a
   clean process, or the pre-existing pool size if other kernels were already
   loaded) — do not merely assume `unload_c` behaves correctly.
5. **Error path** (`tests/test_meta_kernel.py`): run with `SPICE_meta_kernel`
   set to a non-existent filename
   (expect the pure EMTG-side existence-check failure from §3.4, no CSPICE
   call attempted) and to a deliberately malformed `.tm` (bad `PATH_SYMBOLS`,
   missing referenced kernel — expect the `erract_c`/`failed_c`/`getmsg_c`
   path) and confirm both hard-fail with a clear message, never a raw CSPICE
   abort, silent corruption, or fallback to flat discovery.
6. **PyEMTG round-trip** (`tests/test_meta_kernel.py`): open/save an
   `.emtgopt` containing `SPICE_meta_kernel`
   through the PyEMTG GUI (or its options read/write module directly) and
   confirm the value is preserved.
7. **Clean-runtime archive verification** (deferred — see Workflow
   verification note #2 above; not part of the two files created so far):
   when taken up, add one test
   under `tests/emtg_toolchain/integration/` or `tests/emtg_toolchain/deployment/`
   that mounts a nested meta-kernel tree (kernel-load probe fixture or a
   dedicated nested-path fixture) in a clean, compiler-free extracted-archive
   runtime image and verifies, end
   to end: the meta-kernel is loaded; its nested `PATH_VALUES` resolve
   correctly; the flat sentinel `.bsp` placed alongside it is *not* loaded
   (proving priority, not just coexistence); and a mission output is produced.

## 6. Non-goals (this iteration)

- No change to `.emtg_universe` file format or `universe_folder` resolution.
- No change to `ephemeris_source == 2` (SplineEphem) behavior.
- No external staging/validation process, provenance hashing, or packaged
  launcher — that design is retired.
- No attempt to independently re-derive or override CSPICE's own kernel
  precedence/merging rules; CSPICE handles that natively when `furnsh_c` loads
  the meta-kernel.
- No modification to any vendored CSPICE file under `depend/cspice/` — all
  changes are in EMTG's own `src/` code (see "On 'no C source may change'" in
  §1).
- No modification to any file in the trajectory/optimization engine proper
  (`Astrodynamics/`, `Mission/`, `InnerLoop/`, `Propagation/`, `Integration/`,
  `Propulator/`, `Math/`, `SplineEphem/`, `HardwareModels/`) — all changes are
  confined to the `Core/` configuration data model and the `Executable/`
  entry-point's pre-flight SPICE setup/teardown (see the file-scope table in
  §1).

## 7. Open questions / review decisions

1. Where the kernel-load probe fixture and the executable mission fixture
   (§4 Step 4) should live.
2. Whether the archive-deployment verification test (§5 item 7) is taken up
   now under `tests/emtg_toolchain/integration/` or
   `tests/emtg_toolchain/deployment/` (per the workflow-verification note in
   §4 Step 5), or deferred to a later iteration, and whether it runs in normal
   CI or is reserved, like the full OSIRIS-REx bundle and the cold archive
   integration test, for a separate acceptance gate given its clean-runtime/
   Docker dependency.
3. Whether §5 item 2 (flat-layout regression) should be tagged
   `pytest.mark.regression` within `tests/integration/test_meta_kernel.py`, or
   split into a new `tests/regression/test_meta_kernel.py`, to match this
   repo's convention of routing baseline-integrity checks through
   `tests/regression/` rather than the Docker-backed `tests/integration/` tier.
