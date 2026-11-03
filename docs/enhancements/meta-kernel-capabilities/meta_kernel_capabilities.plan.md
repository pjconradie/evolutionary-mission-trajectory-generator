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

### Step 1 — `missionoptions` plumbing (implemented)
1. Add `SPICE_meta_kernel` field, default, parser entry, and writer entry in
   `src/Core/missionoptions.h` / `.cpp`. Done.
2. Mirror in `PyEMTG/MissionOptions.py` (`__init__`, read loop, write method).
   Done, with one fix discovered during implementation: the Python reader
   does `line.rstrip("\n\r ")` before splitting, which strips the trailing
   delimiter space on a `writeAll`-written empty value (`"SPICE_meta_kernel \n"`
   → `"SPICE_meta_kernel"`), leaving a 1-element `linecell` and raising
   `IndexError` on a naive `linecell[1]` lookup. `SPICE_meta_kernel` is the
   first field in this file with a legitimately empty string default that can
   be `writeAll`-written, so this edge case had no prior precedent to copy.
   Fixed with `linecell[1] if len(linecell) > 1 else ""`, covered by
   `test_empty_spice_meta_kernel_survives_writeall_round_trip` in
   `tests/test_meta_kernel.py`. The equivalent C++ path
   (`boost::split(..., boost::token_compress_on)`) was verified empirically to
   already return a 2-element vector (`["SPICE_meta_kernel", ""]`) for the same
   input, so no equivalent C++ fix was needed.

### Step 2 — `EMTG_v9.cpp` load/unload changes (implemented)
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

All six items above are implemented as a free-function helper pair
(`resolve_spice_kernel_path`, `log_loaded_spice_kernels`) in an anonymous
namespace ahead of `main()`, plus the load/unload branches in `main()` itself.
**Compile-verified**: ran the repository's own
`tests/integration/test_none_backend.py::test_none_backend_configures_and_compiles_without_snopt`
against the real pinned Docker toolchain image (not a syntax-only check) —
both `none_backend_configure` and `none_backend_compile` passed, confirming
`missionoptions.h/.cpp` and `EMTG_v9.cpp` build cleanly together with the rest
of the solver-neutral target.

### Step 3 — Documentation (implemented)
1. **Correction to an earlier draft of this plan:** the claim that there is
   "no existing hand-written user-facing reference" for
   `SPICE_leap_seconds_kernel` / `SPICE_reference_frame_kernel` was wrong —
   that search missed the LaTeX-based EMTG user guide. A hand-written
   reference does exist: `docs/0_Users/emtg_user_guide/options/s-physics.tex`,
   "Ephemeris Settings" subsection, with existing `\item`s for "Leap seconds
   kernel" and "Frame kernel" (the generated/autogen hits found by the
   earlier search were a red herring — they don't reflect this hand-authored
   guide).
2. **Revised approach (per user direction):** editing `s-physics.tex` directly
   was rejected — that file is one input into the generated EMTG user guide
   PDF, and editing it would require regenerating the PDF, which is out of
   scope here. Instead, the documentation lives in a new, standalone Markdown
   file: `docs/0_Users/emtg_user_guide/options/meta_kernels.md`. It covers the
   same ground the `s-physics.tex` item would have (delivery contract from
   §3.5, priority rule, hard-fail behavior from §3.4, both path-resolution
   forms from §3.1), cross-references the existing "Ephemeris Settings"
   section in `s-physics.tex` as the options this feature is an alternative
   to, and links back to this plan document. An earlier version of this step
   did add the content directly to `s-physics.tex` and compile-verified it
   with `pdflatex` against a minimal standalone harness — that approach
   caught one real bug (an initial draft used `\ac{CSPICE}`, but no
   `\acro{CSPICE}` entry exists in `docs/shared_latex_inputs/acronymlist.tex`,
   so the real `acronym` package would have hard-errored) — but that change
   was reverted in favor of the standalone Markdown file once the PDS/PDF
   regeneration concern was raised.
3. **No changelog/release-notes file exists in this repository** (confirmed
   by search — only vendored third-party changelogs under `depend/`, nothing
   at the repository root or under `docs/`). Creating a new top-level
   changelog file was judged out of scope for this feature (a larger,
   unrelated process change the user did not ask for); this item is therefore
   not applicable as originally written. If/when this repo adopts a
   changelog convention, this feature should be noted there as additive and
   backward compatible (empty default preserves existing flat-file loading
   exactly).

