# EMTG IPOPT Runtime Archive Toolchain

`emtg_toolchain` builds an IPOPT-enabled `EMTGv9` in the repository's pinned
Debian 12 Docker toolchain and packages the executable plus its runtime assets
as a SHA-256-verified `.tar.gz` archive. It is the upstream build-and-package
surface for downstream deployment environments such as ADSGNC; it does not
deploy or operate a service container.

Run all commands from the repository root.

## Prerequisites

- Python 3.12 or a compatible Python environment with the repository test
  dependencies installed.
- Docker CLI and a running Docker daemon.
- A `linux/amd64` Docker runtime. Docker Desktop on Apple Silicon must support
  amd64 emulation.
- A complete EMTG checkout containing the pinned CSPICE archive at
  `depend/cspice-c_pc_linux_gcc_64bit/cspice.tar.Z`.

The builder image is pinned to Debian 12 Bookworm and is constructed from
[`tests/docker/Dockerfile.toolchain`](../tests/docker/Dockerfile.toolchain).
The toolchain verifies the CSPICE archive during the Docker build.

## Package an EMTG Runtime Archive

Create an archive using the reusable, content-addressed CMake build cache:

```bash
python3 -m emtg_toolchain package \
  --emtg-repo . \
  --output /absolute/path/emtg_debian_902_20261021.tar.gz
```

The output must end in `.tar.gz`, must use a concrete release filename, and
must not already exist. The command also writes:

```text
emtg_debian_902_20261021.tar.gz.sha256
```

Verify the archive before extracting it:

```bash
cd /absolute/path
sha256sum -c emtg_debian_902_20261021.tar.gz.sha256
```

The command performs these steps:

1. Builds the pinned Docker toolchain image if it is absent locally.
2. Compiles `EMTGv9` with `EMTG_NLP_SOLVER=IPOPT`.
3. Validates the executable's dynamic linkage and rejects unresolved
   libraries, SNOPT, a dynamic CSPICE library, and builder-prefix linkage.
4. Stages the allowlisted runtime payload.
5. Creates, validates, and checksums the archive before publishing it.

Intermediate build and staging files are created below the output directory
and are removed after packaging completes.

### Cold package build

Use `--cold` to compile without the reusable package CMake build cache:

```bash
python3 -m emtg_toolchain package \
  --emtg-repo . \
  --output /absolute/path/emtg_debian_902_20261021_cold.tar.gz \
  --cold
```

Use a cold archive for release-baseline evidence. It is slower than the
default hot build because it configures and compiles in a fresh container build
directory.

## Archive Contents

The archive has a single `emtg/` top-level directory:

```text
emtg/
├── bin/EMTGv9
├── universe/
│   ├── *.emtg_universe
│   └── ephemeris_data/
│       ├── naif0012.tls
│       └── pck00010.tpc
├── hardware/
│   └── <standard HardwareModels files>
├── README.md
└── RUNTIME_REQUIREMENTS.txt
```

`EMTGv9` is executable. The archive intentionally excludes source code, build
trees, tests, mission-specific inputs, and SPICE SPK kernels. A deployment
must supply its own mission inputs and SPK kernels and use an isolated writable
directory for generated results.

After extraction under `/opt/toolkit`, the executable is:

```text
/opt/toolkit/emtg/bin/EMTGv9
```

Run it without a shell:

```bash
/opt/toolkit/emtg/bin/EMTGv9 /opt/work/request.emtgopt
```

## Runtime Dependencies

Read `emtg/RUNTIME_REQUIREMENTS.txt` from the verified archive before building
a deployment image. It records the source commit, build mode, build time,
required Debian packages, and the validated `ldd` output.

The current runtime package contract is:

```text
coinor-libipopt1v5
libgsl27
libboost-filesystem1.74.0
libboost-system1.74.0
libboost-serialization1.74.0
libgomp1
libgfortran5
csh
```

The downstream image must use Debian 12 Bookworm-compatible package sources.
No compiler, CMake, or source build is required at runtime. CSPICE is
statically linked into `EMTGv9`; no CSPICE shared library is needed.

## Testing

Collect the toolchain tests without running them:

```bash
python3 -m pytest tests/emtg_toolchain --collect-only -q
```

Run the isolated unit suite:

```bash
python3 -m pytest tests/emtg_toolchain/unit -m unit -q
```

Run the Docker-backed integration suite:

```bash
python3 -m pytest tests/emtg_toolchain/integration -m "integration and docker" -q
```

Run the archive tutorial/deployment checks:

```bash
python3 -m pytest tests/emtg_toolchain/deployment -m tutorials -q
```

The deployment and integration suites can build Docker images, compile EMTG,
and execute tutorial cases. They are intentionally slower than unit tests.

## Current Command Surface

The implemented CLI currently exposes:

```text
python3 -m emtg_toolchain package --emtg-repo PATH --output ARCHIVE.tar.gz [--cold]
```

Future `build`, `run`, and `shell` commands described in broader deployment
planning are not implemented by this module yet and must not be relied upon
until they are added and documented here.
