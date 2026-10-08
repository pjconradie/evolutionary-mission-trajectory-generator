# Testatron IPOPT Testing and Baselining

This directory holds unreviewed IPOPT evidence for the 137 immutable Testatron
SNOPT input/result pairs under `testatron/tests/`. It has two separate
responsibilities:

- The testing framework verifies EMTG code, input staging, comparisons, the
  Docker toolchain, and selected runtime behavior.
- The baselining framework generates repeatable IPOPT evidence from immutable
  SNOPT inputs. It does not promote a result or change a Testatron truth.

Run every command in this guide from the repository root.

## Safety and Ownership

- Never edit or overwrite `testatron/tests/**/*.emtgopt` or the adjacent SNOPT
  `.emtg` files. They are immutable inputs.
- Never edit `docs/3_NLP_Solvers/IPOPT/stage6_checklist.md` from a script or
  test run. It is a manual review record.
- Generated evidence is always `unreviewed`. A passing test does not promote a
  result or establish a new truth.
- The Docker harness owns the container, image, build volume, `/repo`,
  `/build`, and `/artifacts` paths. Do not run a `/repo/...` command directly
  on the host.
- `EMTG_TEST_ARTIFACT_DIR` is a host path. It selects where Docker writes
  generated evidence.
- A baselining run replaces only the selected
  `baselining/<group>/<case>/` directory. It preserves every other case under
  `baselining/`.

## Testing Framework

The test suite validates the system that produces and checks evidence. It is
not itself a corpus-baselining command.

### Unit Contracts

Unit contracts cover case discovery, immutable seed alignment, replay and
refinement comparisons, classifications, deterministic policy enforcement,
provenance, repeatability, case ordering, and artifact replacement behavior.
They do not launch Docker or EMTG.

```zsh
pytest tests/test_ipopt_characterization.py -q
```

### Docker Integration Contracts

Docker integration tests validate the pinned Linux amd64 IPOPT toolchain,
CMake build volume, EMTG execution, repeatability, and the host-facing
baselining launcher.

```zsh
pytest tests/integration/test_baselining.py -q
```

The module includes two repeatability probes and one CLI/batch-layout probe.
Their default evidence location is pytest temporary storage. To retain their
artifacts, set `EMTG_TEST_ARTIFACT_DIR`.

More general pytest categories and markers are documented in
[`testatron/ipopt/README.md`](../README.md). The Docker lifecycle constraints
are documented in
[`docs/3_NLP_Solvers/IPOPT/docker_deployment.readme.md`](../../../docs/3_NLP_Solvers/IPOPT/docker_deployment.readme.md).

## Baselining Framework

Baselining runs the Testatron IPOPT workflow through pytest, which creates the
container, mounts the repository read-only, reuses the IPOPT build volume, and
mounts the selected host artifact directory as writable `/artifacts`.

The runner processes selected cases in the reviewed Testatron group order:
`global_mission_options`, `journey_options`, `mission_tests`,
`output_options`, `physics_options`, `script_constraint_tests`,
`solver_options`, `spacecraft_options`, `state_representation_tests`, and
`transcription_tests`. `mission_tests` currently contains no paired cases.

### What One Case Run Does

For each selected immutable pair:

1. The runner records source and baseline SHA-256 hashes.
2. It stages a replay from the SNOPT decision vector with `run_inner_loop = 0`.
   Replay does not run SNOPT or IPOPT.
3. It compares the generated replay mission to the immutable SNOPT mission.
   A failed replay blocks refinement.
4. Only after an acceptable replay, it runs seeded IPOPT refinement with
   `run_inner_loop = 3`.
5. It requires an accepted native IPOPT exit and compares the refined mission
   to the immutable SNOPT mission.
6. It repeats the full case twice in fresh `attempt-1` and `attempt-2`
   directories. Materially different attempts cannot remain `matched_snopt`.

The deterministic controls are versioned in
[`baselining_policy.json`](baselining_policy.json): MBH is disabled, the RNG
seed is fixed, solver threads are limited to one, and only `Optimal Solution
Found.` is an accepted native IPOPT exit.

### Run One Case to a Durable Directory

This is the supported host command. It uses pytest as the Docker launcher and
replaces only the selected case's evidence directory.

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/tests" \
pytest tests/integration/test_baselining.py -q \
  -k baselining_cli_writes_fixed_mirrored_layout \
  --baselining-filter global_mission_options/globalmissionoptions_MGALT_DLAbounds
```

The evidence appears at:

```text
testatron/ipopt/tests/tests/baselining/
  global_mission_options/
    globalmissionoptions_MGALT_DLAbounds/
      provenance.json
      result.json
      repeatability.json
      attempt-1/
        result.json
        replay/
      attempt-2/
        result.json
        replay/
```

A `refinement/` directory appears inside each attempt only when replay was
acceptable. A replay mismatch is evidence, not a reason to weaken tolerances
or run refinement anyway.

### Run Multiple Selected Cases

Repeat `--baselining-filter` for every case. These selected case directories
are rebuilt; other previously generated case directories remain intact.

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/tests" \
pytest tests/integration/test_baselining.py -q \
  -k baselining_cli_writes_fixed_mirrored_layout \
  --baselining-filter global_mission_options/globalmissionoptions_MGALT_RLAbounds \
  --baselining-filter global_mission_options/globalmissionoptions_MGALT_DLAbounds
```

