# MBH global optimization: out-of-bounds trial points

## Summary

The OSIRIS-REx low-fidelity mission uses EMTG's Monotonic Basin Hopping (MBH) global optimizer. Its generated options currently contain:

```text
run_inner_loop 1
MBH_hop_distribution 2
MBH_max_step_size 1.0
MBH_time_hop_probability 0.05
MBH_RNG_seed -1
```

Here, `run_inner_loop 1` selects MBH, distribution `2` selects Pareto hops, and seed `-1` uses the system clock. This combination makes failures difficult to reproduce and allows very large perturbations before EMTG clips the normalized decision variables to their declared bounds.

The current high-fidelity stage uses `run_inner_loop 3`, which selects a direct IPOPT solve. That is intentional: high fidelity should refine the same-invocation single-phase result rather than perform another unconstrained global search.

## What “out of bounds” can mean

There are two different failure classes:

1. **A decision variable exceeds its EMTG lower or upper bound.** This is an MBH sampling or seeding problem.
2. **A decision variable is inside its EMTG bound but outside a valid physical or ephemeris domain.** For this mission, a trial epoch can be legal according to a broad options bound while still falling outside the available SPICE/SplineEphem coverage.

These must not be fixed by blindly widening every bound. Widening an epoch bound can make the SPICE failure worse and can make the optimizer search dates that are not part of the intended OSIRIS-REx reconstruction.

## Relevant MBH behavior

The implementation is in [monotonic_basin_hopping.cpp](../../../../src/InnerLoop/monotonic_basin_hopping.cpp).

Normal `hop()` operations perturb each normalized variable and then clip it to the corresponding `Xlowerbounds` and `Xupperbounds`. This protects the final hop vector from ordinary numerical excursions, but it does not guarantee that the trial point is physically meaningful or inside the SPICE coverage window.

The Pareto hop also has a numerical weakness. If its generated step is not finite, the code skips assignment for that variable. The value left in `X_after_hop[k]` then comes from an earlier trial rather than from a known valid value. A non-finite hop should instead be rejected or replaced with the incumbent value before clipping.

The `seed()` extension path contains an arithmetic error:

```cpp
this->RNG.uniform(0.0, 1.0)
	* ((Xupper - Xlower) + Xlower)
```

The correct bounded-uniform expression is:

```cpp
this->RNG.uniform(0.0, 1.0) * (Xupper - Xlower) + Xlower
```

The first form is not equivalent when `Xlower` is nonzero and can generate a seed outside the intended interval. This path matters whenever MBH is seeded with a partial or shorter trial vector.

## Immediate workaround

For a reproducible diagnostic MBH run, use conservative uniform hops:

```text
MBH_hop_distribution 0
MBH_max_step_size 0.02
MBH_time_hop_probability 0.0
MBH_RNG_seed 12345
```

Start with `0.02`; increase to `0.05` or `0.1` only after the run is stable. Uniform hops are easier to inspect than Pareto hops because their maximum normalized perturbation is explicit. Disabling time hops prevents additional synodic-period perturbations from moving time variables to the edges of their bounds.

Keep the mission-specific bounds narrow and intentional:

- Fix the departure state and departure wait time to the measured in-flight epoch.
- Keep the first DSM epoch constrained to the 2016-12-28 UTC calendar day.
- Keep Bennu arrival constrained to the 2018-12-03 UTC calendar day.
- Keep total flight time at 300-900 days unless the reconstruction scope changes.
- Keep trial epochs inside the configured SPICE/SplineEphem coverage window.

The first valid comparison should use the same input kernels, options, EMTG build, and fixed `MBH_RNG_seed`. Archive the generated options and `XFfile.csv` with the result so the first invalid or infeasible decision variable can be identified.

## Correct code-level fix

The seed extension should be changed in [monotonic_basin_hopping.cpp](../../../../src/InnerLoop/monotonic_basin_hopping.cpp) to:

```cpp
this->X_after_hop[k] =
	(this->RNG.uniform(0.0, 1.0)
		* (this->myProblem->Xupperbounds[k] - this->myProblem->Xlowerbounds[k])
		+ this->myProblem->Xlowerbounds[k])
	/ this->myProblem->X_scale_factors[k];
```

The Pareto path should also handle non-finite steps explicitly. A robust policy is:

1. Generate the step.
2. If the step or candidate value is non-finite, copy the incumbent value.
3. Clamp the candidate to the normalized lower and upper bounds.
4. Convert it back to the unscaled decision vector.

The same finite-value policy should be applied to any future hop distribution.

## Validation sequence

1. Run the unit and focused IPOPT tests to verify the toolchain.
2. Run low-fidelity MBH with the fixed seed and uniform hops.
3. Inspect `XFfile.csv`, the MBH archive, and `results/low/emtg.log`.
4. Confirm that no trial reaches an ephemeris lookup outside the staged kernel coverage.
5. Re-enable Pareto hops only if they provide a measurable improvement.
6. Keep the single-phase and high-fidelity stages on direct IPOPT, as implemented by [run_mission.py](../src/run_mission.py).

## Interpretation for OSIRIS-REx

An MBH result is a global-search result for the configured mathematical problem, not proof of the flown trajectory or a global physical optimum. The first DSM date is constrained to the flown date, but its magnitude remains an optimization variable. The reported deterministic delta-v also begins at the supplied in-flight state and excludes launch and injection.
