# Using a SPICE meta-kernel

`SPICE_meta_kernel` is an optional string mission option. When set, it
replaces the existing "Leap seconds kernel" / "Frame kernel" options and the
flat `*.bsp` file scan (both documented in the Ephemeris Settings section of
the EMTG user guide, `s-physics.tex`) with a single SPICE meta-kernel (`.tm`)
furnished directly through CSPICE.

## What a meta-kernel is

A meta-kernel is a single SPICE text kernel that lists every leap-second,
frame, and ephemeris kernel to load, via its own `KERNELS_TO_LOAD` /
`PATH_SYMBOLS` / `PATH_VALUES` entries. It lets a mission's full kernel set be
delivered, ordered, and versioned as one unit instead of as separate EMTG
options. See the
[JPL NAIF kernel documentation](https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/kernel.html)
for how to author one.

## Behavior

- **Default**: `""` (empty). EMTG's existing flat-file kernel loading is used
  unchanged — this option is fully backward compatible.
- **When non-empty**: EMTG loads *only* the named meta-kernel through
  CSPICE's `furnsh_c` and does not perform the flat `*.bsp` scan or
  separately load the Leap seconds kernel / Frame kernel settings. Those two
  settings, and any flat `*.bsp` files in the Universe folder's
  `ephemeris_files` directory, are ignored once a meta-kernel is configured.

## Path resolution

The value may be given in either of two forms:

- A **bare filename** (e.g. `meta_kernel.tm`, no directory component) is
  resolved relative to `<universe_folder>/ephemeris_files/`, exactly like the
  existing Leap seconds kernel and Frame kernel settings. This preserves
  tutorial-style compatibility — drop the file into `ephemeris_files/`.
- An **absolute or explicitly relative path** (e.g.
  `/opt/emtg/input/kernel-set/meta_kernel.tm`) is used directly. This
  supports a reviewed, third-party kernel set mounted outside the Universe
  folder.

Either way, the meta-kernel's own `PATH_SYMBOLS` / `PATH_VALUES` may point
anywhere on disk for the individual kernel files it lists — only the
meta-kernel file itself needs to be locatable via one of the two forms above.

## Priority and error handling

A configured meta-kernel is always required to take priority once set, never
merely preferred when conveniently present:

- If `SPICE_meta_kernel` is non-empty but the resolved file cannot be found,
  EMTG halts the run with a descriptive error before any CSPICE call is made.
  It never silently falls back to flat-file loading.
- If CSPICE fails to load the meta-kernel (for example because of an
  unresolved `PATH_SYMBOLS` entry or a `KERNELS_TO_LOAD` entry pointing at a
  missing kernel), EMTG surfaces the CSPICE diagnostic in a clear
  `std::runtime_error` rather than a raw CSPICE abort, unexplained downstream
  failure, or silent fallback.

## Third-party delivery contract

```text
<universe_folder>/
├── ephemeris_files/
│   ├── meta_kernel.tm          <- new, name given by SPICE_meta_kernel
│   ├── naif0012.tls            <- still present if referenced, or resolved
│   └── ...                     <- existing flat *.bsp files, now unused if
│                                   meta-kernel is active, but harmless if left
├── kernels/                    <- arbitrary location, resolved via the
│   ├── lsk/                       meta-kernel's own PATH_SYMBOLS/PATH_VALUES;
│   ├── pck/                       does not need to live under
│   └── spk/...                    ephemeris_files/ at all
```

No change to `universe_folder` resolution or the `.emtg_universe` file format
is needed — only the kernel-loading step inside EMTGv9 changes.

## Option reference

| | |
|---|---|
| Data type | `string` |
| Default value | `""` (empty; flat-file loading is used) |
| `.emtgopt` key | `SPICE_meta_kernel` |

## See also

- `docs/0_Users/emtg_user_guide/options/s-physics.tex`, "Ephemeris Settings"
  — the existing Leap seconds kernel / Frame kernel / Ephemeris Source
  options this feature is an alternative to.
- `docs/enhancements/meta-kernel-capabilities/meta_kernel_capabilities.plan.md`
  — the full design and implementation plan for this feature.
