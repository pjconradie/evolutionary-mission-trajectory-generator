# IPOPT Testing and Verification Data

This directory contains unreviewed IPOPT characterization evidence. It does not
contain promoted regression truths. The committed Testatron truths, tutorial
results, and NASA result packages are immutable inputs to these workflows.

Run commands in this guide from the repository root unless stated otherwise.

## Safety Rules

- Keep every generated result explicitly marked `unreviewed`.
- Never use `--update_truths` while generating IPOPT evidence.
- Never overwrite files below `testatron/tests` or tutorial `results`
  directories.
- Do not edit NASA result packages.
- Persist repository-relative POSIX paths only. Host paths, drive-letter paths,
  and container runtime paths must not appear in committed JSON or
  configuration.
- Runtime paths may be absolute inside a disposable process, but they must be
  converted to repository-relative or stage-relative paths before writing
  evidence.
- Use the direct numeric comparison functions in
  `testatron/ipopt_characterization.py`. Do not use Comparatron to generate
  benchmark evidence.
- Stop at the first unexplained failed, infeasible, timed-out, parse-failed,
  dependency-blocked, or topology-changed result.

## Evidence Types

### Pytest verification

Pytest checks code contracts, parsing, immutable references, builds, linking,
and selected mission behavior. Passing pytest does not promote generated data
or make it a Testatron truth.

### Benchmark evidence

`benchmarks/` contains deterministic replay and IPOPT-refinement evidence for:

- `track-acs-prop`
- `osiris-rex-2022`
- `osiris-rex-2024`

Each benchmark has two stages:

- `replay`: evaluate the aligned reference decision vector without IPOPT.
- `ipopt`: refine the aligned reference decision vector with IPOPT.

### Testatron characterization

`cases/`, `manifest.json`, and `manifest.csv` contain incremental IPOPT runs of
Testatron cases. These are characterization results, not replacement truths.

The current general Testatron manifest writer can retain container runtime paths
in fields such as source, output, comparison, and log paths. Such manifests are
not portable commit-ready evidence until the writer converts those fields to
repository-relative or case-relative paths. Benchmark JSON is already guarded
against this problem.

### Diagnostics

`diagnostics/` contains controlled experiments used to understand solver
behavior. Diagnostics are not benchmark results or regression truths.

## Pytest Categories

The custom category selectors are mutually exclusive.

| Command | Purpose | Docker/native build |
| --- | --- | --- |
| `pytest --unit` | Isolated Python and native contract tests | Normally no Docker build |
| `pytest --regression` | Parser and frozen-reference regression checks | No Docker build |
| `pytest --integration` | Reusable Docker, compile, and solver-runtime checks | Yes |
| `pytest --clean-bootstrap` | One uncached toolchain rebuild and validation | Yes, always uncached |

Plain `pytest` runs the unit, regression, and normal integration selections but
excludes clean bootstrap. It can unnecessarily repeat expensive native
integration work after the category commands have already passed.

`pytest --integration` also excludes clean bootstrap. Run clean bootstrap only
through `pytest --clean-bootstrap` or the compatible marker form:

```bash
pytest -m clean_bootstrap tests/integration/test_linux_toolchain.py -vv
```

Confirm selection without running a test:

```bash
pytest --clean-bootstrap --collect-only -q
pytest --integration --collect-only -q
```

Combining category selectors is an error. For example:

```bash
pytest --integration --clean-bootstrap --collect-only
```

### Registered markers

The markers declared in `pytest.ini` are:

| Marker | Meaning |
| --- | --- |
| `unit` | Isolated tests without external services |
| `integration` | External-tool or combined-component tests |
| `regression` | Established EMTG behavior and frozen baselines |
| `docker` | Requires the Docker CLI and daemon |
| `toolchain` | Validates the pinned Linux environment |
| `none_backend` | Builds or tests the solver-neutral backend |
| `ipopt_backend` | Builds or tests the IPOPT backend |
| `compile` | Configures or compiles native targets |
| `solver_runtime` | Executes a native NLP solver |
| `clean_bootstrap` | Rebuilds the toolchain without reusable layers |

Useful focused selections include:

```bash
pytest --integration -m solver_runtime
pytest --integration -m compile
pytest --integration -m "not compile"
pytest --integration --ignore=tests/integration/test_none_backend.py
```

The last command is appropriate only when the NONE backend already passed and
none of its controlling inputs changed. Rerun it when CMake configuration,
native backend code, Docker/toolchain inputs, or the NONE-backend fixtures
change.

Run a single test by node ID:

```bash
pytest tests/integration/test_ipopt_backend.py::test_track_acs_replay_matches_committed_truth -vv
```

## Docker Conditions

Integration tests use a Debian 12 amd64 image, including on ARM64 hosts. The
pinned image installs IPOPT 3.11.9, NumPy 2.5.3, pandas 3.0.5, and the remaining
build dependencies. Docker must be running.

