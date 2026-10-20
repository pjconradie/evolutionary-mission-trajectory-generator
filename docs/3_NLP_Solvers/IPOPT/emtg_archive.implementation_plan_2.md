# EMTG Debian IPOPT Archive Implementation Plan

## Objective

Deliver a versioned, checksummed `linux/amd64` Debian 12 archive that a
third-party deployment environment can unpack into its Docker image and
execute directly:

```bash
/opt/toolkit/emtg/bin/EMTGv9 /opt/work/<run-id>/request.emtgopt
```

The archive must contain an IPOPT-enabled `EMTGv9` executable and the
runtime EMTG assets that the third-party deployment environment will not mount
separately. It must have a
runtime-dependency list derived from the executable's actual linkage and a
reproducible clean-Bookworm smoke test.

## Scope and Ownership

### EMTG upstream owns

- Building `EMTGv9` with the IPOPT backend in the existing pinned Debian 12
  amd64 Docker toolchain.
- Packaging the executable, public runtime universe data, and public runtime
  hardware assets into one archive.
- Publishing a SHA-256 checksum and a runtime-dependency manifest.
- Documenting invocation behavior, packaged assets, required external inputs,
  and the clean-runtime smoke-test procedure.
- Verifying that a clean Bookworm runtime image can extract and execute the
  archive with the declared runtime packages.

### Third-party deployment environment owns

- Its Docker image, FastAPI endpoint, and API authentication/authorization.
- Supplying uploaded option files or approved templates and validating them.
- Mounting/providing mission-specific SPICE kernels and any mission-specific
  universe or hardware assets excluded from the archive.
- Creating an isolated writable run directory for each request.
- Invoking the fixed `EMTGv9` executable with an argument list and no shell.
- Timeouts, process cancellation, raw exit-code handling, log capture, output
  discovery, artifact retention, and cleanup.
- Returning raw process status, stdout/stderr, timeout state, and generated
  artifact references from its API.

The third-party deployment environment's direct pass-through accepts EMTG
arguments and inputs only. It must not accept an arbitrary shell command to
run inside the container.

## Explicit Non-Goals for This Phase

- Packaging PyEMTG or making PyEMTG imports headless.
- Adding `PyEMTG/__init__.py`, `PyEMTG/EMTGRunner.py`, or a Python runner API.
- Parsing `.emtg` solutions or defining structured mission/feasibility
  response semantics.
- Implementing path rewriting, request path validation, or run-directory
  confinement in EMTG Python code.
- Implementing third-party FastAPI routes, service lifecycle, mounted-volume
  management, or cleanup behavior.
- Immutable-release aliases, atomic alias publication, a metadata schema, or
  package-version provenance beyond the dependency manifest.
- Making the complete Testatron corpus a precondition for packaging.

## Existing Implementation Surfaces

| Surface | Current role | Planned use |
| --- | --- | --- |
| [`tests/docker/Dockerfile.toolchain`](../../../tests/docker/Dockerfile.toolchain) | Pinned Debian 12/Python 3.12 builder; installs IPOPT dependencies and rebuilds validated static CSPICE. | Keep as the one canonical builder recipe. |
| [`tests/integration/conftest.py`](../../../tests/integration/conftest.py) | Builds IPOPT EMTG in Docker, verifies linkage, and executes mission probes. | Reuse Docker/CMake conventions and mission preparation for archive smoke testing. |
| [`CMakeLists.txt`](../../../CMakeLists.txt) and [`src/CMakeLists.txt`](../../../src/CMakeLists.txt) | Select IPOPT and build `EMTGv9`. | Add only the staging/install support required to package the executable cleanly. |
| [`Universe/`](../../../Universe) | Contains public base universe files and basic SPICE support files. | Map required runtime files into the archive. |
| [`HardwareModels/`](../../../HardwareModels) | Contains standard public hardware files. | Map required runtime files into the archive. |

## Implementation Status

The following status records observed evidence from the current implementation
session; it is not a claim that all earlier plan acceptance criteria have been
audited.

