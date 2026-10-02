# Generate IPOPT Benchmark Results

This guide runs the six Docker-backed IPOPT benchmark probes and retains their
unreviewed evidence outside `testatron/ipopt`. Run every command from the
repository root.

The benchmarks are:

- TrackACSProp replay and IPOPT refinement.
- OSIRIS-REx 2022 replay and IPOPT refinement.
- OSIRIS-REx 2024 replay and IPOPT refinement.

Replay evaluates the reference decision vector with `run_inner_loop 0`; it does
not run SNOPT or IPOPT. Refinement starts IPOPT from that verified seed.

## Prerequisites

- Activate the repository Python environment.
- Start Docker Desktop or another compatible Docker daemon.
- Do not modify `testatron/tests`, tutorial result packages, or NASA result
	packages.
- Choose a writable artifact root outside `testatron/ipopt`. The commands use
	`baseline-artifacts/` so that generated evidence is easy to inspect and
	remove.

Confirm Docker is available before starting:

```bash
docker info >/dev/null
python -m pytest --integration --collect-only -q
```

## Run Individual Stages

Use a distinct `EMTG_TEST_ARTIFACT_DIR` for every replay and refinement stage.
Each stage writes names such as `comparison.json` and `result.json`; combining
stages in one directory overwrites the earlier stage's evidence.

### TrackACSProp

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/track-acs-replay" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_track_acs_replay_matches_committed_truth \
	--integration -vv

EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/track-acs-ipopt" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_track_acs_ipopt_refinement_retains_seed \
	--integration -vv
```

### OSIRIS-REx 2022

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/osiris-2022-replay" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2022_replay_matches_nasa_result \
	--integration -vv

EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/osiris-2022-ipopt" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2022_ipopt_refinement_retains_nasa_seed \
	--integration -vv
```

### OSIRIS-REx 2024

```bash
EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/osiris-2024-replay" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2024_replay_matches_nasa_result \
	--integration -vv

EMTG_TEST_ARTIFACT_DIR="$PWD/baseline-artifacts/osiris-2024-ipopt" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2024_ipopt_refinement_retains_nasa_seed \
	--integration -vv
```

## Review Evidence

Each successful directory contains at least:

- `comparison.json`: numerical, structural, feasibility, and IPOPT checks.
- `result.json`: stage, source and generated mission names, duration, and
	artifact filenames.
- `provenance.json`: immutable source paths and SHA-256 hashes.
- `compatibility.json`: staged options, hardware, universe, and seed details.
- `run.log`: EMTG and IPOPT diagnostics.
- Generated `.emtg` mission and `XFfile.csv` data where applicable.

Use [how_to_interpret_results.readme.md](how_to_interpret_results.readme.md)
to review replay and refinement acceptance criteria. A passing pytest result
does not promote any generated file to a regression truth.

## Rerun and Cleanup

Rerunning a stage replaces files in that stage's selected artifact directory.
Use a new directory when preserving an earlier run is important. Remove only
generated evidence when it is no longer needed:

```bash
rm -rf baseline-artifacts/track-acs-replay \
			 baseline-artifacts/track-acs-ipopt \
			 baseline-artifacts/osiris-2022-replay \
			 baseline-artifacts/osiris-2022-ipopt \
			 baseline-artifacts/osiris-2024-replay \
			 baseline-artifacts/osiris-2024-ipopt
```
