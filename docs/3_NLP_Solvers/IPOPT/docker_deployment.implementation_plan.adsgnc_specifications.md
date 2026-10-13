# Upstream Specification: EMTG Artifact Packaging Contract for ADSGNC Integration

## 1. Context and Objective

The **ADSGNC** ecosystem integrates **EMTG** (Evolutionary Mission Trajectory Generator) as a core trajectory simulation and optimization toolkit.

To maintain clean separation of concerns and avoid coupling ADSGNC to upstream C++ build environments, we follow a **Two-Tier Pipeline (Build vs. Deployment)**:
1. **Tier 1 (Upstream EMTG Repository):** Canonical owner of source code, IPOPT integration, verification test suites, Docker compilation recipe, and **binary artifact packaging**.
2. **Tier 2 (Downstream ADSGNC Repository):** Ingests the packaged release archive, packages it into the ADSGNC service architecture (FastAPI on Debian 12 Bookworm), and manages the container lifecycle and mission simulation workflows.

This document specifies the **artifact contract** required from the upstream EMTG repository to enable automated, reproducible deployment in ADSGNC.

---

## 2. Upstream Toolchain Responsibility

The proposed upstream `emtg-toolchain` CLI should provide an explicit **export/package command** in addition to `build`, `run`, and `shell`:

```bash
emtg-toolchain package \
  --emtg-repo /path/to/evolutionary-mission-trajectory-generator \
  --output emtg_debian_<version>_<build_id>.tar.gz
```

Name immutable release archives
`emtg_debian_<version>_<build_id>.tar.gz`. Also provide the standard alias
`emtg_debian_902.tar.gz` for the ADSGNC import workflow; the alias must be
byte-identical to the versioned archive. Generate a companion
`<archive-name>.sha256` checksum file for each archive name provided (for
example, `emtg_debian_902.tar.gz.sha256`); the versioned archive and checksum
identify a specific build, and the alias checksum must be refreshed whenever
the alias is updated.

### Build & Packaging Guarantees
1. **Target Architecture & Platform:**
   - Platform: `linux/amd64`
   - Target Base OS: Debian 12 (Bookworm)
   - Python: 3.12 compatible (`python:3.12-slim-bookworm` or Debian 12 standard)
2. **Dynamic Linkage Contract:**
   - The compiled `EMTGv9` binary must link dynamically against standard Debian package versions available via `apt-get`:
     - IPOPT: `coinor-libipopt1v5` (or `coinor-libipopt-dev` runtime ABI)
     - GSL: `libgsl27`
     - Boost: `libboost-filesystem1.74.0`, `libboost-system1.74.0`, `libboost-serialization1.74.0`
     - Fortran/C runtime: `libgfortran5`, `libgomp1`
   - Bundled CSPICE static archive (`libcspice.a`) must be statically compiled into `EMTGv9`, eliminating runtime CSPICE library mismatches and any separate downstream CSPICE compiler setup.
   - Running `ldd bin/EMTGv9` inside a clean Debian 12 container must resolve all dependencies against standard Debian library locations, with **no references to local development paths or SNOPT**.
3. **Verification Before Export:**
   - The archive must only be produced if upstream unit and integration tests pass (including IPOPT verification, CMake policy probes, and baseline mission regression tests).
4. **Integrity Verification:**
   - Generate the SHA-256 checksum from the completed archive bytes.
   - Before extraction, ADSGNC's `importEmtg.csh` must run `sha256sum -c` against the companion `.sha256` file and fail without extracting if verification fails.

---

## 3. Archive Structure & Contents

The exported `.tar.gz` archive must unpack with the following top-level directory layout:

```
emtg_debian_902/
├── bin/
│   └── EMTGv9                          # Pre-compiled executable (linux/amd64, executable bit set)
├── PyEMTG/                             # Python interface modules
│   ├── __init__.py
│   ├── MissionOptions.py               # Options reader/writer
│   ├── Mission.py                      # Result parser
│   ├── EMTGRunner.py                   # Headless execution CLI & helper
│   ├── Body.py
│   └── ... (all supporting PyEMTG modules)
├── universe/                           # Standard baseline universe files
│   ├── ephemeris_data/
│   └── ...
├── hardware/                           # Standard propulsion, launch vehicle, power models
│   ├── LaunchVehicles/
│   ├── PowerSystems/
│   └── Propulsion/
├── docs/
│   └── tutorial/                       # Reference mission configs (e.g. OSIRIS-REx.emtgopt)
└── metadata.json                       # Build metadata and version manifest
```

