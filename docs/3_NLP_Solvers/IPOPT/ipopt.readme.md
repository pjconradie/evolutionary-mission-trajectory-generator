# IPOPT Docker Toolchain

EMTG's supported open-source IPOPT verification environment is a pinned Docker
toolchain. It provides the Linux dependencies required to configure, compile,
and execute the IPOPT backend without installing those dependencies on the
host. The Docker workflow is used by the IPOPT integration and tutorial tests;
it is not required for an independently configured native EMTG build.

Run the commands below from the repository root.

## Why Docker Is Used

The IPOPT backend must be tested with a coordinated C++ toolchain, CSPICE,
Boost, GSL, BLAS/LAPACK, and IPOPT. Docker makes that environment repeatable:

- The image pins Debian 12, Python 3.12, and the system build dependencies,
   including IPOPT 3.11.9.
- CSPICE is rebuilt from the repository's pinned archive and verified by
   SHA-256 during the image build.
- Host-installed packages, compiler versions, and any proprietary SNOPT
   installation cannot accidentally change the IPOPT verification environment.
- The same `linux/amd64` environment runs on Linux and on macOS through Docker
   Desktop. Apple Silicon hosts use amd64 emulation, which is correct but slower
   than native amd64 execution.
- CI, integration tests, and tutorial verification start from the same
   dependency contract and can retain their logs as artifacts.

Docker proves the portable IPOPT build and runtime path. It does not change
EMTG's mission equations or replace the option-controlled solver selection in
an `.emtgopt` file.

## Resource Model

The workflow creates three different Docker resource types. They have distinct
lifetimes and should be cleaned up deliberately.

| Resource | Name or label | Lifetime | Purpose |
| --- | --- | --- | --- |
| Toolchain image | `emtg-pytest-toolchain:<hash>` | Reused until explicitly removed | Debian amd64 compiler and IPOPT dependencies |
| Run container | Label `org.emtg.pytest.container=true` | Disposable | Executes one test, probe, or manual EMTG command |
| Build volume | `emtg-pytest-ipopt-<hash>` | Reused until explicitly removed | CMake build tree and compiled `EMTGv9` |

The image tag is content-addressed. EMTG calculates it from the bytes of
`tests/docker/Dockerfile.toolchain` and the pinned CSPICE SHA-256. Changing
either input produces a different tag and therefore a fresh image/build cache.

Supported test runs mount:

| Container path | Host source | Access | Purpose |
| --- | --- | --- | --- |
| `/repo` | Repository root | Read-only | Source, tests, and immutable inputs |
| `/build` | Named Docker volume | Read-write | Reusable CMake build tree |
| `/artifacts` | Optional host directory | Read-write | Logs and retained test artifacts |

Containers use `--rm`, so an ordinary completed run leaves no container
behind. The named build volume remains intentionally; it makes later IPOPT
runs much faster.

## Prerequisites and Inspection

Install Docker Desktop on macOS or the Docker Engine on Linux, start its daemon,
and confirm that the client can reach it:

```bash
docker info --format 'Server={{.ServerVersion}} Architecture={{.Architecture}} CPUs={{.NCPU}}'
```

Inspect EMTG-managed images and build volumes:

```bash
docker image ls --filter label=org.emtg.pytest.toolchain=true \
   --format 'IMAGE={{.Repository}}:{{.Tag}} ID={{.ID}} SIZE={{.Size}} CREATED={{.CreatedSince}}'
docker volume ls --filter label=org.emtg.pytest.toolchain=true
```

The first toolchain build may download approximately 150-300 MB when its base
image is already cached and can need 3-5 GB of temporary free disk space. On a
four-core ARM64 host using amd64 emulation, an observed `pytest --integration`
run took about ten minutes; this is a historical measurement, not a guarantee.

## Recommended Build: Pytest Provisions the Image

The supported route is to let the integration fixtures create the image only
when its content-addressed tag is absent. This focused command builds the
toolchain if necessary, configures the IPOPT backend in its reusable build
volume, and runs a direct NLP mission:

```bash
python -m pytest \
   tests/integration/test_ipopt_backend.py::test_ipopt_runs_direct_nlp_mission \
   --integration -q
```

The cold run includes an image build and CMake compilation. A warm run reuses
both the image and `emtg-pytest-ipopt-<hash>` volume.

To retain Docker probe logs outside pytest's temporary directory, set an
artifact directory before running one focused stage:

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/test-artifacts/ipopt-direct-nlp" \
python -m pytest \
   tests/integration/test_ipopt_backend.py::test_ipopt_runs_direct_nlp_mission \
   --integration -q
