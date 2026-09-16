---
created: 2026-09-16
---
# Manual Testatron Execution (IPOPT)

How to run individual Testatron mission cases against the open-source IPOPT
backend outside of pytest. The compiled `EMTGv9` is a `linux/amd64` binary that
lives inside the cached toolchain build volume (`/build/src/EMTGv9`), so these
runs execute **inside the toolchain container**. All output is `unreviewed`
evidence; committed truths are never modified.

## Example: re-running a case with a corrected launch-vehicle key

Some Testatron cases omit `LaunchVehicleKey`, so the characterization harness
falls back to the default `Falcon_9_FT_(RTLS)` instead of the vehicle the
committed truth was built with. That delivers the wrong launch mass and makes
the seeded solve infeasible. The steps below re-run `CoastPhase_EMintercept`
with the correct key (`Atlas_V_401`) in an isolated diagnostic directory —
nothing permanent is modified.

> **Symptom:** the failed run launches at **997.44 kg**
> (`Falcon_9_FT_(RTLS)` @ C3 ≈ 8.61); the committed truth is **2505.33 kg**
> (`Atlas_V_401` @ the same C3).

### 1. Confirm the cached build volume and toolchain image

```bash
docker volume ls | grep emtg-pytest-ipopt
docker image  ls | grep emtg-pytest-toolchain
```

Substitute the tags you see below (this example uses volume
`emtg-pytest-ipopt-309abb32ff087c0b` and image
`emtg-pytest-toolchain:309abb32ff087c0b`).

### 2. Copy the prepared options into a diagnostic directory

```bash
src="testatron/ipopt/manual/all-cases/cases/transcription_tests/CoastPhase_EMintercept"
dst="testatron/ipopt/diagnostics/CoastPhase_Atlas_V_401"
mkdir -p "$dst"
cp "$src/CoastPhase_EMintercept.emtgopt" "$dst/CoastPhase_Atlas_V_401.emtgopt"
```

The prepared file already carries the correct container paths
(`/repo/testatron/universe`, the public NLSII library, the committed
`BEGIN_TRIALX` seed) — only the launch-vehicle key is wrong.

### 3. Set the correct launch-vehicle key and retarget the output

```bash
sed -i.bak \
  -e 's|^LaunchVehicleKey .*|LaunchVehicleKey Atlas_V_401|' \
  -e 's|^mission_name .*|mission_name CoastPhase_Atlas_V_401|' \
  -e 's|^forced_working_directory .*|forced_working_directory /repo/testatron/ipopt/diagnostics/CoastPhase_Atlas_V_401|' \
  "$dst/CoastPhase_Atlas_V_401.emtgopt"

# Verify (expect the public NLSII library and Atlas_V_401):
grep -E '^LaunchVehicleLibraryFile|^LaunchVehicleKey' "$dst/CoastPhase_Atlas_V_401.emtgopt"
```

If no `LaunchVehicleKey` line exists (it was omitted as a default), add one
directly beneath `LaunchVehicleLibraryFile`:

```
LaunchVehicleKey Atlas_V_401
```

### 4. Run EMTG in the toolchain container

```bash
docker run --rm --platform linux/amd64 \
  -w /repo/testatron/ipopt/diagnostics/CoastPhase_Atlas_V_401 \
  -v "$PWD:/repo:ro" \
  -v emtg-pytest-ipopt-309abb32ff087c0b:/build \
  -v "$PWD/testatron/ipopt:/repo/testatron/ipopt:rw" \
  emtg-pytest-toolchain:309abb32ff087c0b \
  /build/src/EMTGv9 \
  /repo/testatron/ipopt/diagnostics/CoastPhase_Atlas_V_401/CoastPhase_Atlas_V_401.emtgopt \
  2>&1 | tee "$dst/run.log"
```

The repository is mounted read-only; only `testatron/ipopt` is writable, so
results land in the diagnostic directory.

### 5. Verify the outcome

```bash
# Feasible solve (not a FAILURE):
grep -E "Acquired (feasible|infeasible) point|Worst constraint|with violation|Decision vector is" "$dst/run.log"

# Success-named output file (no FAILURE_ prefix):
ls "$dst"/*.emtg

# Launch mass (row 1, "launch" event):
grep -m1 "launch" "$dst"/CoastPhase_Atlas_V_401.emtg
```

**Expected results**

| Check | Failed run (`Falcon_9_FT_(RTLS)`) | Corrected run (`Atlas_V_401`) |
|---|---|---|
| Launch mass | `997.44 kg` | **`≈ 2505.33 kg`** |
| Worst constraint violation | `0.0165` (infeasible) | **`≤ 1e-5` (feasible)** |
| Output file | `FAILURE_CoastPhase_*.emtg` | **`CoastPhase_Atlas_V_401.emtg`** |
| Final mass | `~1012 kg` | **`≈ 2505.33 kg` (matches truth)** |

A feasible solve at ≈ 2505.33 kg confirms the failure was a launch-vehicle-key
configuration issue, not a solver defect — the fix is to have the harness
resolve the correct key (via a mass-match against the committed truth) instead
of defaulting to `Falcon_9_FT_(RTLS)`.

## Troubleshooting

- **`Unable to execute EMTG: [Errno 2] No such file or directory: .../build/src/EMTGv9`**
  The `EMTGv9` binary is `linux/amd64` and lives in the Docker build volume, not
  on the host. Do not pass a host path such as `"$PWD/build/src/EMTGv9"` to
  `--emtg`; run inside the toolchain container and use the in-container path
  `/build/src/EMTGv9` (see step 4).
- **Result classified `dependency_blocked` with `return_code: null`**
  EMTG never executed (missing binary or a missing hardware/universe
  dependency). Check `run.log` and `compatibility.json` in the case directory.