Inspect the host and reusable images with:

```bash
docker info --format 'Server={{.ServerVersion}} Architecture={{.Architecture}} CPUs={{.NCPU}}'
docker image ls --filter label=org.emtg.pytest.toolchain=true \
  --format 'IMAGE={{.Repository}}:{{.Tag}} ID={{.ID}} SIZE={{.Size}} CREATED={{.CreatedSince}}'
```

Normal integration tests use a content-addressed image and persistent,
backend-specific build volumes:

```text
emtg-pytest-ipopt-<image-hash>
emtg-pytest-none-<image-hash>
```

The first build for a backend can be slow. Later tests reuse its volume. The
clean-bootstrap test creates a unique uncached image and volume and removes
those disposable resources when it finishes; it does not warm the reusable
NONE or IPOPT build volumes.

On a four-core ARM64 host using amd64 emulation, observed times on 2026-09-15
were:

| Selection | Result | Duration |
| --- | --- | --- |
| `pytest --unit` | 23 passed | 2.68 s |
| `pytest --regression` | 145 passed | 1.62 s |
| `pytest --integration` | 23 passed | 9 min 55 s |
| `pytest --clean-bootstrap -vv` | 1 passed | 29 min 50 s |

These are historical measurements, not fixed expectations. A clean build may
download roughly 150-300 MB when its base image is cached and may need 3-5 GB
of temporary free disk space.

## Pytest Artifact Directory

Docker probes normally write to pytest's temporary directory. Set
`EMTG_TEST_ARTIFACT_DIR` to retain probe output at a chosen location:

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/path/to/artifacts" \
pytest tests/integration/test_ipopt_backend.py::TEST_NODE_ID -vv
```

All benchmark fixtures write common names such as `result.json`,
`comparison.json`, `provenance.json`, and `run.log`. Therefore, point the
environment variable at exactly one benchmark stage and run one benchmark node
at a time. Reusing one directory for multiple stages causes collisions and
cross-contaminated evidence.

## Regenerate Current Benchmarks

The following is the supported regeneration workflow today. It runs each stage
individually and writes directly to its owned directory.

### TrackACSProp replay

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/benchmarks/track-acs-prop/replay" \
pytest tests/integration/test_ipopt_backend.py::test_track_acs_replay_matches_committed_truth -vv
```

### TrackACSProp IPOPT refinement

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/benchmarks/track-acs-prop/ipopt" \
pytest tests/integration/test_ipopt_backend.py::test_track_acs_ipopt_refinement_retains_seed -vv
```

### OSIRIS-REx 2022 replay

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/benchmarks/osiris-rex/2022/replay" \
pytest tests/integration/test_ipopt_backend.py::test_osiris_2022_replay_matches_nasa_result -vv
```

### OSIRIS-REx 2022 IPOPT refinement

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/benchmarks/osiris-rex/2022/ipopt" \
pytest tests/integration/test_ipopt_backend.py::test_osiris_2022_ipopt_refinement_retains_nasa_seed -vv
```

### OSIRIS-REx 2024 replay

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/benchmarks/osiris-rex/2024/replay" \
pytest tests/integration/test_ipopt_backend.py::test_osiris_2024_replay_matches_nasa_result -vv
```

### OSIRIS-REx 2024 IPOPT refinement

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/benchmarks/osiris-rex/2024/ipopt" \
pytest tests/integration/test_ipopt_backend.py::test_osiris_2024_ipopt_refinement_retains_nasa_seed -vv
```

Run the six commands sequentially. Estimate runtime before execution and stop at
the first failure.

## Review Generated Benchmark Evidence

A stage normally contains:

- Prepared `.emtgopt` input.
- Generated `.emtg` mission.
- `run.log` and a probe log.
- `comparison.json`.
- `compatibility.json`.
- `result.json`.
- `provenance.json`.
- EMTG-generated spacecraft and XF files where applicable.

Review each stage after regeneration:

1. Confirm pytest passed and `result.json` reports `acceptable: true`.
2. Confirm `status` remains `unreviewed`.
3. Confirm the stage and benchmark identifiers match the directory.
4. Confirm source paths identify the intended immutable package.
5. Confirm every source hash in `provenance.json` matches the current source.
6. Inspect feasibility, objective, topology, IPOPT exit, and iteration data.
7. Confirm replay logs do not contain IPOPT iteration output.
8. Confirm refinement logs contain the expected IPOPT diagnostics.
9. Confirm no source options, Testatron truth, tutorial result, or NASA package
   changed.
10. Confirm persisted JSON contains no absolute host or container path.

Run the existing portability and provenance guards with:

```bash
pytest --unit -k 'benchmark or repo_relative or provenance'
```

Inspect source changes afterward:

```bash
git status --short
git diff -- testatron/ipopt/benchmarks
```

Do not promote the generated missions to Testatron truths.

## Generate Testatron Characterization Data

The permanent Testatron characterization mode supports repeated filters and
resume. Run it inside an environment where the IPOPT-enabled executable is
available:

```bash
python testatron/testatron.py \
  --ipopt-characterization \
  --emtg /path/available/only/at/runtime/EMTGv9 \
  --output-root /path/available/only/at/runtime/artifacts \
  --timeout 300 \
  --filter 'transcription_tests/CoastPhase_EMintercept'