```

Do not point multiple benchmark stages at the same artifact directory: they
write common names such as `run.log`, `result.json`, and `comparison.json`.

## Manual Image Build

The pytest fixture builds from a temporary context containing exactly the
Dockerfile and CSPICE archive. Reproduce that process manually when diagnosing
an image build:

```bash
context_dir="$(mktemp -d)"
cp tests/docker/Dockerfile.toolchain "$context_dir/Dockerfile"
cp depend/cspice-c_pc_linux_gcc_64bit/cspice.tar.Z "$context_dir/cspice.tar.Z"

cspice_sha256=60a95b51a6472f1afe7e40d77ebdee43c12bb5b8823676ccc74692ddfede06ce
tag="$(python -c 'import hashlib, pathlib, sys; digest = hashlib.sha256(); digest.update(pathlib.Path(sys.argv[1]).read_bytes()); digest.update(sys.argv[2].encode("ascii")); print("emtg-pytest-toolchain:" + digest.hexdigest()[:16])' tests/docker/Dockerfile.toolchain "$cspice_sha256")"

docker build --platform linux/amd64 \
   --label org.emtg.pytest.toolchain=true \
   --build-arg CSPICE_SHA256="$cspice_sha256" \
   --tag "$tag" \
   "$context_dir"

rm -rf "$context_dir"
```

The checksum is verified inside the Dockerfile before CSPICE is built. Keep the
temporary context out of version control and remove it after the build.

For an intentionally uncached bootstrap check, use `--no-cache` and a distinct
tag. The test suite already owns this workflow:

```bash
python -m pytest --clean-bootstrap -vv
```

That test removes its unique uncached image and build volume when it finishes;
it does not populate the reusable IPOPT cache.

## Running a Container

Use an interactive shell to inspect an image without changing the repository:

```bash
docker run --rm --platform linux/amd64 \
   -v "$PWD:/repo:ro" \
   "$tag" sh
```

To run the already compiled EMTG binary, attach the backend-specific build
volume. The following example follows the Coast diagnostic mount model. Replace
the image and volume names with values shown by the inspection commands above:

```bash
image=emtg-pytest-toolchain:309abb32ff087c0b
build_volume=emtg-pytest-ipopt-309abb32ff087c0b
case_dir=testatron/ipopt/diagnostics/CoastPhase_Atlas_V_401

docker run --rm --platform linux/amd64 \
   -w "/repo/$case_dir" \
   -v "$PWD:/repo:ro" \
   -v "$build_volume:/build" \
   -v "$PWD/testatron/ipopt:/repo/testatron/ipopt:rw" \
   "$image" \
   /build/src/EMTGv9 \
   "/repo/$case_dir/CoastPhase_Atlas_V_401.emtgopt"
```

The broad `/repo` mount remains read-only. The narrower writable mount permits
diagnostic output beneath `testatron/ipopt`; use a separate host directory for
any unreviewed experiment. The exact Coast preparation steps are in
[`testatron/ipopt/manual_testron_execution.README.md`](../../../testatron/ipopt/manual_testron_execution.README.md).

## Cleanup and Destruction

Normal runs remove their container automatically. Inspect stopped or running
EMTG-labelled containers only if a command was interrupted:

```bash
docker ps -a --filter label=org.emtg.pytest.container=true
```

Remove one known container, if it still exists:

```bash
docker rm -f <container-name>
```

Remove one toolchain image by its full tag:

```bash
docker image rm --force emtg-pytest-toolchain:<hash>
```

Remove one backend build cache volume:

```bash
docker volume rm --force emtg-pytest-ipopt-<hash>
```

Removing an image does not remove its build volume. Removing a build volume
does not remove its image, but the next IPOPT test using that tag must rerun
CMake and recompile EMTG. Delete only names you have inspected. Avoid broad
commands such as `docker system prune` for this workflow because they can
remove unrelated local Docker resources.

## Related Verification Documentation

The Docker fixture implementation is
[`tests/integration/_docker_support.py`](../../../tests/integration/_docker_support.py),
and the pinned package list is
[`tests/docker/Dockerfile.toolchain`](../../../tests/docker/Dockerfile.toolchain).
For Testatron acceptance policy, tutorial coverage, and evidence handling, see
[`testatron/ipopt/README.md`](../../../testatron/ipopt/README.md).