A group can be selected with a glob:

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/tests" \
pytest tests/integration/test_baselining.py -q \
  -k baselining_cli_writes_fixed_mirrored_layout \
  --baselining-filter 'global_mission_options/*'
```

An explicit wildcard selects the full current corpus. Do this only after
reviewing selected-case evidence and confirming sufficient time and disk space:

```zsh
EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/tests" \
pytest tests/integration/test_baselining.py -q \
  -k baselining_cli_writes_fixed_mirrored_layout \
  --baselining-filter '*'
```

To write an experiment outside the repository, replace the value of
`EMTG_TEST_ARTIFACT_DIR` with an absolute host directory. The artifact tree
still begins with `baselining/` below that directory.

## Read the Evidence

At each selected case root:

- `provenance.json` records immutable input hashes and policy provenance.
- `result.json` combines both attempts and their classifications.
- `repeatability.json` says whether their stable comparison content agrees.

Within each attempt:

- `replay/` contains the staged options, compatibility mapping, EMTG log,
  generated mission, comparison, and stage provenance.
- `refinement/`, when present, contains corresponding IPOPT evidence and its
  native exit diagnostic.
- `result.json` records that attempt's classification and detail.

The possible final classifications are:

| Classification | Meaning |
| --- | --- |
| `matched_snopt` | Replay and refinement both passed comparison; IPOPT had an accepted native exit; attempts were stable. |
| `mismatch_snopt` | A completed comparable replay or refinement differed from the immutable SNOPT reference. |
| `infeasible` | Generated mission feasibility did not meet the required tolerance. |
| `topology_changed` | Journey, event, or decision schema changed. |
| `dependency_blocked` | Required staged input, hardware, universe data, or executable was unavailable. |
| `timed_out` | EMTG did not finish before the configured timeout. |
| `process_failed` | EMTG execution failed. |
| `parse_failed` | Generated output could not be parsed or prepared for comparison. |

Before considering any manual decision, inspect both attempts' `run.log`,
`comparison.json`, `provenance.json`, and `result.json`. Confirm source and
baseline hashes are unchanged. Do not modify the policy or a case tolerance to
make one result pass.

## Promote a Reviewed Baseline

Baselining evidence is replaceable and remains under `baselining/`. Promotion
is a separate, explicit action that creates a curated result below
`testatron/ipopt/tests/tests/<group>/<case>/`. It never runs automatically as
part of a pytest baselining command.

Before promotion, a reviewer must record approval in
[`docs/3_NLP_Solvers/IPOPT/baselining_decision_log.md`](../../../docs/3_NLP_Solvers/IPOPT/baselining_decision_log.md).
The promotion command then verifies that both attempts are stable and
`matched_snopt`, replay and refinement comparisons are acceptable, the native
IPOPT exit is policy-accepted, and the immutable input hashes still match.

```zsh
python testatron/ipopt_characterization.py \
  --promote-baseline global_mission_options/globalmissionoptions_MGALT_DLAbounds \
  --approve-baseline \
  --output-root "$PWD/testatron/ipopt/tests/tests"
```

The command creates a compact curated package:

```text
testatron/ipopt/tests/tests/
  global_mission_options/
    globalmissionoptions_MGALT_DLAbounds/
      globalmissionoptions_MGALT_DLAbounds.emtg
      promotion.json
      provenance.json
      replay-comparison.json
      refinement-comparison.json
      repeatability.json
      ipopt-diagnostics.json
```

The two complete working attempts remain under `baselining/`; promotion copies
one canonical IPOPT mission and the evidence required to verify it. Promotion
refuses to overwrite an existing curated directory. After a separate review,
use `--replace-promoted` only when replacing that specific curated result is
intentional.

Case #1 cannot be promoted while it remains `mismatch_snopt`. A failed
promotion leaves both curated output and immutable Testatron inputs untouched.

## Troubleshooting

- **`/repo/...` not found on macOS:** it is a container path. Use the pytest
  commands above rather than running the in-container command directly.
- **No durable artifacts:** set `EMTG_TEST_ARTIFACT_DIR`; otherwise pytest uses
  a temporary directory below `/private/var/folders/.../pytest-of-...`.
- **A selected case was replaced:** that is intentional. Rerun it only when its
  prior unreviewed evidence may be discarded. Unselected case roots are
  preserved.
- **No `refinement/` directory:** replay did not pass or an operational failure
  occurred. Inspect replay evidence first; refinement is intentionally blocked.
- **Docker or build failure:** verify Docker is running, then consult the
  deployment guide. Do not hand-create image tags, mounts, or build volumes for
  routine baselining.

## Related Guides

- [`testatron/ipopt/README.md`](../README.md): pytest categories, tutorial
  verification, and general IPOPT evidence rules.
- [`testatron/ipopt/tests/baselining_policy.json`](baselining_policy.json):
  deterministic controls and accepted native IPOPT exits.
- [`docs/3_NLP_Solvers/IPOPT/docker_deployment.readme.md`](../../../docs/3_NLP_Solvers/IPOPT/docker_deployment.readme.md): Docker deployment contract.
- [`docs/3_NLP_Solvers/IPOPT/stage6_checklist.md`](../../../docs/3_NLP_Solvers/IPOPT/stage6_checklist.md): manual-only review checklist.