| Plan phase | Evidence-based status |
| --- | --- |
| 1–6 | Implemented. The archive workflow builds a versioned IPOPT runtime archive, derives its runtime-package manifest from verified linkage, includes the allowlisted runtime payload, and publishes an adjacent SHA-256 checksum. A separate acceptance-criteria audit remains useful before a future change is declared ready. |
| 7 | Verified by the archive workflow. The unit suite passed with 23 tests. Hot archive integration passed in 35.55 seconds. Cold archive integration passed in 546.22 seconds. The cold deployment tutorial gate passed in 720.21 seconds, verifying all 17 cases and 33 required stages against the reviewed reference. The archive deployment adapter preserves the established `/artifacts` tutorial staging contract without changing source tutorial preparation or baselines. |
| 8 | Implemented and verified for EMTG 9.02. A cold-built `emtg-ipopt-9.02.tar.gz` and adjacent checksum were generated and checksum-verified. The exact archive passed the release baseline in 217.89 seconds: 17 cases, 33 stages, and `acceptable: true`. Its release record identified source commit `9dc80f4b6900485addd0e337ea077788e8e17cba`. The detailed per-case evidence was reviewed and then intentionally deleted; retain it for future release approvals. The remaining Phase 8 deliverable is the third-party distribution guide. |

Future releases must rerun the documented cold package and exact-archive
release-baseline commands, then retain the command output and evidence for the
release record.

## Implementation Layout and Resource Lifecycle

### Repository resources

The archive toolchain is production code in [`emtg_toolchain/`](../../../emtg_toolchain),
not pytest fixture code. Its initial files are:

| Resource | Lifecycle | Responsibility |
| --- | --- | --- |
| `emtg_toolchain/__init__.py` | Create; retain | Package identity and public command entry point. |
| `emtg_toolchain/__main__.py` | Create; retain | Enables `python -m emtg_toolchain`. |
| `emtg_toolchain/cli.py` | Create; retain | Parses `package --emtg-repo --output`, validates arguments, reports failures, and selects exit statuses. |
| `emtg_toolchain/docker.py` | Create; retain | Reuses the canonical Bookworm image contract, invokes Docker with `linux/amd64`, and runs the package build. |
| `emtg_toolchain/archive.py` | Create; retain | Builds the explicit payload manifest, stages `emtg/`, validates tar paths/layout, and writes the archive/checksum. |
| `emtg_toolchain/runtime.py` | Create; retain | Captures `ldd`, maps verified libraries to Debian runtime packages, and renders `RUNTIME_REQUIREMENTS.txt` and the archive README. |
| `tests/emtg_toolchain/unit/` | Create; retain | Unit-test directory. |
| `tests/emtg_toolchain/unit/test_cli.py` | Create; retain | `unit`-marked tests for argument, repository, output, and error handling. |
| `tests/emtg_toolchain/unit/test_emtg_archive_unit.py` | Create; retain | `unit`-marked tests for payload selection, tar safety/layout, modes, checksums, and cleanup. |
| `tests/emtg_toolchain/unit/test_runtime.py` | Create; retain | `unit`-marked tests for linkage parsing and runtime manifest generation. |
| `tests/emtg_toolchain/integration/` | Create; retain | Docker-backed archive integration-test directory. |
| `tests/emtg_toolchain/integration/test_emtg_archive_integration.py` | Create; retain | `integration`, `docker`, `toolchain`, `ipopt_backend`, and `solver_runtime`-marked archive build, extraction, checksum, and runtime-linkage test. |
| `tests/emtg_toolchain/deployment/` | Create; retain | Deployment-gate test directory. |
| `tests/emtg_toolchain/deployment/test_emtg_archive_tutorials.py` | Create; retain | `tutorials`, `docker`, `ipopt_backend`, and `solver_runtime`-marked extracted-archive execution and complete 17-case tutorial verification gate. |

The following existing repository resources are updated only where required:

| Resource | Update |
| --- | --- |
| [`src/CMakeLists.txt`](../../../src/CMakeLists.txt) | Add a narrow, prefix-respecting install/staging destination for `EMTGv9`; preserve ordinary source-tree builds. |
| [`tests/integration/_docker_support.py`](../../../tests/integration/_docker_support.py) | Add reusable helpers for package-image invocation and clean-runtime containers; preserve the existing Docker image/volume behavior for current tests. |
| [`tests/conftest.py`](../../../tests/conftest.py) | No change planned: existing `--unit`, `--integration`, `--tutorials`, and `--clean-bootstrap` selection logic covers the new tests. |
| [`pytest.ini`](../../../pytest.ini) | No change planned: every required marker is already registered. |
| [`ipopt.readme.md`](ipopt.readme.md) and [`tests.readme.md`](docs/3_NLP_Solvers/IPOPT/tests.readme.md) | Add packaging, resource-cleanup, and exact test-command documentation. |

