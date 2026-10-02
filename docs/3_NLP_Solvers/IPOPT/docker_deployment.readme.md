# Debian IPOPT Docker Deployment Plan

## Purpose

Separate Docker image and container lifecycle implementation from EMTG while
retaining the Debian IPOPT verification recipe inside this repository. EMTG is
the single canonical source of truth for the Dockerfile, its pinned dependency
contract, and the inputs required to reproduce the IPOPT verification
environment.

A secondary toolchain repository owns reusable local Docker build and run
tooling. It consumes a caller-provided EMTG checkout, builds a local image from
the recipe found there, and runs EMTG commands in disposable containers. No
container registry, image publishing workflow, Docker submodule, or mirrored
Dockerfile is required.

Run commands in this document from the EMTG repository root unless stated
otherwise.

## Ownership Boundary

| Responsibility | EMTG repository | Secondary toolchain repository |
| --- | --- | --- |
| Dockerfile and image build context | Canonical owner | Reads from supplied EMTG checkout |
| Dependency and version pins | Canonical owner | Validates and uses them |
| CSPICE archive and checksum contract | Canonical owner | Validates before build |
| Local image build | Declares required image identity | Owns Docker invocation and cache behavior |
| Container execution | Declares test and mission requirements | Owns mount construction, names, locks, and cleanup |
| IPOPT test assertions | Canonical owner | Does not define assertions |
| Image registry and publishing | Not used | Not used |

The secondary repository must not carry a copied Dockerfile or dependency
manifest. The EMTG checkout passed to it determines the exact image recipe.

## Target Layout

Move the current test-only recipe surface into an EMTG top-level toolchain
surface. The final names may vary, but the boundary must be explicit:

```text
evolutionary-mission-trajectory-generator/
  toolchain/
	 Dockerfile.ipopt-debian
	 recipe.toml
	 README.md
  depend/
	 cspice-c_pc_linux_gcc_64bit/
		cspice.tar.Z
  tests/
	 integration/
		_docker_support.py
```

`toolchain/recipe.toml` is the machine-readable contract for all image-affecting
inputs. It records at least:

- Docker platform: `linux/amd64`.
- Debian base-image reference by digest.
- IPOPT package and required version.
- CSPICE archive path and SHA-256.
- The Dockerfile path.
- The expected dependency prefixes used by CMake inside the container.

The Dockerfile remains available in an EMTG checkout, which preserves the
ability to inspect and reproduce the image used by IPOPT verification.

## Secondary Runner Contract

The secondary repository provides a command-line interface with no copied EMTG
recipe. Its minimal interface is:

```bash
emtg-toolchain build --emtg-repo /path/to/evolutionary-mission-trajectory-generator
emtg-toolchain run --emtg-repo /path/to/evolutionary-mission-trajectory-generator -- <command> [arguments...]
emtg-toolchain shell --emtg-repo /path/to/evolutionary-mission-trajectory-generator
```

`build` must:

1. Locate the canonical Dockerfile and recipe manifest in the supplied EMTG
	checkout.
2. Verify every required input exists, including the CSPICE archive.
3. Verify the pinned CSPICE SHA-256 before Docker begins.
4. Compute a deterministic local image identity from the recipe manifest,
	Dockerfile bytes, and declared content hashes.
5. Build only when that image identity is absent locally.

`run` and `shell` must use the image produced by `build` and retain these
container rules:

| Container path | Mount | Access |
| --- | --- | --- |
| `/repo` | Supplied EMTG repository | Read-only |
| `/build` | Backend- and recipe-identity-specific named volume | Read-write |
| `/artifacts` or `/mission` | Caller-selected host directory | Read-write |

All runs use `--platform linux/amd64` and disposable `--rm` containers. The
runner owns container names, volume locks, targeted cleanup, and host-platform
handling. It must report structured errors when the recipe is missing, invalid,
or checksum-mismatched.

## EMTG Integration Changes

### Recipe relocation

1. Move `tests/docker/Dockerfile.toolchain` to the canonical `toolchain/`
	location without changing its dependency contents initially.
