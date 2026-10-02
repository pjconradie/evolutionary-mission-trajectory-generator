# Generate Stage 0 Baseline Results

This guide creates a new local Stage 0 capture before moving regression suites
or IPOPT artifact roots. It records current behavior; it does not promote
generated results or modify immutable Testatron, tutorial, or NASA SNOPT data.

Run all commands from the repository root with the Python virtual environment
active and Docker running. Use a new capture root outside `testatron/ipopt` so
the evidence remains independent of the artifact-root migration.

## Capture Environment

Choose a unique capture root and record execution identity before running any
test. Keep the report even when a later test fails.

```bash
CAPTURE_ROOT="$PWD/baseline-artifacts/stage0-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$CAPTURE_ROOT"

{
	printf 'timestamp_utc='; date -u '+%Y-%m-%dT%H:%M:%SZ'
	printf 'commit='; git rev-parse HEAD
	printf '\n[git status]\n'; git status --short
	printf '\n[host]\n'; uname -a
	printf '\n[python]\n'; python --version
	printf '\n[docker]\n'; docker version
} > "$CAPTURE_ROOT/environment.txt"
```

Derive the content-addressed toolchain image and the persistent IPOPT build
volume used by the integration probes:

```bash
IMAGE="$(python - <<'PY'
import sys
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str(root / "tests" / "integration"))
from _docker_support import toolchain_image_tag

print(toolchain_image_tag(root))
PY
)"

VOLUME="$(python - <<'PY'
import sys
from pathlib import Path

root = Path.cwd()
sys.path.insert(0, str(root / "tests" / "integration"))
from _docker_support import build_volume_name, toolchain_image_tag

print(build_volume_name(toolchain_image_tag(root), "ipopt"))
PY
)"

printf 'image=%s\nvolume=%s\n' "$IMAGE" "$VOLUME" \
	| tee "$CAPTURE_ROOT/toolchain.txt"
docker image inspect "$IMAGE" --format 'image_id={{.Id}}' \
	| tee -a "$CAPTURE_ROOT/toolchain.txt"
docker volume inspect "$VOLUME" --format 'volume={{.Name}}' \
	| tee -a "$CAPTURE_ROOT/toolchain.txt"
```

## Run Contracts and Benchmarks

Run the characterization contracts first:

```bash
python -m pytest tests/test_ipopt_characterization.py -q \
	| tee "$CAPTURE_ROOT/characterization-contracts.log"
```

Run every benchmark stage in a separate artifact directory. Do not combine
replay and refinement: both write `comparison.json` and `result.json`.

```bash
EMTG_TEST_ARTIFACT_DIR="$CAPTURE_ROOT/track-acs-replay" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_track_acs_replay_matches_committed_truth \
	--integration -vv

EMTG_TEST_ARTIFACT_DIR="$CAPTURE_ROOT/track-acs-ipopt" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_track_acs_ipopt_refinement_retains_seed \
	--integration -vv

EMTG_TEST_ARTIFACT_DIR="$CAPTURE_ROOT/osiris-2022-replay" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2022_replay_matches_nasa_result \
	--integration -vv

EMTG_TEST_ARTIFACT_DIR="$CAPTURE_ROOT/osiris-2022-ipopt" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2022_ipopt_refinement_retains_nasa_seed \
	--integration -vv

EMTG_TEST_ARTIFACT_DIR="$CAPTURE_ROOT/osiris-2024-replay" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2024_replay_matches_nasa_result \
	--integration -vv

EMTG_TEST_ARTIFACT_DIR="$CAPTURE_ROOT/osiris-2024-ipopt" \
python -m pytest \
	tests/integration/test_ipopt_backend.py::test_osiris_2024_ipopt_refinement_retains_nasa_seed \
	--integration -vv
```

## Run Testatron Characterization

The characterizer runs inside the same pinned `linux/amd64` toolchain. The
repository is mounted read-only at `/repo`, the reusable IPOPT build is mounted
at `/build`, and only the capture directory is writable at `/artifacts`.

First run representative filters from each Testatron group. Keep the selected
filters and output manifest with the capture.

```bash
REPRESENTATIVE="$CAPTURE_ROOT/cases-representative"
mkdir -p "$REPRESENTATIVE"

docker run --rm \
	--platform linux/amd64 \
	--mount "type=bind,src=$PWD,dst=/repo,readonly" \
	--mount "type=volume,src=$VOLUME,dst=/build" \
	--mount "type=bind,src=$REPRESENTATIVE,dst=/artifacts" \
	"$IMAGE" sh -c '
		set -eu
		test -x /build/src/EMTGv9
		python /repo/testatron/ipopt_characterization.py \
			--ipopt-characterization \
			--emtg /build/src/EMTGv9 \
			--output-root /artifacts \
			--timeout 300 \
			--filter global_mission_options/globalmissionoptions_MGALT_DLAbounds \
			--filter journey_options/EarthToMarsRendezvous \
			--filter output_options/outputoptions_frameICRF \
			--filter physics_options/physicsoptions_SPICEphem \
			--filter script_constraint_tests/EVM_pEnd_distance \
			--filter solver_options/solveroptions_ACEfeasibility \
			--filter state_representation_tests/FreePointArrival_IncomingBplaneRpTA_testatron \
			--filter transcription_tests/CoastPhase_EMintercept
	'
```

Then inventory the complete corpus in a separate directory. `--resume` skips
only cases that already have a retained result in this same directory, so rerun
the exact command after an interruption.

```bash
FULL="$CAPTURE_ROOT/cases-full"
mkdir -p "$FULL"

docker run --rm \
	--platform linux/amd64 \
	--mount "type=bind,src=$PWD,dst=/repo,readonly" \
	--mount "type=volume,src=$VOLUME,dst=/build" \
	--mount "type=bind,src=$FULL,dst=/artifacts" \
	"$IMAGE" sh -c '
		set -eu
		test -x /build/src/EMTGv9
		python /repo/testatron/ipopt_characterization.py \
			--ipopt-characterization \
			--emtg /build/src/EMTGv9 \
			--output-root /artifacts \
			--timeout 300 \
			--resume
	'
```

## Preserve Source and Truth Identity

Before and after the capture, record hashes for immutable source options and
their adjacent SNOPT `.emtg` results. The before and after reports must match.

```bash
find testatron/tests -type f \( -name '*.emtgopt' -o -name '*.emtg' \) -print0 \
	| sort -z \
	| xargs -0 shasum -a 256 > "$CAPTURE_ROOT/testatron-source-truth.sha256"
```

Use [how_to_interpret_results.readme.md](how_to_interpret_results.readme.md)
to review the generated evidence. This guide documents a pre-move baseline;
[testatron/ipopt/benchmarks/how_to_generate_results.readme.md](../testatron/ipopt/benchmarks/how_to_generate_results.readme.md)
documents routine benchmark operation.