No PyEMTG source, tutorial source/options, committed universe/hardware input,
immutable tutorial references, or existing Testatron policy/reference files are
modified by this work.

### Ephemeral and output resources

| Resource | Created by | Retained or destroyed |
| --- | --- | --- |
| Package staging directory | `emtg-toolchain package`, as a uniquely named sibling of the requested output | Destroyed after success or failure. It is never extracted into the repository. |
| Package archive and checksum | `emtg-toolchain package` at the caller-provided `--output` path | Retained only after every package gate passes: `<output>` and `<output>.sha256`. A failed invocation leaves neither newly created file. |
| Existing source-builder Docker image | Existing IPOPT test infrastructure, content-addressed as `emtg-pytest-toolchain:<hash>` | Reused only to compile the source checkout and produce the archive. Source-builder bootstrap hardening is explicitly out of scope for this plan. |
| Clean archive-runtime Docker image | Deployment test, built from the pinned Bookworm runtime base, generated runtime package list, and completed archive | Built without reusable build layers under a unique per-archive tag. Destroyed after the deployment gate completes; it is test evidence, not a published EMTG image. |
| Hot package build volume | Default package command, content-addressed by source fingerprint, CMake configuration, and builder-image identity | Retained and reused only when its recorded identity matches. Never shared with existing pytest backend volumes. |
| Cold package build directory | `emtg-toolchain package --cold`, inside the command-owned staging directory | Destroyed after success or failure. It has no persistent CMake objects or generated build state. |
| Disposable Docker containers | Package, integration, and deployment tests | Run with `--rm`; the helper also targets only its exact generated container name if cleanup after interruption is needed. |
| Test artifact directory | `EMTG_TEST_ARTIFACT_DIR`, when supplied | Retained for review and contains logs, archive-test outputs, tutorial comparisons, and verification evidence. Without the variable, pytest temporary artifacts are discarded by pytest. |
| Tutorial test run directories | Archive tutorial test | Created beneath the configured artifact directory, one isolated directory per tutorial case/stage; retained only with configured artifacts, otherwise discarded with pytest temporary files. |

No command deletes an existing user archive, repository source file, Docker
image/volume not named by the toolchain, or external kernel mount. Cleanup is
limited to the command-owned staging directory, uniquely named package volume,
disposable container, and the clean archive-runtime image.

## Archive Build Paths

This plan defines archive-build cache behavior only. Full cold bootstrap of the
source-builder Docker image remains a separate concern and is not changed here.
Both paths use the existing pinned source-builder image and always create a
new archive plus a new clean archive-runtime image for validation.

### Cold archive build

```bash
python -m emtg_toolchain package --cold \
  --emtg-repo "$PWD" \
  --output "$PWD/test-artifacts/emtg-ipopt.tar.gz"
```

The cold path uses a command-owned temporary CMake build directory. It runs
CMake configure and compiles `EMTGv9` without reusing compiled objects or a
package build volume. Use it for release candidates, after CMake/build-policy
changes, and whenever cache-independent compilation evidence is required.

### Hot archive build

```bash
python -m emtg_toolchain package \
  --emtg-repo "$PWD" \
  --output "$PWD/test-artifacts/emtg-ipopt.tar.gz"
```

The default hot path uses a persistent named CMake build volume. Its identity
contains the source-tree content fingerprint, the canonical builder-image
identity, target platform, IPOPT solver configuration, and CMake dependency
configuration. Every hot invocation re-runs CMake configure and the build;
unchanged sources make the native build a no-op or incremental rebuild.

Before reuse, the tool verifies the recorded cache identity. A mismatch causes
creation of a separate cache volume; it never reuses a volume for a different
source/configuration identity. The hot path is for fast iteration, not a
replacement for a cache-free release build.

## Test Workflow and Pytest Selectors

The test layers are deliberately separate. Category selectors in
[`tests/conftest.py`](../../../tests/conftest.py) are mutually exclusive: do
not combine `--unit`, `--integration`, `--regression`, `--clean-bootstrap`,
or `--tutorials` in one command.

