# EMTG Debian IPOPT Archive Implementation Plan

## Purpose and Delivery Boundary

Implement the upstream portion of
[`emtg_archive.design.md`](emtg_archive.design.md): a reproducible Debian 12
`linux/amd64` EMTG/IPOPT archive, a supported headless Python runner, and
release gates that prevent publication of an invalid artifact.

This repository must provide the artifact, its checksum, metadata, runtime
dependency contract, and the documented smoke test. It must **not** implement
ADSGNC's Docker image, FastAPI endpoints, upload handling, service lifecycle,
or kernel mounting. Those remain downstream acceptance responsibilities.

## Current-State Findings

The implementation should extend the following existing assets rather than
creating a parallel build flow:

| Existing surface | Relevant state | Implementation consequence |
| --- | --- | --- |
| [`tests/docker/Dockerfile.toolchain`](../../../tests/docker/Dockerfile.toolchain) | Already pins `python:3.12-slim-bookworm`, verifies CSPICE, builds static CSPICE, and installs IPOPT build dependencies. | Promote this file into the sole canonical builder definition; parameterize or add adjacent packaging support rather than introducing another builder Dockerfile. |
| [`tests/integration/conftest.py`](../../../tests/integration/conftest.py) | Already builds `EMTGv9` in Docker, verifies `ldd`, and runs baseline missions. | Reuse its Docker support and mission preparation patterns for package and clean-runtime integration tests. |
| [`CMakeLists.txt`](../../../CMakeLists.txt) and [`src/CMakeLists.txt`](../../../src/CMakeLists.txt) | IPOPT is selected through `EMTG_NLP_SOLVER`; `EMTGv9` is built but installed to a source-tree-derived destination. | Add an explicit staging/install destination usable by the packaging command without changing normal local-build behavior. |
| [`PyEMTG/Mission.py`](../../../PyEMTG/Mission.py) and [`PyEMTG/MissionOptions.py`](../../../PyEMTG/MissionOptions.py) | They are legacy top-level modules; `Mission.py` imports other PyEMTG modules without package-qualified imports and has plotting imports inside plotting paths. No `PyEMTG/__init__.py` or `EMTGRunner.py` exists. | Establish and test a supported package import path, preserve legacy imports where required, defer optional plotting imports, and add the runner as a new module. |
| [`Universe/`](../../../Universe) and [`HardwareModels/`](../../../HardwareModels) | Base universe files, leap-second/planetary-constants files, and standard hardware files exist, but not in the archive's required directory taxonomy. | Implement an explicit allowlist and source-to-archive mapping; do not package a broad recursive copy. |
| [`docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/OSIRIS-REx.emtgopt`](../../../docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS-REx/OSIRIS-REx.emtgopt) | Provides the designated tutorial options source. | Stage a verified tutorial copy as `docs/tutorial/OSIRIS-REx.emtgopt` and use a prepared copy in the runtime smoke test. |

## Implementation Sequence

### 1. Define the archive implementation module and command boundary

1. Add a small, standard-library-only Python package under a new
   repository-owned tooling location (for example `tools/emtg_toolchain/`).
   Keep release orchestration separate from PyEMTG parsing and GUI code.
2. Add the `emtg-toolchain` executable entry point using the repository's
   established invocation convention. It must expose:

   ```text
   emtg-toolchain build   --emtg-repo PATH
   emtg-toolchain run     --emtg-repo PATH -- COMMAND [ARGUMENT...]
   emtg-toolchain shell   --emtg-repo PATH
   emtg-toolchain package --emtg-repo PATH --output ARCHIVE.tar.gz
   ```

3. Make each subcommand validate that `--emtg-repo` is an EMTG checkout,
   resolve it to an absolute path, and return a nonzero status with a specific
   error for invalid inputs, Docker failure, build failure, or output-policy
   failure. Never continue after a failed prerequisite.
4. Make `build`, `run`, and `shell` wrappers over the same canonical Docker
   image/build configuration used by `package`; do not fork compiler flags,
   mounts, or CSPICE verification logic between commands.
5. Define testable data types/helpers for repository layout, builder identity,
   artifact naming, package inventory, metadata, and publication paths. Keep
   filesystem mutation in the command layer so unit tests can exercise
   validation and archive generation with temporary directories.

**Acceptance:** `--help` documents all four commands; invalid repositories,
missing Docker, invalid output suffixes, and preexisting immutable release
outputs fail explicitly without creating an archive or checksum.

### 2. Make the canonical builder release-ready

1. Retain the existing Bookworm base-image digest in
   [`tests/docker/Dockerfile.toolchain`](../../../tests/docker/Dockerfile.toolchain)
   and retain build-time CSPICE SHA-256 validation.
