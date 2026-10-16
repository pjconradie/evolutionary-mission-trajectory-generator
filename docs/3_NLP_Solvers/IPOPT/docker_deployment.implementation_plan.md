# EMTG Debian IPOPT Packaging Plan for ADSGNC

## Status and Objective

This is the upstream EMTG implementation plan for the authoritative ADSGNC
integration design. EMTG owns C++ compilation, IPOPT integration, verification,
and release artifacts. ADSGNC owns its Docker service, FastAPI endpoints,
container lifecycle, mounted mission data, and service orchestration.

The objective is a verified Debian 12 `linux/amd64` artifact that ADSGNC can
install in its `api_services_v1:1.0` service image without compiling EMTG:

```bash
emtg-toolchain package \
  --emtg-repo /path/to/evolutionary-mission-trajectory-generator \
  --output emtg_debian_902_20261013.tar.gz
```

The command must fail without publishing an archive if compilation,
verification, linkage validation, archive validation, or checksum generation
fails.

The upstream CLI retains its build and inspection commands and adds export:

```text
emtg-toolchain build   --emtg-repo PATH
emtg-toolchain run     --emtg-repo PATH -- COMMAND [ARGUMENT...]
emtg-toolchain shell   --emtg-repo PATH
emtg-toolchain package --emtg-repo PATH --output ARCHIVE.tar.gz
```

## Two-Tier Handoff

| Responsibility | EMTG upstream | ADSGNC downstream |
| --- | --- | --- |
| Source, IPOPT build, CSPICE static linkage, and regression verification | Owns | Consumes results |
| Debian Bookworm builder recipe and runtime dependency manifest | Owns and publishes | Installs listed runtime packages |
| `EMTGv9`, headless PyEMTG, and `EMTGRunner` | Builds and tests | Calls through its toolkit adapter |
| Release archive and SHA-256 manifest | Produces | Verifies before extraction |
| Service image and FastAPI routes | Provides no implementation | Owns |
| Kernel mounts, per-request work directory, retention, and container lifecycle | Provides configuration contract | Owns |

ADSGNC must not compile EMTG, copy the builder Dockerfile, or require an EMTG
C++ environment in its deployment image.

## Build and Runtime Contract

### Target platform and linkage

Build with Docker using `--platform linux/amd64` on Debian 12 Bookworm. Promote
the current [`tests/docker/Dockerfile.toolchain`](../../../tests/docker/Dockerfile.toolchain)
into the single canonical upstream builder recipe; do not maintain separate
test and release recipes.

The builder may install compilers and development packages. The deployed
binary must dynamically link only to standard Debian 12 runtime libraries:

| Required deployment package | Purpose |
| --- | --- |
| `coinor-libipopt1v5` | IPOPT runtime ABI |
| `libgsl27` | GNU Scientific Library |
| `libboost-filesystem1.74.0` | Boost filesystem |
| `libboost-system1.74.0` | Boost system |
| `libboost-serialization1.74.0` | Boost serialization |
| `libgomp1` | OpenMP runtime |
| `libgfortran5` | GNU Fortran runtime |
| `csh` | EMTG runtime shell dependency |

Build the bundled
`depend/cspice-c_pc_linux_gcc_64bit/cspice.tar.Z` into `libcspice.a` and link
it statically into `EMTGv9`. `ldd bin/EMTGv9` must have no unresolved entries,
no development or build-prefix paths, no CSPICE shared library, and no SNOPT
reference.

Pin the builder base image by digest, verify the CSPICE SHA-256 before Docker
build begins, and generate the final runtime package list from the verified
binary linkage. Record every package's actual Debian version in
`metadata.json`.

### ADSGNC runtime compatibility

The artifact target is ADSGNC's `api_services_v1:1.0` base image, which must
be Debian 12 Bookworm with Python 3.12. ADSGNC must use
`python:3.12-slim-bookworm` pinned by digest, or make its Docker build fail
unless `/etc/os-release` confirms Debian 12 before it installs runtime
packages. The upstream package suite verifies the artifact in
`python:3.12-slim-bookworm`; ADSGNC repeats the supplied smoke test after
installing the metadata-declared packages in its final service image. No
`gcc`, `g++`, `cmake`, or `make` is required in that image.