### Step 4 — Fixtures (implemented)

Split into two independent fixtures, since a minimal kernel set sufficient to
*load* is not necessarily sufficient to *solve a mission*. Both are built
from kernels already committed to this repository (no new large binary
kernels were added):

1. **Kernel-load probe fixture** — `tests/integration/fixtures/meta_kernel/
   meta_kernel.tm` and a deliberately malformed sibling,
   `malformed_meta_kernel.tm`. The valid fixture's `PATH_VALUES`/
   `PATH_SYMBOLS` reference two already-committed directories
   (`Universe/ephemeris_files/` for `naif0012.tls`/`pck00010.tpc`, and
   `docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS_universe/ephemeris_files/`
   for the small `bennu_refdrmc_v1.bsp`), proving both path-resolution forms
   and multi-directory `PATH_SYMBOLS` resolution in one fixture. The
   malformed sibling references a kernel file that does not exist, to
   exercise the CSPICE-level error path. Used by a new standalone CSPICE
   probe, `tests/cpp/test_meta_kernel_cspice_probe.cpp` (mirroring
   `tests/cpp/dependency_probe.cpp`'s style/calling convention), which
   directly exercises `furnsh_c`/`ktotal_c`/`kdata_c`/`unload_c`/`failed_c`/
   `getmsg_c`/`reset_c` without needing a full `EMTGv9` run — covering §5
   items 3 (partially: load + inventory), 4 (teardown), and 5 (the
   CSPICE-side half of the error path).
   One real-world wrinkle found only by actually running this probe in
   Docker: `ktotal_c("ALL")` counts the meta-kernel `.tm` file itself as a
   loaded kernel (CSPICE treats it as a loaded "META" text kernel), so a
   3-kernel meta-kernel reports a pool size of 4, not 3, right after
   `furnsh_c` — the probe (and `EMTG_v9.cpp`'s own `log_loaded_spice_kernels`
   inventory log from Step 2) both reflect this accurately; it is expected
   CSPICE behavior, not a bug. A second wrinkle: after a meta-kernel fails to
   load because one of its `KERNELS_TO_LOAD` entries is missing, CSPICE may
   still have registered the `.tm` file's own text-kernel entry before
   hitting the missing file, so the pool is not necessarily empty afterward
   — the probe checks "no `.bsp` data kernel got loaded" rather than
   asserting an empty pool, which is the more precise and more robust
   assertion.
2. **Executable mission fixture** — reuses the existing, already-working,
   fast (180 s timeout) `testatron/tests/transcription_tests/
   CoastPhase_EMintercept.emtgopt` mission (Moon/Sun/synthetic-body, no new
   universe needed) rather than authoring a new universe from scratch. A new
   `conftest.py` helper (`_write_meta_kernel_for_testatron_ephemeris`) writes
   a `meta_kernel.tm` at test-runtime (not committed — it is generated into a
   `tmp_path_factory` directory and mounted read-only into the Docker
   container) that lists every `*.bsp` file the flat loader would already
   scan out of the host's `testatron/universe/ephemeris_files/` (so the
   meta-kernel path loads exactly the same real kernel set the flat path
   already loads today, discovered dynamically rather than hand-curated, so
   it can't silently drift out of sync with whatever the host/CI actually has
   downloaded). The containing fixture (`meta_kernel_mission_probe`) skips
   with a clear message if `de430.bsp` is not present on the host, matching
   this repo's existing convention for host-downloaded kernels (see
   `testatron/universe/ephemeris_files/go_get_these_files.txt`). Used for §5
   item 3's "mission still solves" check and the two EMTG-side hard-fail
   checks in §5 item 5 (missing `SPICE_meta_kernel` file, and a mission run
   against the malformed-`.tm` fixture).

### Step 5 — Automated pytest coverage (implemented)

Add two new pytest files mapping to the unit/integration split already used by
this repo's test suite (`tests/test_*.py` for unit, `tests/integration/test_*.py`
for integration — see `tests/test_ipopt_characterization.py`,
`tests/integration/test_tutorials.py`):