2. Add a builder invocation that always requests `--platform linux/amd64`,
   passes the pinned CSPICE digest, and records the resulting image identity.
   It must work on native amd64 and Docker Desktop emulation without silently
   building for the host architecture.
3. Configure EMTG in a clean build directory using `EMTG_NLP_SOLVER=IPOPT`,
   the CMake configuration values currently supplied by the integration
   fixtures, and a package-specific install/staging prefix. Build `EMTGv9`
   from that configuration.
4. Update CMake only as needed to support a conventional install destination
   for `EMTGv9` (for example `bin/EMTGv9`) when a staging prefix is supplied.
   Preserve existing source-tree output behavior for ordinary developer
   configurations.
5. Capture the verified IPOPT package version from `pkg-config` and collect
   the exact installed Debian versions for every declared runtime package.
   Produce these values after the build, not from literals.
6. Run `ldd` on the staged executable and reject any unresolved dependency,
   CSPICE shared-library dependency, SNOPT reference, or absolute
   build/development-prefix path. Derive the required runtime package names
   from this reviewed linkage result and assert the required Bookworm package
   set from the design.

**Acceptance:** a clean builder produces a dynamically IPOPT-linked,
statically CSPICE-linked `EMTGv9`; its linkage has no `not found` lines,
no SNOPT dependency, and no `libcspice.so`.

### 3. Inventory and stage the archive payload safely

1. Implement an explicit manifest builder rather than copying repository
   directories recursively. Each entry records its source, archive-relative
   destination, file mode, and reason for inclusion.
2. Stage `EMTGv9` at `bin/EMTGv9` with executable permissions retained.
3. Map the assets into the design layout:

   | Source | Archive destination | Inclusion rule |
   | --- | --- | --- |
   | `Universe/*.emtg_universe` | `universe/` | Include each committed base universe definition. |
   | `Universe/ephemeris_files/naif0012.tls` and `pck00010.tpc` | `universe/ephemeris_data/` | Include only the baseline files; exclude SPK/planetary ephemerides. |
   | `HardwareModels/` | `hardware/LaunchVehicles/`, `hardware/Propulsion/`, and `hardware/PowerSystems/` | Classify each standard distributable hardware asset in a reviewed mapping table. Do not infer by filename at extraction time. |
   | OSIRIS-REx tutorial options | `docs/tutorial/OSIRIS-REx.emtgopt` | Copy the selected tutorial source after validating it can be parsed/prepared for packaged paths. |
   | Headless PyEMTG closure | `PyEMTG/` | Include only the modules imported by the supported public API and their non-GUI dependencies. |

4. Add denylist checks for `.git`, CMake build directories, test directories,
   GUI panels, generated solutions, user uploads, proprietary solver material,
   and mission SPK/planetary-kernel files. Fail packaging if any proposed
   manifest entry matches a denylisted category.
5. Build the tar archive from the staged root using archive-relative paths
   only. Before writing, validate every entry is relative, normalized, beneath
   exactly one root directory, and neither absolute nor traversal-capable.
   Validate the same properties by reopening the final tarball.
6. Set archive ownership deterministically to the packaging identity where
   supported, preserve the executable bit for `bin/EMTGv9`, and write the
   tarball with a single root named from the immutable release version.

**Acceptance:** a test opens the archive without extracting it and verifies
the required layout, no forbidden content, no unsafe tar names, and an
executable `bin/EMTGv9`.

### 4. Implement generated metadata and fail-closed publication

1. Derive the release version from the repository's authoritative version
   source; document the exact source selected. Read the Git commit SHA with
   `git rev-parse HEAD` and fail if it cannot be determined.
2. Generate UTF-8 `metadata.json` during staging with:
   - EMTG version, UTC ISO-8601 `build_date`, commit SHA, target platform, and
     `debian:12-bookworm` base OS;
   - IPOPT solver name, build package, and verified version;
   - the required runtime package names; and
   - actual installed versions keyed by package name.
3. Validate generated metadata against a repository-owned JSON Schema or
   equivalent strict validator. Tests must assert the required keys, value
   formats, package/value correspondence, and values captured from the
   verified builder.
4. Name immutable artifacts
   `emtg_debian_<version>_<build-id>.tar.gz` and their checksum files. Reject
   preexisting immutable artifacts by default. If a non-release overwrite
   mode is introduced, make it explicit, opt-in, and unavailable for normal
   release naming.
5. Create the tarball and its single-line SHA-256 manifest in a uniquely named
   temporary sibling directory. Verify the checksum before publication.