| Layer               | Command                                                                                                                               | What it proves                                                                                                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Unit                | `python -m pytest tests/emtg_toolchain/unit --unit -q`                                                                                | CLI validation, manifest rendering, tar safety, payload layout, file modes, checksums, linkage-to-package mapping, and cleanup behavior without Docker.                                   |
| Archive integration | `EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive" python -m pytest tests/emtg_toolchain/integration --integration -q`        | Canonical amd64 builder, IPOPT binary build, archive creation, checksum validation, clean extraction, and declared runtime linkage.                                                       |
| Deployment gate     | `EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/emtg-archive-tutorials" python -m pytest tests/emtg_toolchain/deployment --tutorials -q` | Cold-bootstraps a clean Bookworm runtime image from the archive and declared packages, then verifies the extracted archive binary against every required stage for all 17 tutorial cases. |

The normal deployment approval workflow is:

1. Run the unit command.
2. Run the archive-integration command.
3. Run the deployment-gate command.
4. Publish the archive only when all three commands succeed and the tutorial
   verification report records all 17 cases and all required stages as
   accepted.

The archive integration and deployment-gate commands use separate
`EMTG_TEST_ARTIFACT_DIR` values so one test layer cannot overwrite the other
layer's evidence. The deployment-gate test records the package archive
checksum, EMTG commit SHA, tutorial verification-reference checksum, per-case
logs, comparisons, generated outputs, and final verification report.

## Implementation Steps

### 1. Define one packaging command

1. Add the package CLI in [`emtg_toolchain/`](../../../emtg_toolchain). Its
   minimum command is:

   ```text
   emtg-toolchain package --emtg-repo PATH --output ARCHIVE.tar.gz
   ```

2. Resolve `--emtg-repo` to an absolute EMTG checkout and validate that the
   expected Dockerfile, CMake files, CSPICE archive, `Universe/`, and
   `HardwareModels/` inputs exist.
3. Reject a missing `--output`, a non-`.tar.gz` output, or an existing output
   unless a deliberate future overwrite option is added.
4. Ensure errors from Docker, CMake, staging, archive generation, checksum
   generation, or smoke testing cause a nonzero exit and do not leave a new
   output archive/checksum pair behind.

**Acceptance:** invoking the command with invalid repository or output inputs
fails clearly before publishing artifacts.

### 2. Build IPOPT EMTG in the canonical Docker toolchain

1. Reuse [`tests/docker/Dockerfile.toolchain`](../../../tests/docker/Dockerfile.toolchain)
   and build it with `--platform linux/amd64`.
2. Preserve the existing CSPICE SHA-256 verification and static CSPICE build;
   do not add a release-specific Dockerfile.
3. Configure CMake with `EMTG_NLP_SOLVER=IPOPT` and the same dependency paths
   currently used by the Docker integration fixtures.
4. Build `EMTGv9` in a clean packaging build directory.
5. If necessary, add a narrow CMake install/staging rule that copies the
   resulting executable to `bin/EMTGv9` without changing normal developer
   source-tree build behavior.
6. Run `ldd` on the staged binary. Fail when a dependency is unresolved, when
   a SNOPT library is present, or when a CSPICE shared library is present.

**Acceptance:** the staged binary is executable, links to IPOPT, has no
unresolved libraries, has no SNOPT dependency, and uses the bundled static
CSPICE library rather than a CSPICE shared object.

### 3. Derive and write the runtime dependency manifest

1. Capture the final `ldd` result from the staged executable.
2. Maintain a reviewed mapping from the observed Bookworm library set to
   runtime Debian package names. At minimum, account for IPOPT, GSL, Boost
   filesystem/system/serialization, OpenMP, the GNU Fortran runtime, and
   `csh` when they are required by the verified binary/runtime behavior.
3. Write `RUNTIME_REQUIREMENTS.txt` into the archive. It must include:
   - target platform: `linux/amd64`;
   - base OS: Debian 12 Bookworm;
   - `apt` package names the third-party deployment environment must install;
   - the exact `ldd` output used to derive the list;
   - a statement that the archive does not include mission-specific SPICE SPK
     kernels; and
   - the EMTG commit SHA and build timestamp for basic traceability.
