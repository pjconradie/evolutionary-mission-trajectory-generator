# EMTG Debian IPOPT Archive Implementation Plan

## Objective

Deliver a versioned, checksummed `linux/amd64` Debian 12 archive that ADSGNC
can unpack into an ADSGNC-built Docker image and execute directly:

```bash
/opt/toolkit/emtg/bin/EMTGv9 /opt/work/<run-id>/request.emtgopt
```

The archive must contain an IPOPT-enabled `EMTGv9` executable and the
runtime EMTG assets that ADSGNC will not mount separately. It must have a
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

### ADSGNC owns

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

ADSGNC direct pass-through means EMTG arguments and inputs only. It must not
accept an arbitrary shell command to run inside the container.

## Explicit Non-Goals for This Phase

- Packaging PyEMTG or making PyEMTG imports headless.
- Adding `PyEMTG/__init__.py`, `PyEMTG/EMTGRunner.py`, or a Python runner API.
- Parsing `.emtg` solutions or defining structured mission/feasibility
  response semantics.
- Implementing path rewriting, request path validation, or run-directory
  confinement in EMTG Python code.
- Implementing ADSGNC FastAPI routes, service lifecycle, mounted-volume
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

## Implementation Steps

### 1. Define one packaging command

1. Add a small repository-owned packaging script or CLI. Its minimum command
   is:

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
   - `apt` package names ADSGNC must install;
   - the exact `ldd` output used to derive the list;
   - a statement that the archive does not include mission-specific SPICE SPK
     kernels; and
   - the EMTG commit SHA and build timestamp for basic traceability.
4. Add a test that compares the declared dependency package list with the
   verified linkage fixture so a library change cannot silently make the
   manifest stale.

**Acceptance:** ADSGNC can install the declared package names in a clean
Bookworm image and resolve every dependency reported by `ldd`.

### 4. Stage the minimal runtime archive payload

1. Stage a single archive root, named from the requested release version, with
   this layout:

   ```text
   emtg-ipopt-<version>/
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
   archive and verify the same condition.

**Acceptance:** the archive contains the listed runtime payload only, has one
root directory, no unsafe member names, and an executable `bin/EMTGv9`.

### 5. Add minimal runtime documentation

1. Write the archive `README.md` to state:
   - the required Debian runtime packages and `RUNTIME_REQUIREMENTS.txt`;
   - extraction under an ADSGNC-selected toolkit root;
   - the fixed EMTG invocation form and the fact that no shell is required;
   - the working-directory behavior expected by EMTG;
   - which universe/hardware inputs are bundled;
   - which external kernels and mission data ADSGNC must supply; and
   - that outputs belong in ADSGNC's isolated writable run directory.
2. Update [`ipopt.readme.md`](ipopt.readme.md) with the package command,
   archive output, checksum verification, and clean-runtime smoke-test
   command.
3. Update [`tests.readme.md`](tests.readme.md) with the focused archive test
   and clean-Bookworm runtime test. Do not make full-corpus Testatron
   baselining part of the package command's required gates.

**Acceptance:** an ADSGNC engineer can build an image that extracts the
archive, installs the declared packages, supplies its mission inputs, and runs
the fixed executable without reading EMTG source code.

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
3. Add one reproducible clean-Bookworm smoke test:
   - use a fresh `python:3.12-slim-bookworm` image;
   - install the declared runtime packages;
   - extract the archive;
   - copy/mount a known mission's required external kernels and options into a
     writable test run directory;
   - run `EMTGv9` directly with an argument list; and
   - assert exit code zero and expected generated output.
4. Reuse the existing IPOPT mission preparation and Docker test utilities
   where practical. The existing broader IPOPT/Testatron tests remain useful
   repository validation but are not packaging-release prerequisites.

**Acceptance:** the packaging command and the clean runtime smoke test prove
that the archive works without compilers, CMake, source checkout, PyEMTG, or
GUI dependencies in the deployment image.

## Completion Criteria

This first integration milestone is complete when:

1. A versioned `.tar.gz` archive contains IPOPT-enabled `EMTGv9`, required
   public runtime universe/hardware assets, `RUNTIME_REQUIREMENTS.txt`, and
   usage documentation.
2. A corresponding SHA-256 file verifies the archive successfully.
3. The dependency list is derived from the packaged binary's actual linkage.
4. A clean Debian 12 runtime container installs the declared packages,
   extracts the archive, and runs a known mission with external mission data
   supplied separately.
5. Documentation explicitly states that ADSGNC owns FastAPI request handling,
   process execution, timeout/error/log behavior, path validation, artifact
   management, and all future structured `.emtg` result handling.