2. Add `toolchain/recipe.toml` and `toolchain/README.md`.
3. Preserve the CSPICE archive in `depend/`; record its exact path and SHA-256
	in the recipe manifest.
4. Update all repository documentation and tests to use the canonical path.

### Test client adapter

Replace direct Docker lifecycle implementation in
`tests/integration/_docker_support.py` with a thin secondary-runner client.
The adapter retains EMTG-specific behavior:

- Docker availability diagnostics exposed to pytest.
- `EMTG_TEST_ARTIFACT_DIR` support.
- Probe scripts and `EMTG_CHECK` output parsing.
- Test timeouts and artifact collection.
- Backend-specific cache selection.

The adapter must no longer construct `docker build` or `docker run` commands,
copy Docker build contexts, calculate Docker tags independently, or delete
toolchain-owned resources directly.

Keep existing pytest fixture names where practical so
`tests/integration/conftest.py` and focused test modules remain behaviorally
stable during migration.

### Mission-runner adoption

Refactor `docs/2_Missions/osiris-rex/src/run_mission.py` to use the same
secondary-runner interface. Preserve its mission-specific writable `/mission`
mount, result paths, and CMake configuration, but remove its independent image
selection, Docker Desktop startup, and volume-lifecycle implementation.

### CMake boundary

Do not couple CMake to the secondary repository. EMTG CMake continues to
discover IPOPT through `pkg-config`; the local container merely provides the
pinned Debian dependency environment. EMTG source must not require the path of
the secondary repository.

## Migration Sequence

1. Capture the current integration probe results, image identity, volume names,
	and cold/warm runtimes as migration evidence.
2. Add the canonical `toolchain/` recipe surface in EMTG and make the current
	direct-Docker implementation consume it without changing behavior.
3. Implement the secondary runner against a real EMTG checkout. Verify it
	rejects missing Dockerfile, missing CSPICE archive, invalid manifest, and
	checksum mismatch before calling Docker.
4. Add a runner client to `_docker_support.py` behind a temporary migration
	switch. Compare its output to the current direct-Docker path.
5. Migrate platform, dependency, CMake-policy, IPOPT-adapter, and direct-NLP
	probes in that order.
6. Migrate OSIRIS and a representative Testatron execution.
7. Remove the temporary direct-Docker implementation only after parity checks
	pass. Do not retain two long-lived lifecycle implementations.

## Verification

The migration is complete only when all of the following hold:

1. The secondary runner and EMTG test adapter compute the same image identity
	from the same EMTG checkout.
2. An incomplete or checksum-mismatched canonical recipe fails before Docker
	execution with a precise error.
3. Cold and warm runs pass the current Debian platform, dependency, CMake
	policy, IPOPT adapter, and direct-NLP integration probes.
4. Containers retain a read-only `/repo` mount, scoped writable artifacts or
	mission mount, `linux/amd64` platform pinning, and persistent backend-scoped
	build volumes.
5. OSIRIS and representative Testatron workflows retain their pre-migration
	behavior when launched by the secondary runner.
6. EMTG contains the canonical recipe and tests, but not duplicated Docker
	image/container lifecycle implementation. The secondary repository contains
	lifecycle implementation but no copied EMTG recipe.

## Documentation Updates

Update these documents as the migration lands:

- `docs/3_NLP_Solvers/IPOPT/ipopt.readme.md`: recipe contents and local
  toolchain usage.
- `docs/3_NLP_Solvers/IPOPT/tests.readme.md`: test execution through the
  runner, without changing SNOPT/IPOPT comparison policy.
- `testatron/ipopt/README.md`: Testatron runner invocation and artifact mounts.
- `docs/2_Missions/osiris-rex/docs/osiris_rex.readme.md`: OSIRIS toolchain
  invocation.
- Top-level setup documentation: two-checkout prerequisite and secondary
  runner installation.

## Non-Goals

- Publishing the image to a registry.
- Copying or mirroring the EMTG Docker recipe into the secondary repository.
- Replacing Docker with a native host dependency manager.
- Changing the IPOPT solver contract, SNOPT baseline policy, or Testatron
  acceptance criteria.