4. Add a test that compares the declared dependency package list with the
   verified linkage fixture so a library change cannot silently make the
   manifest stale.

**Acceptance:** the third-party deployment environment can install the
declared package names in a clean Bookworm image and resolve every dependency
reported by `ldd`.

### 4. Stage the minimal runtime archive payload

1. Stage a single archive root named `emtg/`, with this layout:

   ```text
   emtg/
   ├── bin/
   │   └── EMTGv9
   ├── universe/
   │   ├── *.emtg_universe
   │   └── ephemeris_data/
   │       ├── naif0012.tls
   │       └── pck00010.tpc
   ├── hardware/
   │   └── ... required public runtime hardware assets ...
   ├── RUNTIME_REQUIREMENTS.txt
   └── README.md
   ```

   The versioned archive filename identifies the package variant and release;
   it must not add another extracted directory level. Extracting the archive
   into `/opt/toolkit` must produce `/opt/toolkit/emtg/bin/EMTGv9`.

2. Use an explicit source-to-destination manifest:
   - Include committed `Universe/*.emtg_universe`.
   - Include only `naif0012.tls` and `pck00010.tpc` from
     `Universe/ephemeris_files/`.
   - Create and review a mapping of the standard distributable files in
     `HardwareModels/` into `hardware/`. Preserve names expected by options
     files; do not rename assets during extraction.
   - Include no planetary ephemerides or mission SPK kernels.
3. Exclude source code, PyEMTG, GUI modules, tests, `.git`, CMake build
   directories, generated mission results, proprietary solvers, and
   development-only assets.
4. Preserve the executable mode on `bin/EMTGv9`.
5. Build the archive using only normalized, relative tar member names. Reject
   absolute paths and traversal entries before writing, then reopen the final
   archive and verify the same condition and the single `emtg/` root.

**Acceptance:** the archive contains the listed runtime payload only, has one
root directory, no unsafe member names, and an executable `bin/EMTGv9`.

### 5. Add minimal runtime documentation

1. Write the archive `README.md` to state:
   - the required Debian runtime packages and `RUNTIME_REQUIREMENTS.txt`;
   - extraction into `/opt/toolkit`, resulting in
     `/opt/toolkit/emtg/bin/EMTGv9`;
   - the fixed EMTG invocation form and the fact that no shell is required;
   - the working-directory behavior expected by EMTG;
   - which universe/hardware inputs are bundled;
   - which external kernels and mission data the third-party deployment
     environment must supply; and
   - that outputs belong in its isolated writable run directory.
2. Update [`ipopt.readme.md`](ipopt.readme.md) with the package command,
   archive output, checksum verification, and clean-runtime smoke-test
   command.
3. Update [`tests.readme.md`](docs/3_NLP_Solvers/IPOPT/tests.readme.md) with the focused archive test
   and clean-Bookworm runtime test. Do not make full-corpus Testatron
   baselining part of the package command's required gates.

**Acceptance:** an engineer can build a third-party deployment image that
extracts the archive, installs the declared packages, supplies its mission
inputs, and runs the fixed executable without reading EMTG source code.

### 6. Generate checksum and publish the completed archive

1. Build the archive in a temporary directory adjacent to the requested output
   path.
2. Generate `<archive>.sha256` in standard `sha256sum -c` format, naming the
   archive's basename.
3. Verify the checksum before moving either file to the requested location.
4. Move the archive and checksum only after all build, staging, archive, and
   smoke-test gates pass.
5. Do not implement compatibility aliases or a mutable release channel in this
   phase.

**Acceptance:** from the artifact directory, this succeeds:

```bash
sha256sum -c emtg-ipopt-<version>.tar.gz.sha256
```

### 7. Verify with focused tests

1. Add non-Docker tests for:
   - output-name validation;
   - runtime manifest rendering;
   - archive member safety;
   - required-layout and forbidden-content checks;
   - executable-mode preservation; and
   - checksum file format.
2. Add a Docker-backed archive test that:
   - packages an IPOPT `EMTGv9`;
   - extracts the resulting archive into an empty location;
   - verifies its checksum;
   - inspects `ldd` after installing only the declared runtime packages; and
   - confirms no unresolved, SNOPT, or CSPICE shared-library linkage.