### `metadata.json` Specification
The archive must include a `metadata.json` file describing the build provenance:
```json
{
  "emtg_version": "9.0.2",
  "build_id": "<build-id>",
  "build_date": "2026-10-13T10:00:00Z",
  "commit_sha": "<git-sha>",
  "target_platform": "linux/amd64",
  "base_os": "debian:12-bookworm",
  "solver": {
    "name": "ipopt",
    "package": "coinor-libipopt-dev",
    "version": "3.14.x"
  },
  "runtime_dependencies": [
    "coinor-libipopt1v5",
    "libgsl27",
    "libboost-filesystem1.74.0",
    "libboost-system1.74.0",
    "libboost-serialization1.74.0",
    "libgfortran5",
    "libgomp1"
  ]
}
```

---

## 4. Headless Python Interface Contract (`PyEMTG`)

ADSGNC consumes EMTG programmatically via Python inside a container service. The packaged `PyEMTG` must fulfill the following headless requirements:

1. **GUI Independence:**
   - `PyEMTG` must import cleanly in headless environments without requiring `wxPython`, `matplotlib`, or an active X11 display.
   - Core modules (`MissionOptions.py`, `Mission.py`, `EMTGRunner.py`) must have zero hard dependencies on graphical libraries.
2. **Configurable Path Resolution:**
   - `MissionOptions.py` and `EMTGRunner.py` must support programmatic overriding of:
     - `universe_folder`
     - `HardwarePath`
     - SPICE kernel paths
     - Output / working directories
   - Path rewriting must safely accept standard Linux forward-slash paths (`/opt/kernels/...`).
   - Resolve settings field by field in this precedence order: request payload overrides (`raw_options`), environment variables, then baseline `.emtgopt` file defaults.
3. **Headless Execution Helper (`EMTGRunner.py`):**
   - Provide a clean Python function or CLI that accepts an options file or options object and request overrides (`raw_options`), executes `EMTGv9` via managed `subprocess.run`, handles timeouts, and parses the produced `.emtg` solution into a `PyEMTG.Mission` object.
   - Return structured results with captured `stdout`, `stderr`, and constraint-violation metrics. Use return codes `0` (successful execution / optimization evaluated), `1` (options or universe configuration error), `2` (numerical crash), and `124` (timeout). Include optimization status and constraint metrics in the response; code `0` alone does not imply feasibility or convergence.

---

## 5. SPICE Kernel Expectations

1. **Decoupled Planetary Ephemerides:**
   - Do not hardcode host paths to CSPICE kernels inside the pre-packaged files.
   - `PyEMTG` and `EMTGv9` must allow specifying the kernel directory via environment variable (e.g. `SPICE_KERNEL_DIR` or `EMTG_UNIVERSE_DIR`) or via option parameters (`universe_folder`), enabling ADSGNC to mount shared mission kernels from the host to `/opt/kernels`.
2. **Deployment Paths and Run Isolation:**
   - Resolve the packaged executable at `/opt/toolkit/emtg/bin/EMTGv9` and baseline universe assets at `/opt/toolkit/emtg/universe`.
   - Mount shared SPICE kernels read-only at `/opt/kernels`.
   - Isolate each execution under its UUID-scoped working directory `/opt/work/<run_id>/` and direct generated files and outputs to that run directory.

---

## 6. Summary of Action Items for Upstream EMTG Repository

1. **Add Export Target in `emtg-toolchain`:**
   Implement `emtg-toolchain package` (or equivalent target) that compiles `EMTGv9` inside the verified Debian Docker builder and bundles the binary, `PyEMTG`, universe assets, and `metadata.json` into a `.tar.gz` archive.
2. **Verify Headless Execution and Runtime Contract:**
   Confirm that `from PyEMTG import MissionOptions, Mission, EMTGRunner` succeeds in headless `python:3.12-slim-bookworm` without GUI warnings or missing package errors. Verify path precedence, runner return codes, captured output, constraint metrics, kernel mount, and per-run directory isolation.
3. **Publish / Provide the Archive:**
   Provide the immutable versioned archive, its SHA-256 file, and the standard `emtg_debian_902.tar.gz` alias with its checksum for placement in ADSGNC's `toolkits/emtg/emtg_debian_902/app/`. ADSGNC must verify the checksum in `importEmtg.csh` before extraction.