6. Validate archive contents and metadata, then atomically rename the complete
   versioned release directory into place. Only after that succeeds, publish
   or replace the mutable `emtg_debian_<version>.tar.gz` compatibility alias
   and generate a checksum manifest whose recorded filename is the alias
   filename.
7. On every failure, remove only the command-owned temporary staging and
   sibling release directories; leave existing immutable releases untouched.
   If alias publication is interrupted, leave the alias absent or invalid so
   `sha256sum -c` fails closed, and document the recovery command.

**Acceptance:** both immutable and alias manifests pass `sha256sum -c` from
their artifact directory; failed builds cannot leave a newly usable archive or
checksum manifest behind.

### 5. Establish a headless PyEMTG package surface

1. Add `PyEMTG/__init__.py` defining the supported public imports:

   ```python
   from PyEMTG import MissionOptions, Mission, EMTGRunner
   ```

   Keep compatibility with current top-level `MissionOptions`/`Mission`
   imports used by existing tests and scripts; use package-qualified imports
   inside newly touched modules.
2. Trace the import closure for `MissionOptions` and `Mission` with a clean
   Python 3.12 environment. Convert only the closure's unconditional
   intra-PyEMTG imports to a package-safe compatibility pattern, avoiding
   unrelated modernization of all legacy modules.
3. Move imports of `matplotlib` and any GUI/display dependencies in
   [`PyEMTG/Mission.py`](../../../PyEMTG/Mission.py), its imported modules,
   and the runner closure into plotting-only methods. The parser/import path
   must not import `wx`, matplotlib, X11 bindings, or attempt display access.
4. Add an import-closure test run in `python:3.12-slim-bookworm` containing
   only the runtime Python dependencies. It must import the three public API
   names without GUI packages installed.
5. Use the import test's traced module list as the packaging allowlist for
   `PyEMTG/`; reject GUI-panel modules rather than relying on a future
   accidental import to reveal missing or unwanted files.

**Acceptance:** the clean runtime image executes the documented three imports
without `wxPython`, matplotlib, X11, or a display server.

### 6. Implement `PyEMTG.EMTGRunner`

1. Add [`PyEMTG/EMTGRunner.py`](../../../PyEMTG/EMTGRunner.py) with typed,
   serializable request/result dataclasses and a small CLI. It must accept
   either an options-file path or a `MissionOptions` instance.
2. Resolve the executable, universe, hardware, and SPICE locations using the
   documented precedence: explicit runner/request value, environment variable,
   then selected baseline option. Use defaults matching the archive container
   contract only when the relevant value is absent.
3. Before launch, create/validate an isolated run directory, materialize the
   resolved options file within it, and constrain all output paths to that
   directory. Accept read-only inputs only beneath the configured toolkit or
   kernel roots. Reject traversal after resolution, paths outside allowed
   roots, writes to read-only locations, arbitrary host paths, and malformed
   options-file inputs with explicit errors.
4. Inventory the selected tutorial/options templates for Windows paths. Add a
   reviewed, field-specific mapping table from each discovered legacy source
   prefix to exactly one approved container destination. Do not add a generic
   string replacement. Reject UNC paths, unrecognized Windows paths, and
   ambiguous matches; preserve ordinary Linux paths unchanged.
5. Invoke EMTG with `subprocess.run([binary, options_path], cwd=run_dir,
   capture_output=True, text=True, timeout=...)`; never use a shell. Capture
   stdout, stderr, duration, raw return code, resolved paths, and command
   arguments for diagnostics.
6. Model wrapper outcomes exactly as the design specifies:
   `completed`, `launch_error`, `timed_out`, `process_failed`,
   `solution_missing`, and `solution_malformed`. Preserve a parsed solution
   and diagnostic fields even when the process exited nonzero.
7. Locate the expected produced `.emtg` solution only within `run_dir`, parse
   it through `Mission`, and expose optimizer/convergence information and
   `worst_constraint_violation`. Mark feasibility at `<= 1e-5`; emit an
   explicit warning for a parsed infeasible incumbent without rewriting its
   process or wrapper status.

**Acceptance:** runner unit tests cover both input forms; precedence;
field-specific path mappings; Linux preservation; all path-rejection cases;
launch, timeout, nonzero-return, missing, and malformed-solution outcomes;
captured logs; raw return-code preservation; and feasible/infeasible parsed
solutions.

### 7. Add layered verification gates

1. Add fast unit tests for artifact naming, metadata generation/schema,
   manifest construction, tar safety, checksum content, publication sequencing,
   and all runner pure functions. Use temporary directories and fake subprocess
   results; these tests must not require Docker.