3. Use the complete 17-case tutorial corpus as the reproducible clean-runtime
   deployment test:
   - generate a temporary Dockerfile from the pinned
     `python:3.12-slim-bookworm` base image;
   - build a unique archive-runtime image with `--no-cache --platform
     linux/amd64`, installing only the runtime packages declared by the
     completed archive and extracting that archive to `/opt/toolkit`;
   - assert the image contains no source checkout, CMake, compiler, build
     volume, or source-builder `/opt/emtg-deps` directory;
   - provide the repository's existing tutorial options, expected references,
     and required external kernels as test-only mounted inputs, not as archive
     payload;
   - start a fresh `--rm` container from the clean archive-runtime image for
     each tutorial stage and run the extracted fixed `EMTGv9` executable with
     an argument list and isolated writable run directory;
   - retain per-case logs, generated artifacts, comparisons, and provenance;
   - run the existing tutorial-baselining verification workflow against its
     reviewed reference, recording the EMTG commit SHA and checksum of that
     reference with the deployment evidence; and
   - require every one of the 17 registered tutorial cases to pass
     verification. A missing, skipped, timed-out, failed, or mismatched case
     blocks deployment approval.
4. Preserve the existing tutorial verification semantics: where the current
   corpus has replay and refinement stages, every required stage for each of
   the 17 cases must be accepted by the reviewed verification reference. The
   deployment gate is not satisfied merely because `EMTGv9` exits zero or
   writes an `.emtg` file.
5. Reuse the existing IPOPT mission preparation, tutorial-baselining, and
   Docker test utilities where practical. Adapt them to invoke the extracted
   archive binary in the clean archive-runtime image rather than a binary in
   the source build directory. The broader Testatron corpus remains useful
   repository validation but is not a packaging-release prerequisite.

**Acceptance:** the archive runs without compilers, CMake, source checkout,
PyEMTG, or GUI dependencies in the deployment image, and the complete
17-case tutorial verification report is accepted before a deployment is
greenlit.

### 8. Baseline the release archive and document third-party handoff

1. Add a release-baselining path that accepts an existing versioned archive,
   rather than calling `package` to create a substitute test archive.
2. Verify the supplied archive checksum, read its
   `RUNTIME_REQUIREMENTS.txt`, build the clean runtime image from that exact
   archive, and run the complete 17-case deployment tutorial gate.
3. Retain release evidence that records the archive filename and SHA-256,
   source commit SHA, cold build mode, runtime-requirements checksum, tutorial
   verification-reference checksum, final `verification.json`, and the
   evidence-directory location.
4. Require the same deployment acceptance criteria: 17 cases, 33 stages,
   repeatable attempts, and every stage marked `matched`.
5. Document the third-party deployment-environment handoff:
   - versioned archive filename and accompanying SHA-256 checksum;
   - checksum verification;
   - extraction into `/opt/toolkit`, yielding
     `/opt/toolkit/emtg/bin/EMTGv9`;
   - installation of the declared runtime packages;
   - the runtime package manifest;
   - the release-baseline command and required accepted
     `verification.json`; and
   - ownership of container construction, API behavior, request validation,
     process control, logs, output retention, and cleanup.

**Acceptance:** the exact versioned archive delivered to a third-party
deployment environment has a retained, accepted, cold release-baseline record;
the handoff documentation enables independent checksum, extraction, and
runtime-package verification.

## Completion Criteria

This first integration milestone is complete when:

1. A versioned `.tar.gz` archive contains IPOPT-enabled `EMTGv9`, required
   public runtime universe/hardware assets, `RUNTIME_REQUIREMENTS.txt`, and
   usage documentation.
2. A corresponding SHA-256 file verifies the archive successfully.
3. The dependency list is derived from the packaged binary's actual linkage.
4. A clean Debian 12 runtime container installs the declared packages,
   extracts the archive, and passes verification for all 17 registered
   tutorial cases using the extracted executable and separately supplied
   test-only tutorial inputs/kernels.
5. Missing, skipped, timed-out, failed, or mismatched tutorial verification
   blocks deployment approval.
6. Documentation explicitly states that the third-party deployment environment
   owns FastAPI request handling, process execution, timeout/error/log
   behavior, path validation, artifact management, and all future structured
   `.emtg` result handling.
7. Phase 8 release baselining verifies the exact versioned archive intended
   for handoff, not a newly generated substitute archive.