- `tests/test_meta_kernel.py` — `pytestmark = pytest.mark.unit`.
  **Implemented and passing (6 tests, all green).** Covers §5 items 1
  (missionoptions round-trip, at the C++ level) and 6 (PyEMTG round-trip,
  plus the default-value/empty-value-round-trip edge case found while
  implementing Step 1).
  `doubleType.h`'s `#include "GSAD_2B.h"` is guarded by `#ifdef
  AD_INSTRUMENTATION` (off by default), so `missionoptions.cpp` does **not**
  actually pull in the GSAD automatic-differentiation dependency in a normal
  build — an earlier draft of this plan stated otherwise and was wrong; this
  was caught and corrected by actually host-compiling it (`g++ -std=c++17 -I
  src/Core -I src/Utilities -I src/Math`, no GSL/GSAD/CSPICE needed, only
  `boost::filesystem`). This repo already has a matching, pre-existing,
  CMake-gated (`RUN_MISSIONOPTIONS_TESTBED`) native driver for exactly this —
  `src/Testing/missionoptions_tests/missionoptions_testbed_driver.cpp` — which
  was compiled and run directly against a `SPICE_meta_kernel`-bearing fixture
  file during implementation (both a normal value and the empty-default
  `writeAll` edge case) and confirmed to round-trip correctly end-to-end.
  `tests/test_meta_kernel.py` now includes a `test_cpp_contracts.py`-style
  host-compiled-and-run test built directly from `missionoptions.cpp` +
  `journeyoptions.cpp` + `file_utilities.cpp` + the testbed driver (skipped,
  not failed, if no host compiler or `boost::filesystem` is available).
  Items 4 (`ktotal_c` teardown check) and 5 (CSPICE error path) ended up at
  the integration tier instead (see below) rather than this unit-tier file,
  since both need a real CSPICE runtime that only the Docker toolchain
  provides.
- `tests/integration/test_meta_kernel_integration.py` — `pytestmark =
  [pytest.mark.integration, pytest.mark.docker, pytest.mark.solver_runtime]`,
  matching the exact marker pairing every existing file in
  `tests/integration/` uses (`integration` is never applied alone — see
  `test_baselining.py`, `test_cmake_policy.py`, `test_ipopt_backend.py`, etc.
  — and `solver_runtime` because this test runs `EMTGv9` to completion, the
  same reason `test_baselining.py`/`test_tutorials.py` carry it). **Implemented
  and passing (4 tests, all green, verified via real Docker runs, not just
  syntax checks):**
  - `test_meta_kernel_cspice_load_resolves_path_symbols` — runs the Step 4
    standalone CSPICE probe; covers §5 items 3 (partially) and 4.
  - `test_meta_kernel_mission_still_solves` — builds and runs `EMTGv9`
    against the Step 4 executable-mission fixture, asserts the §3.6 inventory
    log shows `"Completed loading SPICE meta-kernel"` (and *not* the flat
    path's `"Completed loading SPICE kernels."`), and asserts a `.emtg`
    output is produced; covers the rest of §5 item 3.
  - `test_meta_kernel_missing_file_hard_fails` — points `SPICE_meta_kernel`
    at a nonexistent absolute path and asserts the exact EMTG-side hard-fail
    text (`"EMTG failed with error:"` / `"does not exist"`) appears and no
    `.emtg` output is produced; covers the EMTG-side half of §5 item 5.
  - `test_meta_kernel_malformed_tm_hard_fails` — points `SPICE_meta_kernel` at
    the malformed `.tm` fixture and asserts both `"EMTG failed with error:"`
    and `"Failed to load SPICE meta-kernel"` (CSPICE's own diagnostic,
    surfaced through `getmsg_c`) appear, and no `.emtg` output is produced;
    covers the CSPICE-side half of §5 item 5 at the full-executable level
    (the standalone probe above covers the same path at the CSPICE-API
    level).
  These tests reuse and extend the existing session-scoped Docker fixtures in
  `tests/integration/conftest.py`/`_docker_support.py`
  (`_prepare_mission_options` gained an optional `spice_meta_kernel` kwarg;
  `_mission_runtime_probe` gained `read_only_mounts`/`log_path` passthrough;
  a new `_mission_error_probe` helper mirrors `_mission_runtime_probe` but
  does not assert a zero exit code or a produced `.emtg` file, since
  `EMTG_v9.cpp`'s outer `catch (std::exception&)` always returns 0 and skips
  output on a hard-fail — the only reliable signal is the captured log text)
  rather than reimplementing container orchestration, so they automatically
  honor `EMTG_TEST_ARTIFACT_DIR` like every sibling file.
  §5 item 2 (flat-layout regression) and item 7 (clean-runtime archive
  verification) are **not** part of this file — see the final decision on
  §7's open questions below.

**Naming note (discovered during implementation, not anticipated in earlier
drafts):** `tests/integration/test_meta_kernel.py` could not keep that
filename. This repo has no `__init__.py` anywhere under `tests/`, so pytest's
default "prepend" import mode treats same-basename test files in different
directories as the same module; with both `tests/test_meta_kernel.py` and
`tests/integration/test_meta_kernel.py` populated, collection fails outright
with "import file mismatch" (confirmed empirically). Three fixes were
weighed — `--import-mode=importlib` in `pytest.ini`, adding `__init__.py` to
every test directory, or renaming one file — and `--import-mode=importlib` was
tried first but reverted immediately: it breaks four existing files
(`tests/integration/conftest.py`, `test_baselining.py`, `test_docker_support.py`,
`test_tutorial_baselining.py`) that rely on prepend-mode's implicit sys.path
insertion for bare sibling imports like `from _docker_support import
run_probe`. The zero-risk fix was chosen instead: the integration file is
named `tests/integration/test_meta_kernel_integration.py`. `tests/test_meta_kernel.py`
keeps its original name (no collision, since it's the only file with that
basename once the other is renamed).

### Workflow verification against `docs/3_NLP_Solvers/IPOPT/tests.readme.md`

Checked this plan's test placement against the established workflow
documented in
[tests.readme.md](/Users/jacoconradie/Documents/GitHub/Surreal%20Technologies/evolutionary-mission-trajectory-generator/docs/3_NLP_Solvers/IPOPT/tests.readme.md).
Two corrections and one scope decision (later resolved in §7) came out of
that review:

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
   not `tests/integration/test_meta_kernel_integration.py`. Since only
   `tests/test_meta_kernel.py` and `tests/integration/test_meta_kernel_integration.py`
   have been created, genuine third-party-archive meta-kernel verification
   (a new test under `tests/emtg_toolchain/integration/` or
   `tests/emtg_toolchain/deployment/`, following the `EMTG_TEST_ARTIFACT_DIR`/
   `EMTG_ARCHIVE_COLD` conventions in that section of `tests.readme.md`) is
   deferred to a later iteration (resolved as item 2 in §7) rather than
   silently folded into the source-workflow integration test.
3. **§5 item 2 ("flat-layout regression") is arguably a `tests/regression/`
   concern, not `tests/integration/`.** `tests.readme.md` describes
   `tests/regression/` (marker `pytest.mark.regression`) as "the important
   source/baseline integrity suite" for exactly this kind of
   "does existing behavior still match" check, distinct from the Docker-backed
   compile-and-run checks in `tests/integration/`. Deferred to a later
   iteration (resolved as item 3 in §7) rather than introducing a third file
   unilaterally, since the two test files already created by the user are
   the scope confirmed so far.

## 5. Verification plan

Since this repo's C++ "tests" are small standalone driver executables (see
`src/Testing/missionoptions_tests/missionoptions_testbed_driver.cpp`) rather
than a gtest-style unit framework, verification is primarily:

1. **Missionoptions round-trip** (`tests/test_meta_kernel.py`,
   `test_spice_meta_kernel_round_trips_through_native_missionoptions`).
   **Implemented.** The existing `missionoptions_tests` driver is
   host-compiled (no extra sources added), run against a
   `SPICE_meta_kernel`-bearing `.emtgopt`, and the regenerated
   `tests/newdefault.emtgopt` is asserted to contain the round-tripped value.
2. **Flat-layout regression** (deferred — see §7 item 3 for the final
   scope decision): run
   an existing tutorial `.emtgopt`
   (e.g. one under `docs/0_Users/tutorial/...`) with `SPICE_meta_kernel` unset
   and confirm it passes the project's existing tutorial comparison/replay
   checks (whatever mechanism the repo already uses to validate tutorial runs
   — e.g. mission-feasibility/objective comparison, not a raw byte-for-byte
   diff, since output directories, timestamps, and optimizer internals make
   byte equivalence an inappropriate bar). This proves (ii) and confirms no
   regression.
3. **Meta-kernel load** (`tests/integration/test_meta_kernel_integration.py`,
   `test_meta_kernel_cspice_load_resolves_path_symbols` and
   `test_meta_kernel_mission_still_solves`). **Implemented and verified via
   real Docker runs.** The CSPICE-level probe confirms the expected kernel
   set is loaded/resolved; the `EMTGv9`-level test confirms the §3.6
   inventory log shows the meta-kernel path (not the flat `.bsp` loop) was
   taken, and that the mission still solves to a produced `.emtg` file.
4. **Teardown/unload verification**
   (`tests/integration/test_meta_kernel_integration.py`,
   `test_meta_kernel_cspice_load_resolves_path_symbols`, backed by the new
   standalone probe `tests/cpp/test_meta_kernel_cspice_probe.cpp`).
   **Implemented and verified.** Loads the `.tm`, confirms via `ktotal_c`/
   `kdata_c` that exactly the expected kernels (plus the meta-kernel's own
   text-kernel pool entry — see the Step 4 note on this) were loaded, calls
   `unload_c(meta_kernel_path)`, then asserts `ktotal_c("ALL")` returns to
   zero — this ended up at the integration tier (not `tests/test_meta_kernel.py`
   as originally planned) since it needs a real CSPICE runtime, which only
   the Docker toolchain provides.
5. **Error path** (`tests/integration/test_meta_kernel_integration.py`,
   `test_meta_kernel_missing_file_hard_fails`,
   `test_meta_kernel_malformed_tm_hard_fails`, and
   `test_meta_kernel_cspice_load_resolves_path_symbols`'s malformed-`.tm`
   section). **Implemented and verified**, at both the full-`EMTGv9`
   level (missing file and malformed `.tm`, asserted via captured stdout
   text — not exit code, since `EMTG_v9.cpp`'s outer catch always returns 0)
   and the standalone-CSPICE-probe level (`erract_c`/`failed_c`/`getmsg_c`/
   `reset_c` directly). Also moved to the integration tier for the same
   real-CSPICE-runtime reason as item 4.
6. **PyEMTG round-trip** (`tests/test_meta_kernel.py`): open/save an
   `.emtgopt` containing `SPICE_meta_kernel`
   through the PyEMTG GUI (or its options read/write module directly) and
   confirm the value is preserved.
7. **Clean-runtime archive verification** (deferred — see §7 item 2 for the
   final scope decision; not part of the two files created so far):
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

## 7. Open questions / review decisions (resolved)

1. **Fixture placement** — resolved. The kernel-load probe fixture lives at
   `tests/integration/fixtures/meta_kernel/` (`meta_kernel.tm` and
   `malformed_meta_kernel.tm`), alongside the test tier that consumes it. The
   executable-mission fixture is *not* a committed file at all: it is
   generated at test-runtime into a `tmp_path_factory` directory by
   `_write_meta_kernel_for_testatron_ephemeris` in `conftest.py`, since it
   must enumerate whatever real `.bsp` files are actually present on the
   host/CI (gitignored, host-downloaded) rather than hard-code a kernel list
   that could drift out of sync.
2. **Archive-deployment verification (§5 item 7)** — resolved as **deferred,
   out of scope for this iteration**. It was a Medium-priority recommendation
   in the original review, not a blocker, and it depends on the separate
   clean-runtime/archive-extraction workflow (`tests/emtg_toolchain/`) rather
   than the source-build workflow this iteration's two test files exercise.
   Taking it up means adding a new test under `tests/emtg_toolchain/
   integration/` or `tests/emtg_toolchain/deployment/` that mounts a nested
   meta-kernel tree in a clean, compiler-free extracted-archive runtime image
   and verifies the meta-kernel loads, its nested `PATH_VALUES` resolve, a
   flat sentinel `.bsp` placed alongside it is *not* loaded, and a mission
   output is produced — left for a follow-up iteration.
3. **Flat-layout regression placement (§5 item 2)** — resolved as **deferred,
   out of scope for this iteration**, for the same reason: it is a
   Medium-priority recommendation (replace a byte-for-byte diff with the
   project's existing tutorial comparison/replay checks), not a blocker to
   the core SPICE_meta_kernel capability landing, and it depends on
   whichever existing tutorial-comparison mechanism `tests/regression/`
   already uses for other options, which should be surveyed on its own
   rather than guessed at here. When taken up, route it through
   `tests/regression/` (`pytest.mark.regression`) rather than
   `tests/integration/`, per this repo's convention of keeping baseline-
   integrity checks out of the Docker-backed integration tier.