```

Filters match paths relative to `testatron/tests` and accept extensionless
identifiers. Repeat `--filter` to form a batch and add `--resume` to reuse
existing `result.json` records:

```bash
python testatron/testatron.py \
  --ipopt-characterization \
  --emtg /path/available/only/at/runtime/EMTGv9 \
  --output-root /path/available/only/at/runtime/artifacts \
  --timeout 300 \
  --filter 'output_options/*' \
  --filter 'solver_options/*' \
  --resume
```

The absolute values above are placeholders for ephemeral runtime paths, not
values to persist in committed configuration or evidence. The current manifest
writer must be hardened before its output is portable commit-ready evidence.

Regenerate a report from existing case results without running EMTG:

```bash
python testatron/testatron.py \
  --ipopt-characterization \
  --output-root /path/available/only/at/runtime/artifacts \
  --report-only
```

Never add `--update_truths` to these commands.

## Add Future Verification Data

Use this process for a new deterministic benchmark, tutorial example, or
Testatron characterization case.

1. Choose a stable, descriptive identifier that does not depend on a temporary
   directory or execution timestamp.
2. Map it explicitly to one repository-relative source `.emtgopt`, one
   repository-relative reference `.emtg`, and an XF description schema when
   required. Do not discover a reference by selecting the latest dated folder.
3. Assign a unique repository-relative output root and unique stage
   directories.
4. Preserve mission semantics. Rewrite only runtime paths, writable output
   locations, solver selection required by the test, and documented legacy
   dependency mappings.
5. Align seeds by ordered decision descriptions. Reject missing, reordered,
   non-finite, out-of-bound, or differently sized vectors.
6. Define acceptance before execution. At minimum, check process success,
   parsing, topology, finite source-tolerance feasibility, and scale-aware
   objective behavior.
7. Generate `result.json`, `comparison.json`, `compatibility.json`, and
   `provenance.json`, plus logs and generated mission data.
8. Store repository-relative paths and SHA-256 hashes for every immutable
   source. Reject paths outside the repository.
9. Add focused unit coverage for mapping, preparation, comparison boundaries,
   provenance, portability, and failure classification.
10. Add one focused integration test for executable behavior. Do not make a
    long all-cases run the first test of a new workflow.
11. Run the focused test, inspect evidence, then widen incrementally.
12. Commit code/tests separately from reviewed generated evidence.

For tutorial workflows, execute every current top-level lesson input. Historical
files below tutorial `results/` are references, not extra lesson inputs. PEATSA
is a separate multi-case workflow and requires its own validation.

For Testatron growth, run deterministic representatives first, then folder
batches with `--resume`, and finally the unfiltered inventory. Stop on every new
non-reviewable classification.

## Roadmap: Registry-Backed Regeneration

The following interface is planned and is **not currently implemented**:

```text
python testatron/ipopt_characterization.py \
  --regenerate-benchmarks \
  [--only BENCHMARK_ID] \
  [--dry-run] \
  --emtg RUNTIME_EXECUTABLE
```

The future command should:

- Validate explicit benchmark and stage mappings.
- Print mappings without writing in dry-run mode.
- Run stages sequentially into unique destinations.
- Fail at the first preparation, process, parsing, or comparison error.
- Share preparation, comparison, and writers with pytest fixtures.
- Write portable provenance and reject absolute persisted paths.
- Leave truths, tutorial/NASA packages, and frozen diagnostic snapshots
  untouched.

Until that command exists and is tested, use the six pytest commands in this
document.

## Maintenance Checklist

Update this guide whenever any of the following changes:

- Pytest category selector or marker.
- Docker image dependency, platform, or cache-volume naming.
- Benchmark registry identity, stage, or reference mapping.
- Generated artifact or provenance schema.
- Tutorial input inventory.
- Testatron inventory, filtering, resume, or classification behavior.

Before committing documentation or evidence:

- Verify current selectors with `pytest --help`.
- Verify expensive selections with `--collect-only` first.
- Verify every documented node ID still exists.
- Verify benchmark source and destination directories exist.
- Run focused portability and provenance tests.
- Search committed JSON for host, drive-letter, and container runtime paths.
- Confirm all generated statuses remain `unreviewed`.
- Confirm immutable references have not changed.
- Record the command, image identity, duration, and result counts used for the
  evidence review.
