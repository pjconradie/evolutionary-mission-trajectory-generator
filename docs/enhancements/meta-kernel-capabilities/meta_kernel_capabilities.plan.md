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

The option stores a filename (e.g. `meta_kernel.tm`), resolved the same way the
two existing SPICE filename options are resolved: relative to
`<universe_folder>/ephemeris_files/`. This keeps the third-party delivery
contract identical to today's — drop files into `ephemeris_files/` — while
letting the meta-kernel's own `PATH_SYMBOLS`/`PATH_VALUES` point anywhere else
on disk (e.g. a sibling `kernels/` tree) for the individual kernel files it
lists.

### 3.2 Detection and priority

In the load block:

```cpp
bool using_meta_kernel = false;
std::string meta_kernel_path;

if (options.ephemeris_source >= 1)
{
    if (!options.SPICE_meta_kernel.empty())
    {
        meta_kernel_path = options.universe_folder + "/ephemeris_files/" + options.SPICE_meta_kernel;
        using_meta_kernel = boost::filesystem::exists(meta_kernel_path);
    }

    if (using_meta_kernel)
    {
        furnsh_c(meta_kernel_path.c_str());
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
not execute when a meta-kernel is configured and present. If
`options.SPICE_meta_kernel` is set but the file does not exist, fall back to the
flat layout (treat as "not supplied") rather than failing silently — see §3.4
for whether this should instead be a hard error.

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

### 3.4 Error handling

Decide (see open questions, §7) whether:

- a configured-but-missing `SPICE_meta_kernel` file is a hard error (fail fast,
  avoid silently running on the wrong kernel set), vs. a silent fallback to the
  flat layout (more forgiving, matches "either/or" wording of requirement (i)
  literally); and
- a malformed `.tm` (CSPICE furnsh failure, e.g. unresolved `PATH_SYMBOLS` or a
  missing referenced kernel) should surface through EMTG's existing
  `erract_c("SET", ..., "RETURN")` / error-check pattern already used around
  the leap-second/reference-frame load, producing a clear EMTG-level error
  message rather than a raw CSPICE abort.

Recommendation: treat a configured-but-missing meta-kernel file as a hard error
(clearer for third-party integrators who explicitly opted in), and keep the
"no option set" case as the silent, fully-backward-compatible default path.

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

## 4. Step-by-step implementation plan

### Step 1 — `missionoptions` plumbing
1. Add `SPICE_meta_kernel` field, default, parser entry, and writer entry in
   `src/Core/missionoptions.h` / `.cpp`.
2. Mirror in `PyEMTG/MissionOptions.py` (`__init__`, read loop, write method).

### Step 2 — `EMTG_v9.cpp` load/unload changes
1. Introduce `using_meta_kernel` / `meta_kernel_path` locals alongside the
   existing `SPICE_files_*` vectors.
2. Branch the load block per §3.2; keep the existing flat-file loop intact in
   the `else` branch (no logic changes to it).
3. Branch the unload block per §3.3.
4. Keep the existing `erract_c`/`errprt_c` error-suppression toggles scoped the
   same way they are today (currently only wrapped around the leap-second/
   reference-frame load); extend that scope to cover the meta-kernel `furnsh_c`
   call too, and decide/implement the error surfacing from §3.4.

### Step 3 — Documentation
1. Add `SPICE_meta_kernel` to wherever `SPICE_leap_seconds_kernel` /
   `SPICE_reference_frame_kernel` are documented for users (options reference
   docs under `docs/`).
2. Add a short "Using a SPICE meta-kernel" subsection near the existing
   SPICE/ephemeris documentation, including the delivery contract from §3.5 and
   the priority rule.
3. Note in the changelog/release notes that this is additive and backward
   compatible.

### Step 4 — Example/fixture
1. Add a small, redistributable example `meta_kernel.tm` (e.g. under
   `testatron/universe/` or a new `tests/` fixture) referencing a couple of the
   already-available `naif0012.tls` / `pck00010.tpc` kernels plus one small
   `.bsp`, so the new path has a concrete, runnable example independent of the
   (non-redistributable) OSIRIS-REx kernel set shown in the requirements doc.

## 5. Verification plan

Since this repo's C++ "tests" are small standalone driver executables (see
`src/Testing/missionoptions_tests/missionoptions_testbed_driver.cpp`) rather
than a gtest-style unit framework, verification is primarily:

1. **Missionoptions round-trip**: extend the `missionoptions_tests` driver (or
   add a focused one) to set `SPICE_meta_kernel`, write an `.emtgopt`, re-read
   it, and assert the value round-trips.
2. **Flat-layout regression**: run an existing tutorial `.emtgopt`
   (e.g. one under `docs/0_Users/tutorial/...`) with `SPICE_meta_kernel` unset
   and confirm output/log is byte-for-byte equivalent to current behavior
   ("Completed loading SPICE kernels." + identical trajectory output) —
   this proves (ii) and confirms no regression.
3. **Meta-kernel load**: run `EMTGv9` against the Step 4 fixture with
   `SPICE_meta_kernel` set, confirm the flat `.bsp` loop is skipped (e.g. via
   log output), the mission still solves, and `unload_c` cleanly unloads the
   meta-kernel (no leaked kernel pool entries across repeated runs, if EMTGv9
   is ever invoked in a loop/batch mode).
4. **Error path**: run with `SPICE_meta_kernel` set to a non-existent filename
   and to a deliberately malformed `.tm` (bad `PATH_SYMBOLS`, missing
   referenced kernel) and confirm the chosen behavior from §3.4 occurs with a
   clear message, not a raw CSPICE abort or silent corruption.
5. **PyEMTG round-trip**: open/save an `.emtgopt` containing `SPICE_meta_kernel`
   through the PyEMTG GUI (or its options read/write module directly) and
   confirm the value is preserved.

## 6. Non-goals (this iteration)

- No change to `.emtg_universe` file format or `universe_folder` resolution.
- No change to `ephemeris_source == 2` (SplineEphem) behavior.
- No external staging/validation process, provenance hashing, or packaged
  launcher — that design is retired.
- No attempt to independently re-derive or override CSPICE's own kernel
  precedence/merging rules; CSPICE handles that natively when `furnsh_c` loads
  the meta-kernel.

## 7. Open questions / review decisions

1. Hard-fail vs. silent-fallback when `SPICE_meta_kernel` is set but the file
   is missing (§3.4) — recommend hard-fail.
2. Exact location/resolution rule if a third party wants the meta-kernel file
   itself to live outside `ephemeris_files/` (current design keeps it there for
   consistency with the other two `SPICE_*_kernel` options, while the kernels
   it references can live anywhere via its own `PATH_VALUES`).
3. Whether `SPICE_meta_kernel` should accept an absolute/relative path directly
   (bypassing the `ephemeris_files/` prefix) for deployments that prefer to
   keep the meta-kernel outside the universe folder entirely.
4. Where the redistributable example fixture (§4 Step 4) should live.
