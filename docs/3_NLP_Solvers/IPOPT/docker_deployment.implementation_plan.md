# EMTG Docker Deployment and Artifact Packaging Plan

## Purpose

Define the upstream EMTG build and packaging work required to deploy EMTG in
ADSGNC. EMTG owns the source build, IPOPT integration, verification suites,
Docker compilation recipe, and a reproducible binary artifact. ADSGNC consumes
that artifact and owns its service image, container lifecycle, and mission
workflow integration.

This plan follows the artifact contract in
[`docker_deployment.implementation_plan.adsgnc_specifications.md`](./docker_deployment.implementation_plan.adsgnc_specifications.md).
Where an earlier plan described a separate toolchain repository owning Docker
build/run lifecycle, that ownership model is superseded: it is not a
prerequisite for this upstream-to-downstream artifact handoff.

## Ownership Boundary

| Responsibility | Upstream EMTG | Downstream ADSGNC |
| --- | --- | --- |
| EMTG source, IPOPT integration, and verification suites | Owns | Consumes tested artifact |
| Debian Docker compilation recipe and build environment | Owns | Does not build EMTG from source |
| Binary artifact packaging and build metadata | Owns | Ingests the archive |
| Service image, container lifecycle, and mission workflows | Provides runtime contract | Owns |
| Runtime configuration and mounted mission kernels | Supports configurable paths | Supplies configuration and mounts |

The upstream `emtg-toolchain` CLI provides `build`, `run`, and `shell` for
upstream development and verification, plus an explicit `package` operation
for artifact export. These commands do not transfer downstream service
container lifecycle ownership to EMTG. ADSGNC must not need EMTG's C++ build
environment to consume the archive.

## Target Build and Runtime Contract

Build and package for:

- `linux/amd64`.
- Debian 12 (Bookworm), using a compatible base such as
  `python:3.12-slim-bookworm`.
- Python 3.12-compatible PyEMTG modules.

The compiled `EMTGv9` executable must resolve its shared libraries from
standard Debian 12 locations. Its runtime contract is:

- IPOPT: `coinor-libipopt1v5` (or the compatible runtime ABI from
  `coinor-libipopt-dev`).
- GSL: `libgsl27`.
- Boost: `libboost-filesystem1.74.0`, `libboost-system1.74.0`, and
  `libboost-serialization1.74.0`.
- Fortran and OpenMP runtimes: `libgfortran5` and `libgomp1`.
- CSPICE: compile the bundled `libcspice.a` statically into `EMTGv9`, or
  include it in the archive so deployment does not require a CSPICE compiler
  setup.

Verify `ldd bin/EMTGv9` in a clean Debian 12 container. All dependencies must
resolve, with no local development paths or SNOPT references.

## Archive and Metadata

Add an `emtg-toolchain package` (or equivalent) operation that builds in the
verified Debian Docker environment and exports a `.tar.gz` archive, by default
named `emtg_debian_902.tar.gz`. The archive must contain this top-level layout:

```bash
emtg-toolchain package \
  --emtg-repo /path/to/evolutionary-mission-trajectory-generator \
  --output emtg_debian_902.tar.gz
```

```text
emtg_debian_902/
├── bin/
│   └── EMTGv9
├── PyEMTG/
│   ├── __init__.py
│   ├── MissionOptions.py
│   ├── Mission.py
│   ├── EMTGRunner.py
│   └── ... supporting PyEMTG modules
├── universe/
│   ├── ephemeris_data/
│   └── ... standard baseline universe assets
├── hardware/
│   ├── LaunchVehicles/
│   ├── PowerSystems/
│   └── Propulsion/
├── docs/
│   └── tutorial/
│       └── ... reference mission configurations
└── metadata.json
```

Preserve the executable permission on `bin/EMTGv9`. Include all supporting
PyEMTG modules and required baseline universe and hardware data; do not package
only the example files shown above.

`metadata.json` records build provenance and the runtime contract. It must
include the EMTG version, build timestamp, source commit SHA, target platform,
base OS, solver name/package/version, and runtime dependency package names.
For example:

```json
{
  "emtg_version": "9.0.2",
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

Generate the build timestamp and commit SHA from the actual package build;
the example values above are illustrative, not values to hardcode.

## Headless PyEMTG Interface

ADSGNC invokes EMTG programmatically, so the packaged interface must work in a
headless Python 3.12 environment:

1. `from PyEMTG import MissionOptions, Mission, EMTGRunner` must succeed
   without `wxPython`, `matplotlib`, or an active X11 display. The core
   `MissionOptions.py`, `Mission.py`, and `EMTGRunner.py` modules must have no
   hard dependencies on graphical libraries.
2. `MissionOptions.py` and `EMTGRunner.py` must allow callers to override
   `universe_folder`, `HardwarePath`, SPICE kernel paths, and output/working
   directories. Path handling must support standard Linux forward-slash paths,
   including paths such as `/opt/kernels/...`.
3. `EMTGRunner.py` must provide a Python function or CLI that accepts an
   options file or object, executes `EMTGv9` with managed subprocess handling,
   supports timeouts, and parses the generated `.emtg` solution into a
   `PyEMTG.Mission` object. On optimizer errors or constraint violations,
   provide structured return codes and captured stdout/stderr.

## SPICE Kernel Configuration

Do not hardcode host-specific CSPICE kernel paths in packaged files.
`PyEMTG` and `EMTGv9` must allow the kernel directory to be supplied at runtime
through an environment variable such as `SPICE_KERNEL_DIR` or
`EMTG_UNIVERSE_DIR`, or through option parameters such as `universe_folder`.
This allows ADSGNC to mount shared mission kernels at `/opt/kernels`.

## Implementation Sequence

1. Keep the Debian Docker compilation recipe and EMTG IPOPT verification
   environment under upstream EMTG ownership. Pin and document the target
   platform, Debian base, IPOPT/runtime dependencies, and CSPICE handling.
2. Add `emtg-toolchain package` (or an equivalent explicit export target) to
   build in that verified environment, assemble the required archive layout,
   generate `metadata.json`, and write the requested `.tar.gz` output.
3. Audit the packaged PyEMTG core modules for GUI imports and hard
   dependencies. Add the path overrides, headless execution helper, timeout
   handling, solution parsing, and structured failure output required by the
   interface contract.
4. Ensure universe and kernel resolution is configurable at runtime and does
   not depend on paths from the build host.
5. Deliver the tested `emtg_debian_902.tar.gz` to ADSGNC for placement in
   `toolkits/emtg/emtg_debian_902/app/`. ADSGNC then builds its service image
   and manages container lifecycle independently.

## Verification

Do not produce a release archive unless upstream unit and integration tests
pass, including IPOPT verification, CMake policy probes, and baseline mission
regression tests. Retain the existing IPOPT source-verification coverage:
backend probes, benchmark replay/refinement stages, and every executable
immutable tutorial source must pass under
`python -m pytest --ipopt-verification -q`.

This gate preserves immutable tutorial and benchmark references while accepting
only their reviewed current outcomes. Known schema or refinement differences
remain explicit comparison diagnostics; an execution failure or any changed
reviewed outcome blocks release verification.

The artifact is ready for ADSGNC only when all of the following are verified:

1. The package command uses the verified `linux/amd64` Debian 12 build
   environment and refuses to export after required tests fail.
2. The archive has the specified top-level directory structure, complete
   runtime assets, executable `bin/EMTGv9`, and valid build metadata.
3. `ldd bin/EMTGv9` resolves all dependencies in a clean Debian 12 container,
   without local development paths or SNOPT.
4. The packaged PyEMTG core imports and runs in headless
   `python:3.12-slim-bookworm`, without GUI dependencies or display access.
5. A smoke mission verifies configurable universe, hardware, SPICE kernel,
   working, and output paths, successful result parsing, timeout behavior,
   and structured optimizer failure output.
6. ADSGNC can consume the archive without compiling EMTG or requiring a
   separate CSPICE compiler setup.

## Documentation Updates

Update the directly related documentation as the implementation lands:

- `docs/3_NLP_Solvers/IPOPT/ipopt.readme.md`: Debian build recipe, runtime
  dependencies, packaging command, and artifact contract.
- `docs/3_NLP_Solvers/IPOPT/tests.readme.md`: verification gates required
  before packaging.
- `docs/2_Missions/osiris-rex/docs/osiris_rex.readme.md`: any affected
  upstream mission invocation or packaging usage.
- `emtg-toolchain` documentation: `package` options, archive layout, metadata,
  and headless runtime contract.
- ADSGNC-facing integration documentation: archive handoff location and
  configurable runtime/kernel mounts.

## Non-Goals

- Moving ADSGNC's service container lifecycle into the EMTG repository.
- Requiring ADSGNC to build EMTG from source or carry EMTG's Docker recipe.
- Hardcoding host-specific mission kernel paths in the artifact.
- Changing the IPOPT solver contract, SNOPT baseline policy, or existing
  verification acceptance criteria.
