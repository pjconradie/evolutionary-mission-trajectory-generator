
# Endpoint Difference

Once launch mass, topology, controls, flight time, and final mass align, remaining endpoint differences can come from:

- Ephemeris/SPICE or spline interpolation differences
- Propagation/integration implementation or tolerances
- Force-model changes, such as gravity or perturbation handling
- Frame/state conversion differences
- Small accumulated numerical differences in a long propagation

Already around 117 cases with endpoint difference of around 107 km.

Example: For `EarthToMars_ForcedInitialCoast`, the ΔvΔv and velocity differences are tiny while position differs by `107.675 km`. That pattern points more toward ephemeris/propagation drift than launch-vehicle selection. It remains an unproven hypothesis until we compare the first state-epoch divergence.
# journey_options/EarthMars_Depart2-2_Arrive2-2

```json
{
	"case_id": "journey_options/EarthMars_Depart2-2_Arrive2-2",
	"classification": "parse_failed",
	"detail": {
		"first": "EMTG produced no .emtg result",
		"second": "EMTG produced no .emtg result"
		},
	"comparison_classification": {
		"first": {
			"replay": null,
			"refinement": null
		},
		"second": {
			"replay": null,
			"refinement": null
		}
	}
}
```

To fly the spaceship, EMTG needs instructions about its engine:

- How much push it makes
- How much electricity it uses
- How much propellant it consumes

Those instructions are selected by a number called `engine_type`.

In this test, the old instruction says:

```text
engine_type 23
```

A long time ago, number `23` meant:

```text
NEXT TT11 High-Thrust
```

That was like saying:

> “Use the special red rocket-engine recipe stored inside the old version of EMTG.”

The old EMTG program knew that recipe by heart. It had the engine’s thrust and fuel-use data built in.

But the current open-source EMTG is newer and has a smaller list of built-in recipes. It only recognizes engine numbers `0` through `17`.

So when it reads `23`, it says:

> “I do not know what engine number 23 is. I cannot start the mission.”

That is why there is no `.emtg` result file and the case is currently called `parse_failed`.

The important part: simply changing `23` to another number would be like putting a different engine into the toy spaceship. EMTG might run, but it would no longer be replaying the same historical mission. The expected propellant use, thrust, flight time, and final location could change.

A modern, table-driven engine setting can represent a high-thrust engine, but it needs a file containing the original engine recipe: a **throttle table**. The historical test refers to:

```text
NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable
```

That file is not present in the public test resources. Without its real contents, EMTG cannot faithfully reconstruct the old engine.

So `unsupported_legacy_engine` would mean:

> “This test input is valid for an older EMTG that knew engine 23, but this open-source EMTG does not contain the needed engine model data. We intentionally did not substitute a different engine.”

It is a more honest label than `parse_failed` because it says *why* the input cannot run. It is not an IPOPT failure, an SNOPT mismatch, or a trajectory failure. It is an old configuration asking for an engine recipe that the current executable no longer has.


# `topology_changed` cases

There are 13 `topology_changed` cases:

1. `journey_options/EarthToMars_ForcedInitialCoast`
2. `journey_options/EarthToMars_ForcedTerminalCoast`
3. `script_constraint_tests/EVM_pEndRRP_arrival`
4. `script_constraint_tests/EarthMarsLikePointFreePointChemRendezvous_RPRconjunction`
5. `script_constraint_tests/EarthMarsLikePointFreePointChemRendezvous_RRPconjunction`
6. `script_constraint_tests/EarthMars_RPRangle_force_conjunction`
7. `spacecraft_options/spacecraft_LT_multiStage_spacecraftFile`
8. `spacecraft_options/spacecraft_LT_powerFile`
9. `spacecraft_options/spacecraft_LT_propFile`
10. `state_representation_tests/FreePointArrival_IncomingBplaneRpTA_testatron`
11. `state_representation_tests/FreePointArrival_OutgoingBplaneRpTA_testatron`
12. `state_representation_tests/PeriapseArrival_IncomingBplaneRpTA_testatron`
13. `state_representation_tests/PeriapseArrival_OutgoingBplaneRpTA_testatron`

They naturally form four investigation groups: forced coasts, script constraints, spacecraft-file staging, and boundary-state representations.

We resolve each case by finding **why its trip changed**:

1. Compare the old and generated event sequences to identify the first added, removed, or reordered event.
2. Check the staged configuration, hardware, ephemerides, and current EMTG defaults that control that event.
3. If staging accidentally changed a mission input, correct the staging mapping and rerun.
4. If current EMTG intentionally changed the mission construction, retain `topology_changed` until a reviewed replacement baseline is approved.
5. If neither is true, treat it as an EMTG regression and fix the mission-construction code.

We should not change tolerances or promote these cases just to remove the label; that would be comparing two different trips as though they were the same one.