2. Add package-focused Docker integration fixtures adjacent to the current
   toolchain fixtures. Reuse the existing image creation and CSPICE checksum
   constants instead of duplicating image commands in test files.
3. In the builder, run the existing IPOPT CMake contract checks and targeted
   baseline mission regression before packaging. Reuse the established
   `EMTGv9`-based regression preparation where possible; do not create a second
   mission-comparison policy.
4. Start a fresh `python:3.12-slim-bookworm` runtime container with only the
   metadata-declared runtime packages installed. Verify:
   - `ldd bin/EMTGv9` resolves fully and meets the no-SNOPT/no-shared-CSPICE
     contract;
   - `from PyEMTG import MissionOptions, Mission, EMTGRunner` succeeds;
   - the runner executes a prepared OSIRIS-REx baseline using mounted
     mission-specific kernels rather than kernels copied into the archive; and
   - extracted files retain the required modes and are sufficient to run.
5. Test archive extraction into an empty directory, run both checksum
   manifests from that directory, and assert that failure injection (bad CSPICE
   digest, CMake failure, linkage failure, smoke-test failure, bad metadata, bad
   tar entry, or checksum write failure) prevents publication.
6. Add pytest markers consistent with the existing `integration`, `docker`,
   `toolchain`, and `clean_bootstrap` convention. Document focused package
   commands and the full release-gate command in the IPOPT test guide.

**Acceptance:** the complete package command succeeds only after all listed
unit and Docker gates pass; each injected gate failure is observable and leaves
no newly published artifact.

### 8. Update operator and downstream handoff documentation

1. Extend [`ipopt.readme.md`](ipopt.readme.md) with package/build/run/shell
   usage, required Docker platform, archive output location, expected
   duration/resource notes, and cleanup limited to known toolchain resources.
2. Update [`tests.readme.md`](docs/3_NLP_Solvers/IPOPT/tests.readme.md) with focused non-Docker unit
   tests, package integration tests, clean-runtime test, and full release-gate
   command. Keep generated-result examples separate from immutable baselines.
3. Add a package-consumption section describing:
   - archive layout and `metadata.json`;
   - the precise runtime `apt` package names;
   - `sha256sum -c` verification before extraction;
   - `/opt/toolkit/emtg`, `/opt/kernels`, and `/opt/work/<run_id>` path
     contracts and environment variables;
   - required mounted mission kernels and the fact that they are not shipped;
   - headless Python imports and `EMTGRunner` result/status behavior; and
   - alias fail-closed behavior and recovery.
4. Cross-link the design, this implementation plan, Docker toolchain guide,
   and API documentation. State clearly that ADSGNC repeats the smoke test in
   its final Debian 12 service image and owns all service/API validation.

**Acceptance:** an operator can build, verify, extract, and smoke-test the
artifact from the documentation without compiler tooling in the runtime
container, while a downstream integrator has no ambiguity about upstream versus
ADSGNC-owned responsibilities.

## Required Test Matrix

| Level | Focus | Required evidence |
| --- | --- | --- |
| Unit | Naming, JSON schema, manifest allow/deny rules, tar safety, checksum and atomic publication logic, runner path/status logic | No Docker; deterministic temporary-directory tests |
| Builder integration | CSPICE checksum, IPOPT CMake build, `EMTGv9` linkage, baseline mission | Existing toolchain probes extended with package-stage assertions |
| Archive integration | Required layout, mode, forbidden-content rejection, metadata derived from build, immutable and alias checksums | Archive reopened and extracted into an empty directory |
| Clean runtime | Declared packages only, `ldd`, headless imports, runner mission execution | Fresh Bookworm Python 3.12 runtime container |
| Failure injection | Every mandatory gate fails closed | No new archive, manifest, or valid alias after induced failure |

## Completion Criteria

The work is complete only when all of the following are true:

1. `emtg-toolchain package` creates a validated, checksummed, immutable
   Debian 12 amd64 archive and its compatibility alias.
2. The archive contains only the documented runtime closure, required assets,
   and generated metadata; it contains no unsafe tar entries, proprietary
   solver material, SPK kernels, build products, or GUI dependencies.
3. `EMTGv9` has the required IPOPT runtime linkage and static CSPICE linkage
   in a clean Bookworm runtime image.
4. The documented PyEMTG public imports work headlessly on Python 3.12, and
   `EMTGRunner` implements the documented subprocess, result, feasibility, and
   path-validation contracts.
5. Unit, builder, archive, clean-runtime, and failure-injection test gates
   pass and are documented.
6. The repository supplies a clear upstream handoff contract while leaving
   ADSGNC service deployment and endpoint implementation out of scope.