The dependency names are the deployment requirement. The recorded versions
are release provenance, not exact-version installation pins: ADSGNC installs
the named packages from its pinned Bookworm sources and its smoke test verifies
that `ldd` resolves the binary and the baseline mission runs. Exact
reproduction across future repository changes requires a separately agreed
APT snapshot or package mirror; it is not implied by this handoff contract.

## Release Files and Naming

The following filenames are examples. For EMTG version `902` and build
identifier `20261013`, upstream publishes:

```text
emtg_debian_902_20261013.tar.gz
emtg_debian_902_20261013.tar.gz.sha256
emtg_debian_902.tar.gz
emtg_debian_902.tar.gz.sha256
```

The first pair is immutable and must never be overwritten. The second pair is
the mutable ADSGNC compatibility alias, implemented as a symlink or copy of
that exact release and its matching checksum manifest. Update the alias only
as part of publishing a complete release; do not alter the versioned pair.
The alias checksum must name `emtg_debian_902.tar.gz`, so it works from the
ADSGNC artifact directory without command-line filename substitution.

Each checksum manifest must name the archive it verifies and must succeed with:

```bash
sha256sum -c emtg_debian_902.tar.gz.sha256
```

The package command rejects an existing versioned output unless an explicit
overwrite operation is requested for a non-release build. It stages and
validates both files in a temporary sibling release directory, then atomically
renames that directory into the versioned release location. It updates the
compatibility alias only after the versioned release is complete.

The archive and checksum cannot be atomically renamed as a pair at the
artifact-directory root. A publication interrupted while updating the alias
therefore leaves an invalid or absent alias pair; `sha256sum -c` must fail
closed. Recovery is to retain the immutable versioned release, remove only the
incomplete alias files, and rerun the alias-publication step. ADSGNC must not
extract an alias until its checksum command succeeds.

SHA-256 provides the agreed integrity check. Artifact-channel authenticity is
provided by ADSGNC's trusted release delivery path; detached signing is not
part of this handoff contract.

## Archive Layout and Assets

The archive unpacks into one root directory with no absolute or traversal
entries:

```text
emtg_debian_902/
├── bin/
│   └── EMTGv9
├── PyEMTG/
│   ├── __init__.py
│   ├── MissionOptions.py
│   ├── Mission.py
│   ├── EMTGRunner.py
│   ├── Body.py
│   └── ... required headless support modules
├── universe/
│   ├── ephemeris_data/
│   └── *.emtg_universe
├── hardware/
│   ├── LaunchVehicles/
│   ├── Propulsion/
│   └── PowerSystems/
├── docs/
│   └── tutorial/
│       └── OSIRIS-REx.emtgopt
└── metadata.json
```

`bin/EMTGv9` must retain its executable mode. The package implementation maps
the source-tree `Universe/` and `HardwareModels/` layout into the downstream
layout above. It must include:

- Base `Universe/*.emtg_universe` files.
- Baseline leap-second and planetary-constants files under
  `universe/ephemeris_data/`. Mission-specific planetary ephemerides and SPK
  kernels remain external mounted assets.
- Standard hardware libraries, organized under the archive's
  `hardware/LaunchVehicles/`, `hardware/Propulsion/`, and
  `hardware/PowerSystems/` directories.
- The OSIRIS-REx tutorial `.emtgopt` configuration under `docs/tutorial/`.
- The complete non-GUI dependency closure for `MissionOptions`, `Mission`, and
  `EMTGRunner`.

Do not include planetary ephemerides or mission SPK kernels, uploaded options,
mission-specific hardware/universe inputs, generated solutions, `.git`, build
directories, tests, GUI panels, or development-only files. ADSGNC mounts
mission kernels from `missions/<mission>/kernels/` at `/opt/kernels` and owns
all per-run inputs and outputs.

### Build metadata

