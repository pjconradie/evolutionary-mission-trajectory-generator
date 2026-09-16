---
created: 2026-09-16
---
We have a miss match between the supplied configuration in the open source repository and the configurations actually used by NASA for verification.

It is clear that changing the input configuration `testatron/ipopt/manual/coast-retest/CoastPhase_EMintercept.emtgopt` under:

- HardwarePath /repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/Config_Files/hardware_models
- LaunchVehicleLibraryFile LaunchVehicles_PubliclyDistributable_NLSII_v2.emtg_launchvehicleopt
- SpacecraftOptionsFile default.emtg_spacecraftopt
- LaunchVehicleKey Falcon_9_FT_(RTLS)_CoastPhase_Test

we can set the correct spacecraft configuration to recreate the NASA verification results.

It is thus suggested to have a lookup file like `testatron/ipopt/case_lookup.csv` that contains a master mapping of the configuration that needs setting for each of the 137-sweep for testron.

The lookup csv will have the desired settings to verify the NASA EMTG using IPOPT solver with appropriate spacecraft configuration.

---

Let me verify the specific configs the README references before judging whether it's sensible.

Searched for text `Falcon_9_FT_(RTLS)_CoastPhase_Test`, 8 results

Searched for files matching `**/*NLSII_v2*`, 1 match

Searched for regex `LaunchVehicleKey|LaunchVehicleLibraryFile|SpacecraftModelInput` (`**/testatron/tests/transcription_tests/CoastPhase_EMintercept.emtgopt`), 4 results

Reviewed — and I'd push back before you go further with this. **The concept (a per-case lookup) is sensible; the specific mechanism the README describes is not, and it actually contradicts what your own lookup just proved.** Here's what the files show.

## What the README's approach actually does

1. It **fabricated a launch vehicle.** `LaunchVehicles_PubliclyDistributable_NLSII_v2.emtg_launchvehicleopt:11` defines `Falcon_9_FT_(RTLS)_CoastPhase_Test` as `3277.8748 -79.874 -2.288 0.1325` — i.e. the **public Falcon's shape** (`-79.874, -2.288, 0.1325`) with the constant bumped from `1770 → 3277.87` so the mass lands on ~2505.3 kg **at one point** ($C3=8.6079$).
2. It **created an unnecessary `_v2` library** and a misleadingly-named key (it's not a Falcon).
3. It **edited the committed Testatron test input** — `CoastPhase_EMintercept.emtgopt:48` now points at that fabricated vehicle.

## Why that's the wrong fix

- **It fabricates a launch model** — exactly the thing to avoid. The real vehicle is **`Atlas_V_401`**, which already exists in the *unmodified* public library and matches the truth **exactly** (2505.333433 kg) — your own `case_lookup.csv` resolved it: `…CoastPhase_EMintercept … Atlas_V_401 … 2505.3334 … 0.0` error.

- **It's fragile.** The fabricated entry only matches at $C3=8.6079$ (Falcon curvature + a bumped constant). If IPOPT moves the launch $C3$ during the solve, it delivers the wrong mass and can re-introduce infeasibility. `Atlas_V_401` is correct at *every* $C3$.

- **It modifies a committed test source** — the exact thing the whole "unreviewed, never touch truths" discipline exists to prevent. The fix belongs in harness *preparation*, not in the checked-in `.emtgopt`.

- `SpacecraftOptionsFile default.emtg_spacecraftopt` is a red herring — CoastPhase uses `SpacecraftModelInput 2` (inline), so it reads no spacecraft file.

## The sensible version (which you already have)

Your generator did the right thing: it mass-matched the truth to the **real** `Atlas_V_401` in the **existing** public library. So the correct config for CoastPhase is simply:

```

LaunchVehicleLibraryFile LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt

LaunchVehicleKey Atlas_V_401

```

No `_v2` library, no synthetic vehicle, no edits to the test `.emtgopt`. The lookup stores `Atlas_V_401`; the harness applies it at prepare-time.
## Recommendation

1. **Make `case_lookup.csv`/`.json` the source of truth** — its `resolved_launch_vehicle.key` is derived by mass-matching real library entries, which is correct and robust across all $C3$.
2. **Revert the fabrication:** delete `LaunchVehicles_PubliclyDistributable_NLSII_v2…` and the `Falcon_9_FT_(RTLS)_CoastPhase_Test` entry, and restore `CoastPhase_EMintercept.emtgopt` (remove the added `LaunchVehicleLibraryFile`/`LaunchVehicleKey` lines) so the committed test input is unmodified.
3. **Rewrite the README** to describe the real approach: "for each case, the lookup pins the `LaunchVehicleKey` (and library/hardware roots) that reproduces the committed truth, resolved by mass-matching — applied by the harness at preparation, never by editing test sources."

So: keep the lookup table idea (it's exactly right), but drop the synthetic-vehicle / edited-source mechanism in favor of the real `Atlas_V_401` your generator already identified.

Want me to rewrite `case_lookup.README.md` to describe the correct mass-match/lookup approach, and list the exact files to revert (the `_v2` library and the `CoastPhase_EMintercept.emtgopt` edits)?