Generate `metadata.json`; do not copy a hand-maintained file. It must be UTF-8
JSON and include at least:

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
    "version": "<verified-version>"
  },
  "runtime_dependencies": [
    "coinor-libipopt1v5",
    "libgsl27",
    "libboost-filesystem1.74.0",
    "libboost-system1.74.0",
    "libboost-serialization1.74.0",
    "libgfortran5",
    "libgomp1",
    "csh"
  ],
  "runtime_dependency_versions": {
    "coinor-libipopt1v5": "<verified-version>",
    "libgsl27": "<verified-version>",
    "libboost-filesystem1.74.0": "<verified-version>",
    "libboost-system1.74.0": "<verified-version>",
    "libboost-serialization1.74.0": "<verified-version>",
    "libgfortran5": "<verified-version>",
    "libgomp1": "<verified-version>",
    "csh": "<verified-version>"
  }
}
```

The JSON values shown are examples; the package generates the version, build
date, commit SHA, and package versions from the actual verified release build.
`build_date` is UTC ISO 8601 with a `Z` suffix. Package tests validate the
schema, archive filename/checksum pairing, and values derived from the verified
builder.

## Headless PyEMTG and Runner Contract

PyEMTG is EMTG's complete programmatic integration surface. ADSGNC exposes a
generic pass-through endpoint, `POST /v1/toolkit/emtg/execute`, rather than a
separate REST field for every EMTG option. The standard
`/v1/target/simulated_trajectory` route remains an ADSGNC adapter that
translates high-level scenario inputs before invoking the same runner.

The following must import in headless `python:3.12-slim-bookworm` without
`wxPython`, `matplotlib`, X11, or display requirements:

```python
from PyEMTG import MissionOptions, Mission, EMTGRunner
```

[`PyEMTG/Mission.py`](../../../PyEMTG/Mission.py) currently imports plotting
code, so plotting and GUI imports must be deferred to plotting-only functions
or split into optional modules before release.

`PyEMTG/EMTGRunner.py` provides the supported API and CLI. It accepts an
options file or `MissionOptions` object, executes:

```python
subprocess.run(
    ["/opt/toolkit/emtg/bin/EMTGv9", options_path],
    capture_output=True,
    text=True,
    timeout=timeout_seconds,
    cwd=run_dir,
)
```

It must not invoke a shell. It captures stdout/stderr, preserves the actual
return code, parses a produced `.emtg` solution into `Mission`, and returns
structured data for process, parser, optimizer/convergence, and feasibility
outcomes. A process success does not itself prove feasibility.

The runner exposes the raw return code separately from its wrapper status. It
does not promise meanings for EMTG exit codes other than preserving them. The
wrapper status is one of:

| Wrapper status | Meaning |
| --- | --- |
| `completed` | Process returned and any produced solution was parsed |
| `launch_error` | Executable could not be started |
| `timed_out` | `subprocess.run` raised a timeout |
| `process_failed` | Process returned a non-zero code |
| `solution_missing` | Process completed but produced no expected solution |
| `solution_malformed` | Produced solution could not be parsed |

For a parsed solution, `worst_constraint_violation <= 1e-5` is feasible;
a larger value is an infeasible incumbent and must be returned with an
explicit warning. Launch failure, timeout, non-zero process exit, missing
solution, malformed solution, optimizer state, and feasibility remain distinct
structured result fields.

## ADSGNC Container Path Contract

| Resource | Container path | Environment variable |
| --- | --- | --- |
| EMTG executable | `/opt/toolkit/emtg/bin/EMTGv9` | `EMTG_BIN_PATH` |
| Packaged universe | `/opt/toolkit/emtg/universe` | `EMTG_UNIVERSE_DIR` |
| Mounted SPICE kernels | `/opt/kernels` | `SPICE_KERNEL_DIR` or `EMTG_SPICE_DIR` |
| Packaged hardware | `/opt/toolkit/emtg/hardware` | `EMTG_HARDWARE_DIR` |
| Isolated run directory | `/opt/work/<run_id>/` | none |

Use this precedence for universe, kernel, hardware, and output path values:

1. Explicit fields from `EmtgExecutionRequestModel.raw_options`.
2. The relevant container environment variable.
3. The value in the selected baseline `.emtgopt` template.

The runner/wrapper rewrites legacy Windows drive paths such as `C:\...` to the
matching container locations before running EMTG. It preserves normal Linux
forward-slash paths. Universe, hardware, and SPICE paths remain independently
configured; a value for one resource is never used as a fallback for another.

The ADSGNC service accepts an uploaded options file or an approved template
identifier and its `raw_options` overrides, never an arbitrary host filesystem
path. It writes the resolved options to `/opt/work/<run_id>/`, mounts mission
inputs and `/opt/kernels` read-only where possible, and grants writable access
only to the isolated run directory. ADSGNC owns output retention and cleanup.

At the service boundary, ADSGNC validates uploaded filenames and every
path-valued option before calling the runner. A value must either resolve under
the request's `/opt/work/<run_id>/` directory or be an approved read-only
path beneath `/opt/toolkit/emtg/` or `/opt/kernels`; reject absolute or
relative traversal that resolves elsewhere and reject output paths under
read-only mission, toolkit, or kernel mounts.

## Upstream Release Gates

`emtg-toolchain package` publishes a release only when these upstream-owned
checks pass:

1. Existing EMTG unit tests, IPOPT verification, CMake policy probes, and
   baseline mission regressions pass in the canonical builder.
2. The CSPICE archive checksum matches the pinned value before Docker runs.
3. `ldd bin/EMTGv9` passes the linkage contract in a clean Bookworm runtime
   image with the metadata-declared packages installed.
4. The clean runtime image imports `MissionOptions`, `Mission`, and
   `EMTGRunner` without GUI packages, then runs a baseline IPOPT mission.
5. Runner tests cover request-option precedence, Windows-path rewriting,
   explicit Linux paths, launch failure, raw return-code preservation, timeout,
   missing/malformed solutions, captured logs, optimizer state, and feasible
   versus infeasible parsed solutions.
6. Archive tests verify the required layout and assets, forbidden content,
   tar-entry safety, `EMTGv9` mode, metadata, checksum verification, and clean
   extraction.

## ADSGNC Deployment Acceptance

The following downstream checks are required before deployment, but are not
preconditions of `emtg-toolchain package` and do not require the upstream
command to access the ADSGNC repository or environment:

1. The ADSGNC Docker build pins `python:3.12-slim-bookworm` by digest or
   verifies Debian 12 before installing the named runtime packages.
2. The service image verifies the archive checksum before extraction, installs
   the named runtime packages, and runs the upstream smoke test.
3. Toolkit health confirms the executable and headless PyEMTG imports.
4. The OSIRIS-REx baseline passes through the ADSGNC endpoint with
   `/opt/kernels` mounted read-only and a unique `/opt/work/<run_id>/`.
5. API tests reject unsafe uploaded filenames and path-valued overrides,
   including traversal and attempted writes to read-only mounts.

## Delivery Sequence

1. Establish the canonical upstream Bookworm builder and its pinned CSPICE
   input from [`tests/docker/Dockerfile.toolchain`](../../../tests/docker/Dockerfile.toolchain).
2. Implement `emtg-toolchain package` with validated staging, metadata
   generation, immutable versioned output, and ADSGNC compatibility alias.
3. Make PyEMTG core imports headless and implement `EMTGRunner` with the
   documented result, path, and legacy Windows-path behavior.
4. Add package, linkage, runner, archive, and clean-runtime tests.
5. Update IPOPT and PyEMTG documentation with the package command, package
   metadata, runtime `apt` list, checksum verification, archive layout,
   container paths, and mounted-kernel configuration.
6. Deliver the archive and its checksum to ADSGNC's
   `toolkits/emtg/emtg_debian_902/app/` directory. ADSGNC performs extraction,
   service deployment, FastAPI wiring, and container lifecycle management.

## Non-Goals

- Publishing a Docker image or requiring ADSGNC to run the upstream builder.
- Providing ADSGNC service, FastAPI, client, registry, or deployment code in
  the EMTG repository.
- Shipping a CSPICE shared library, SNOPT, planetary SPK kernels, GUI
  dependencies, or build tools in the deployment artifact.
- Replacing the ADSGNC pass-through with an incomplete EMTG-specific REST API.
