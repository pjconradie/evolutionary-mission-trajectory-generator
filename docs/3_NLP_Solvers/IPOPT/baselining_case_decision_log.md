# IPOPT Baselining Decision Log

This generated log documents the final, two-attempt IPOPT replay evidence for every immutable Testatron SNOPT case. It is generated from the fixed baselining evidence root; source `.emtgopt` files and SNOPT `.emtg` baselines are not modified.

## Universal Runtime Staging

Every replay selects IPOPT, writes a staged options file and working directory, aligns the immutable SNOPT decision vector, and evaluates it with `run_inner_loop=0`. A refinement, when present, runs only after an acceptable replay and uses `run_inner_loop=3`. The case-specific changes below are additional staged compatibility actions, each recorded in the corresponding `compatibility.json`.

## Case Records

## global_mission_options

### global_mission_options/globalmissionoptions_MGALT_DLAbounds

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `LaunchVehicleKey`: `Falcon_9_FT_(RTLS)` -> `Atlas_V_401`. case-scoped public launch vehicle override: the implicit Falcon_9_FT_(RTLS) default has C3 upper bound 10, while the immutable SNOPT seed requires C3 48.5809

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.292669897485666e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2516805231571` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_RLAbounds

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.292669896597488e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2516805231571` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_constrDryMass

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.292700798101066e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2516691982746` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_constrFinalMass

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.292700798101066e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2516691982746` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_includeInitialImpulse

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.292677564241785e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.251643538475` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_numtimesteps

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.297581296772933e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.251783490181` km, velocity `3.000000003972048e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj0

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `objective`: IPOPT - SNOPT = `4.496873597048534e-06`.
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.496873597048534e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.140355348587` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj1

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.496873597048534e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.140355348587` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj14

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.962998233295821e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2327777445316` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj15

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.962998233295821e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2327777445316` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj17

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `3.393221836844873e-08`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3795886486769` km, velocity `3.999999975690116e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj18

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.795571643370408e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2644922435284` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj19

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.795571643370408e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2644922435284` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj20

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.496873597048534e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.140355348587` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj22

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.580805709444633e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3130910694599` km, velocity `1.999999987845058e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj23

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.580805709444633e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3130910694599` km, velocity `1.999999987845058e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj3

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.496873597048534e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.140355348587` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj4

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `9.289808605927874e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.1489091515541` km, velocity `4.000000064507958e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj5

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.496873597048534e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.140355348587` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj8

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.496873597048534e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.140355348587` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_obj9

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.496873597048534e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.140355348587` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_postFlybyCoast

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.802177292871022e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.140355348587` km, velocity `3.000000026176508e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_postLaunchTCM

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.126954548931081e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2757586538792` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_postlaunchCoast

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.281017942529218e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2518943846226` km, velocity `2.000000165480742e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_preFlybyCoast

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.297272663933427e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.1147038340569` km, velocity `3.999999997894577e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_preFlybyTCM

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.496873597048534e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.140355348587` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGALT_timeboundsOFF

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `0.08002502341402451`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.1832676827908` km, velocity `3.999999997894577e-08` km/s, mass `195.5406` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### global_mission_options/globalmissionoptions_MGAnDSMs_obj0

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.5406341552734` km, velocity `2.000000000335067e-08` km/s, mass `1218.1078` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

## journey_options

### journey_options/AerodynamicDrag_EarthOrbit_Maneuver

- Classification: `matched_snopt`.
- Repeatability: `stable`.
- Replay: `matched_snopt`; acceptable: `True`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_August2018.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `earth_magic_aerodynamic_drag_universe`: `testatron/universe/Earth_MAGIC.emtg_universe` -> `testatron/replacement_resources/Earth_MAGIC_AerodynamicDrag.emtg_universe` (review status: `provisional`). Historical universe file is unavailable in the repository and reachable Git history. This case-scoped candidate preserves the Earth/Moon/Sun model required by AerodynamicDrag_EarthOrbit_Maneuver.

#### Replay Mismatches
- None; all replay checks passed.

#### Refinement
- Classification: `matched_snopt`.
- Acceptable: `True`.
- IPOPT: exit `Optimal Solution Found.`, iterations `842`, terminal constraint violation `2.952470841881193e-07`.

### journey_options/EME_stageAfterArrival

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `snapier_multistage_spacecraft`: `docs/0_Users/tutorial/Tutorial_EMTG_Files/Config_Files/hardware_models/snapier_multistage.emtg_spacecraftopt` -> `testatron/HardwareModels/default_2stage.emtg_spacecraftopt` (review status: `provisional`). Historical spacecraft model is unavailable in the repository and reachable Git history. Both cases request an explicit stage transition, which requires the tracked two-stage model.

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `-5.844566758865902`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.496778845787` km, velocity `2.999999981767587e-08` km/s, mass `1335.3239` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EME_stageBeforeArrival

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `snapier_multistage_spacecraft`: `docs/0_Users/tutorial/Tutorial_EMTG_Files/Config_Files/hardware_models/snapier_multistage.emtg_spacecraftopt` -> `testatron/HardwareModels/default_2stage.emtg_spacecraftopt` (review status: `provisional`). Historical spacecraft model is unavailable in the repository and reachable Git history. Both cases request an explicit stage transition, which requires the tracked two-stage model.

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `-5.712162549301301`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.497507750988` km, velocity `3.000000070585429e-08` km/s, mass `1337.6408` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthMarsVenus_FlybyDeparture

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.6028728932142` km, velocity `2.999999892949745e-08` km/s, mass `3255.6811` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthMars_Depart2-2_Arrive2-2

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `engine_type`: `23` -> `15`. case-scoped runnable approximation: legacy NEXT TT11 high-thrust engine type is unsupported by the current schema
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `AEPS.ThrottleTable`. case-scoped runnable approximation paired with engine_type 15; AEPS performance is not equivalent to NEXT TT11
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2561213672161` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMarsBallisticRendezvous

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2758544385433` km, velocity `1.999999998947288e-08` km/s, mass `1465.5429` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMarsParkingOrbit

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3697527050972` km, velocity `3.000000003972048e-08` km/s, mass `1569.0688` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMarsParkingOrbit_PatchedConic

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3695791959763` km, velocity `2.000000165480742e-08` km/s, mass `1458.0095` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMarsPeri

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.409198641777` km, velocity `2.0000000766629e-08` km/s, mass `2969.0844` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMarsPeri_boundedAggFlightTime

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data
- Seed-bound violation retained: `{'index': 11, 'description': 'j0p0MGAnDSMs: virtual chemical fuel', 'value': -9.057998807162299e-05, 'lower_bound': 0.0, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 12, 'description': 'j0p0MGAnDSMs: virtual chemical oxidizer', 'value': -8.378648499626057e-05, 'lower_bound': 0.0, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 18, 'description': 'j1p0MGAnDSMsFreePointFreeDirectDeparture: event left state mass', 'value': 525.2001525263892, 'lower_bound': 1e-13, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 26, 'description': 'j1p0MGAnDSMsPeriapseFlybyIn: event left state mass', 'value': 525.2000608802921, 'lower_bound': 1e-13, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 28, 'description': 'j1p0MGAnDSMs: virtual chemical oxidizer', 'value': -8.529783920799587e-05, 'lower_bound': 0.0, 'upper_bound': 525.2}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.4303634762764` km, velocity `1.999999987845058e-08` km/s, mass `1783.162` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMarsPeri_boundedarrivaldate

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2936335355043` km, velocity `5.999999999617422e-08` km/s, mass `3100.6905` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMarsPeri_boundedtime

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.5014352798462` km, velocity `2.999999892949745e-08` km/s, mass `1983.5378` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMarsPeri_ovverrideproptype

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data
- Seed-bound violation retained: `{'index': 20, 'description': 'j1p0MGAnDSMsPeriapseFlybyIn: event left state r', 'value': 3390.0, 'lower_bound': 3689.9, 'upper_bound': 1003389.9}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.6689666807652` km, velocity `2.999999998420932e-08` km/s, mass `3100.6905` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMarsRendezvous

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2818981707096` km, velocity `2.999999981767587e-08` km/s, mass `1457.5879` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_ForcedInitialCoast

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data
- `LaunchVehicleKey`: `Falcon_9_FT_(RTLS)` -> `Falcon_Heavy_(Expendable)`. case-scoped public launch vehicle override: the implicit Falcon_9_FT_(RTLS) default has C3 upper bound 10, while the Falcon_Heavy_(Expendable) model supports the immutable SNOPT seed C3

#### Replay Mismatches
- `objective`: IPOPT - SNOPT = `-3.584258134736729e-08`.
- `total_deterministic_deltav`: IPOPT - SNOPT = `-3.584258134736729e-08`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.6749619543552` km, velocity `3.999999975690116e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_ForcedTerminalCoast

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data
- `LaunchVehicleKey`: `Falcon_9_FT_(RTLS)` -> `Falcon_Heavy_(Expendable)`. case-scoped public launch vehicle override: the implicit Falcon_9_FT_(RTLS) default has C3 upper bound 10, while the Falcon_Heavy_(Expendable) model supports the immutable SNOPT seed C3

#### Replay Mismatches
- `objective`: IPOPT - SNOPT = `-2.825088851743374e-08`.
- `total_deterministic_deltav`: IPOPT - SNOPT = `-2.825088851743374e-08`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.666931733489` km, velocity `3.000000003972048e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_JourneyEndDeltaV

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `objective`: IPOPT - SNOPT = `816786.0198252469`.
- `total_deterministic_deltav`: IPOPT - SNOPT = `816786.0198252469`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.5169925093651` km, velocity `3.000000070585429e-08` km/s, mass `2728.753` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_OverrideDutyCycle

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `objective`: IPOPT - SNOPT = `5.881098156059458`.
- `total_deterministic_deltav`: IPOPT - SNOPT = `5.881098156059458`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.5318495035172` km, velocity `3.000000070585429e-08` km/s, mass `458.7323000000001` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_coastphasematchpt

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3663713335991` km, velocity `3.000000003972048e-08` km/s, mass `1201.0047` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_dep1-2_atMars

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3695082962513` km, velocity `1.999999998947288e-08` km/s, mass `1583.1123` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_fixedEndMassInc

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.4649916291237` km, velocity `3.00000000119649e-08` km/s, mass `3255.6811` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_fixedStartingMassInc

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3810992240906` km, velocity `3.000000003972048e-08` km/s, mass `1932.6757` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_overrideTimesteps

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.4649916291237` km, velocity `3.00000000119649e-08` km/s, mass `3255.6811` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/EarthToMars_variableMassInc

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.1575116813183` km, velocity `3.999999999997929e-08` km/s, mass `1782.5838` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/LEO_to_GEO

- Classification: `matched_snopt`.
- Repeatability: `stable`.
- Replay: `matched_snopt`; acceptable: `True`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- None; all replay checks passed.

#### Refinement
- Classification: `matched_snopt`.
- Acceptable: `True`.
- IPOPT: exit `Optimal Solution Found.`, iterations `189`, terminal constraint violation `7.174401977165364e-12`.

### journey_options/default_PSBI_fixed_inertial_control

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Seed-bound violation retained: `{'index': 30, 'description': 'j0p0PSBI_Step1: virtual chemical fuel', 'value': -6.3024e-10, 'lower_bound': 0.0, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 42, 'description': 'j0p0PSBI_Step2: virtual chemical fuel', 'value': -6.8276e-10, 'lower_bound': 0.0, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 54, 'description': 'j0p0PSBI_Step3: virtual chemical fuel', 'value': -6.3024e-10, 'lower_bound': 0.0, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 66, 'description': 'j0p0PSBI_Step4: virtual chemical fuel', 'value': -5.7772e-10, 'lower_bound': 0.0, 'upper_bound': 525.2}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2340596020222` km, velocity `2.999999992869817e-08` km/s, mass `210.4961000000001` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/default_force_unit_magnitude_control

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1096353.867307531`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2500505447388` km, velocity `2.000000165480742e-08` km/s, mass `3100.6905` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/default_with_Jupiter_perturbation

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1084392.944849861`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.251690864563` km, velocity `3.000000070585429e-08` km/s, mass `3100.6905` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/default_with_Jupiter_perturbations_PSBI

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.1675433814526` km, velocity `3.999999997894577e-08` km/s, mass `637.6492000000001` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/default_zeroControl_intercept_MGALT

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `0.748325400509033`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3737015426159` km, velocity `2.999999999808711e-08` km/s, mass `1173.6623` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/default_zeroControl_intercept_PSBI

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2760172188282` km, velocity `2.999999892949745e-08` km/s, mass `3100.6905` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### journey_options/escape_from_KSC_FreePointDirectDeparture_along_velocity_vector

- Classification: `matched_snopt`.
- Repeatability: `stable`.
- Replay: `matched_snopt`; acceptable: `True`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 5 does not use throttle-table performance data

#### Replay Mismatches
- None; all replay checks passed.

#### Refinement
- Classification: `matched_snopt`.
- Acceptable: `True`.
- IPOPT: exit `Optimal Solution Found.`, iterations `18706`, terminal constraint violation `1.852854594052186e-08`.

### journey_options/park_to_SOI_FBLT

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- No case-specific runtime option changes.
- Replacement resources:
  - `earth_magic_gateway_universe`: `testatron/universe/Earth_MAGIC.emtg_universe` -> `testatron/replacement_resources/Earth_MAGIC_Park.emtg_universe` (review status: `provisional`). The pinned DSG receding_horiz_3189_1burnApo_DiffCorr_15yr.bsp SPK provides target -60000 throughout the required reference epoch. This candidate supplies the contiguous Moon through Neptune menu required by Park's third-body perturbation lists.
  - `earth_magic_gateway_universe`: `testatron/universe/Earth_MAGIC.emtg_universe` -> `testatron/replacement_resources/Earth_MAGIC_Park.emtg_universe` (review status: `provisional`). The pinned DSG receding_horiz_3189_1burnApo_DiffCorr_15yr.bsp SPK provides target -60000 throughout the required reference epoch. This candidate supplies the contiguous Moon through Neptune menu required by Park's third-body perturbation lists.
  - `earth_magic_gateway_universe`: `testatron/universe/Earth_MAGIC.emtg_universe` -> `testatron/replacement_resources/Earth_MAGIC_Park.emtg_universe` (review status: `provisional`). The pinned DSG receding_horiz_3189_1burnApo_DiffCorr_15yr.bsp SPK provides target -60000 throughout the required reference epoch. This candidate supplies the contiguous Moon through Neptune menu required by Park's third-body perturbation lists.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `8623.18787822` km, velocity `9.73615916` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

## output_options

### output_options/outputoptions_frameICRF

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.6177838146687` km, velocity `1.999999987845058e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### output_options/outputoptions_frameJ2000BCF

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `98.72002953290939` km, velocity `1.999999998947288e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### output_options/outputoptions_frameTODBCF

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `98.72002953290939` km, velocity `1.999999998947288e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### output_options/outputoptions_frameTODBCI

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.6177838146687` km, velocity `2.000000165480742e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### output_options/outputoptions_outputjourneywaittimes

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `111.9490861818194` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

## physics_options

### physics_options/Earth_to_SmallBody_SAM

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `SPICE_reference_frame_kernel`: `pck00010.tpc` -> `codes_300ast_20100725.tf`. case-scoped CODES frame kernel required for the Lacadiera ephemeris frame
- Seed-bound violation retained: `{'index': 263, 'description': 'j1p0MGALTFreePointLTRendezvous: event left state SMA', 'value': 374.9999999835351, 'lower_bound': 374.9999999999999, 'upper_bound': 375.0000000000001}`.
- Seed-bound violation retained: `{'index': 264, 'description': 'j1p0MGALTFreePointLTRendezvous: event left state ECC', 'value': 9.64390610182e-09, 'lower_bound': 9.9999e-09, 'upper_bound': 1.00001e-08}`.
- Seed-bound violation retained: `{'index': 265, 'description': 'j1p0MGALTFreePointLTRendezvous: event left state INC', 'value': 1.5707963273159664, 'lower_bound': 1.5707963267948948, 'upper_bound': 1.5707963267948981}`.
- Seed-bound violation retained: `{'index': 266, 'description': 'j1p0MGALTFreePointLTRendezvous: event left state RAAN', 'value': -0.5235987737175757, 'lower_bound': -0.5235987755983006, 'upper_bound': -0.5235987755982972}`.
- Seed-bound violation retained: `{'index': 267, 'description': 'j1p0MGALTFreePointLTRendezvous: event left state AOP', 'value': 8.984844334e-11, 'lower_bound': -1.74533e-15, 'upper_bound': 1.74533e-15}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `119.723630040884` km, velocity `9.070000000832579e-06` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### physics_options/physicsoptions_SPICEphem

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.6177102327347` km, velocity `1.999999987845058e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### physics_options/physicsoptions_add3rdbody

- Classification: `matched_snopt`.
- Repeatability: `stable`.
- Replay: `matched_snopt`; acceptable: `True`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- None; all replay checks passed.

#### Refinement
- Classification: `matched_snopt`.
- Acceptable: `True`.
- IPOPT: exit `Optimal Solution Found.`, iterations `5`, terminal constraint violation `5.176223891833446e-10`.

### physics_options/physicsoptions_addJ2

- Classification: `matched_snopt`.
- Repeatability: `stable`.
- Replay: `matched_snopt`; acceptable: `True`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- None; all replay checks passed.

#### Refinement
- Classification: `matched_snopt`.
- Acceptable: `True`.
- IPOPT: exit `Optimal Solution Found.`, iterations `5`, terminal constraint violation `1.121377090479343e-07`.

### physics_options/physicsoptions_addSRP

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.6177838146687` km, velocity `2.000000165480742e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### physics_options/physicsoptions_periapseCartesian

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data
- Seed-bound violation retained: `{'index': 12, 'description': 'j0p0MGAnDSMs: virtual chemical oxidizer', 'value': -1.667109706598963e-05, 'lower_bound': 0.0, 'upper_bound': 5000.0}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.8611271455884` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### physics_options/physicsoptions_periapseIncomingBplane

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data
- Seed-bound violation retained: `{'index': 11, 'description': 'j0p0MGAnDSMs: virtual chemical fuel', 'value': -2.031035147633358e-05, 'lower_bound': 0.0, 'upper_bound': 5000.0}`.
- Seed-bound violation retained: `{'index': 12, 'description': 'j0p0MGAnDSMs: virtual chemical oxidizer', 'value': -1.526992209070614e-05, 'lower_bound': 0.0, 'upper_bound': 5000.0}`.
- Seed-bound violation retained: `{'index': 25, 'description': 'j1p0CoastPhasePeriapseFlybyIn: event left state TAin', 'value': -2.163554463239e-08, 'lower_bound': -1.74533e-15, 'upper_bound': 1.74533e-15}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.8611448705196` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### physics_options/physicsoptions_periapseSphericalAZFPA

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.8611356541514` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### physics_options/physicsoptions_periapseSphericalRADEC

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.4052376151085` km, velocity `3.000000026176508e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### physics_options/physicsoptions_shortspline

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 6 does not use throttle-table performance data

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.6178274452686` km, velocity `2.999999892949745e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

## script_constraint_tests

### script_constraint_tests/EVM_MGAnDSMs_bEnd_but_not_pEnd_maneuverMagnitude

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.5102326571941` km, velocity `3.000000003972048e-08` km/s, mass `2531.6885` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EVM_MGAnDSMs_flybyDeparture_distance_from_Earth

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.4983520060778` km, velocity `3.000000026176508e-08` km/s, mass `1168.6778` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EVM_MGAnDSMs_pEnd_and_Bend_maneuverMagnitude

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- Seed-bound violation retained: `{'index': 9, 'description': 'j0p0MGAnDSMs: virtual chemical fuel', 'value': -0.00013156818509714587, 'lower_bound': 0.0, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 10, 'description': 'j0p0MGAnDSMs: virtual chemical oxidizer', 'value': -0.00012170056417831655, 'lower_bound': 0.0, 'upper_bound': 525.2}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.5104273855686` km, velocity `3.000000003972048e-08` km/s, mass `2528.8206` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EVM_MGAnDSMs_pEndbutnotBend_maneuverMagnitude

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.5103291273117` km, velocity `3.999999997894577e-08` km/s, mass `2566.0986` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EVM_PSBI_pEnd_bpt

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- Seed-bound violation retained: `{'index': 19, 'description': 'j0p0PSBI_Step0: virtual electric propellant', 'value': -2.3043821287967e-07, 'lower_bound': 0.0, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 269, 'description': 'j0p1PSBI_Step0: virtual electric propellant', 'value': -4.795847997168e-08, 'lower_bound': 0.0, 'upper_bound': 525.2}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `106.9757013618946` km, velocity `5.000000002919336e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EVM_PSBI_pEnd_distance

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- Seed-bound violation retained: `{'index': 29, 'description': 'j0p0PSBI_Step1: left state mass', 'value': 525.200000125157, 'lower_bound': 1e-13, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 31, 'description': 'j0p0PSBI_Step1: virtual electric propellant', 'value': -1.2494703105598e-07, 'lower_bound': 0.0, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 41, 'description': 'j0p0PSBI_Step2: left state mass', 'value': 525.2000001678647, 'lower_bound': 1e-13, 'upper_bound': 525.2}`.
- Seed-bound violation retained: `{'index': 43, 'description': 'j0p0PSBI_Step2: virtual electric propellant', 'value': -1.676546873951e-07, 'lower_bound': 0.0, 'upper_bound': 525.2}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.0065767467022` km, velocity `3.999999999282355e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EVM_pEndRRP_arrival

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `LaunchVehicleKey`: `Falcon_9_FT_(RTLS)` -> `Falcon_Heavy_(Expendable)`. case-scoped public launch vehicle override: the implicit Falcon_9_FT_(RTLS) default has C3 upper bound 10, while the Falcon_Heavy_(Expendable) model supports the immutable SNOPT seed C3

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `3.073840465050992e-06`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.4805524796247` km, velocity `3.000000070585429e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EVM_pEnd_distance

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `58.29723219582067`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2865167558193` km, velocity `3.000000003972048e-08` km/s, mass `3100.6905` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EarthMarsLikePointFreePointChemRendezvous_RPRconjunction

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `engine_type`: `6` -> `10`. case-scoped runnable approximation: engine_type 6 has a 2.7 kW minimum, while the immutable SNOPT seed requires thrust at lower available power; engine_type 10 supports the seeded power range
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `LaunchVehicleKey`: `Falcon_9_FT_(RTLS)` -> `Falcon_Heavy_(Expendable)`. case-scoped public launch vehicle override: the implicit Falcon_9_FT_(RTLS) default has C3 upper bound 10, while the Falcon_Heavy_(Expendable) model supports the immutable SNOPT seed C3

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `0.2380084357562047`.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EarthMarsLikePointFreePointChemRendezvous_RRPconjunction

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `engine_type`: `6` -> `10`. case-scoped runnable approximation: engine_type 6 has a 2.7 kW minimum, while the immutable SNOPT seed requires thrust at lower available power; engine_type 10 supports the seeded power range
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `LaunchVehicleKey`: `Falcon_9_FT_(RTLS)` -> `Falcon_Heavy_(Expendable)`. case-scoped public launch vehicle override: the implicit Falcon_9_FT_(RTLS) default has C3 upper bound 10, while the Falcon_Heavy_(Expendable) model supports the immutable SNOPT seed C3

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `0.2474768568872761`.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EarthMars_RPRangle_force_conjunction

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `engine_type`: `6` -> `10`. case-scoped runnable approximation: engine_type 6 has a 2.7 kW minimum, while the immutable SNOPT seed requires thrust at lower available power; engine_type 10 supports the seeded power range
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- `LaunchVehicleKey`: `Falcon_9_FT_(RTLS)` -> `Falcon_Heavy_(Expendable)`. case-scoped public launch vehicle override: the implicit Falcon_9_FT_(RTLS) default has C3 upper bound 10, while the Falcon_Heavy_(Expendable) model supports the immutable SNOPT seed C3

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `10.99681583056462`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `106.9934435486794` km, velocity `5.000000000143778e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/EarthMars_RRPangle_force_conjunction

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `201808.9776132088`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.1078767478466` km, velocity `4.999999991817106e-08` km/s, mass `802.1884` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### script_constraint_tests/ShuttlePark_to_Molniya

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `matched_snopt`; acceptable: `True`.

#### Case-Specific Runtime Changes
- No case-specific runtime option changes.
- Seed-bound violation retained: `{'index': 12, 'description': 'j0p0MGAnDSMsFreePointDirectInsertion: virtual chemical oxidizer', 'value': -0.0020303132712711108, 'lower_bound': 0.0, 'upper_bound': 23077.0}`.

#### Replay Mismatches
- None; all replay checks passed.

#### Refinement
- Classification: `mismatch_snopt`.
- Acceptable: `False`.
- IPOPT: exit `Optimal Solution Found.`, iterations `25`, terminal constraint violation `6.493336138871575e-06`.

## solver_options

### solver_options/solveroptions_ACEfeasibility

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 3 does not use throttle-table performance data

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `3.243308105416176e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.209357380867` km, velocity `2.999999999808711e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### solver_options/solveroptions_MBH_RNG_seed

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 3 does not use throttle-table performance data

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `3.256483167568547e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2093347609043` km, velocity `2.999999999808711e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### solver_options/solveroptions_NLPstepsub1

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 3 does not use throttle-table performance data

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `3.253631518651545e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2093380689621` km, velocity `4.000000000670134e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### solver_options/solveroptions_noChaperone

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 3 does not use throttle-table performance data

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `3.253631518651545e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2093380689621` km, velocity `4.000000000670134e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### solver_options/solveroptions_skip1stNLP

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `ThrottleTableFile`: `NEXT_TT11_NewFrontiers_EOL_1_3_2017.ThrottleTable` -> `empty.ThrottleTable`. engine_type 3 does not use throttle-table performance data

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `3.256483167568547e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2093347609043` km, velocity `2.999999999808711e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

## spacecraft_options

### spacecraft_options/Earth_to_SmallBody_SAM_RTG

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `SPICE_reference_frame_kernel`: `pck00010.tpc` -> `codes_300ast_20100725.tf`. case-scoped CODES frame kernel required for the Lacadiera ephemeris frame

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `150.7916434407234` km, velocity `1.094000000012585e-05` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/Earth_to_SmallBody_SAM_solar_power

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `SPICE_reference_frame_kernel`: `pck00010.tpc` -> `codes_300ast_20100725.tf`. case-scoped CODES frame kernel required for the Lacadiera ephemeris frame

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.107585945765322e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `139.0737041980028` km, velocity `9.490000000056398e-06` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/default_SCfile_PM

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `default.emtg_launchvehicleopt` -> `default.emtg_launchvehicleopt`. tracked public performance library for LaunchVehicleKey Falcon_9_FT_(RTLS)
- Replacement resources:
  - `multistage_spacecraft_file`: `HardwareModels/spacecraft_LT_multiStage_spacecraftFile.emtg_spacecraftopt` -> `testatron/HardwareModels/default_2stage.emtg_spacecraftopt` (review status: `provisional`). Historical spacecraft model is unavailable in the repository and reachable Git history. This case requires a two-stage model.

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.896152936552691`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.1491023302078` km, velocity `3.999999997894577e-08` km/s, mass `410.7101` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraft_LT_multiStage_spacecraftFile

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `LaunchVehicleKey`: `Falcon_9_FT_(RTLS)` -> `Atlas_V_401`. case-scoped public launch vehicle override: at the immutable SNOPT seed C3 25, the Atlas_V_401 curve provides the baseline pre-multiplier launch mass of approximately 1632.015 kg
- `SpacecraftOptionsFile stage-one power profile`: `5 kW polynomial power model` -> `7kWarray_800Wbus`. case-scoped power-profile replacement: the immutable baseline's stage-one available-power schedule matches the tracked 7kWarray_800Wbus solar array and bus-load model
- Replacement resources:
  - `multistage_spacecraft_file_public_hardware`: `docs/0_Users/tutorial/Tutorial_EMTG_Files/Config_Files/hardware_models/spacecraft_LT_multiStage_spacecraftFile.emtg_spacecraftopt` -> `testatron/HardwareModels/default_2stage.emtg_spacecraftopt` (review status: `provisional`). The legacy launch-library mapping selects the public tutorial hardware root. This case requests stage_after_departure and therefore requires a two-stage model.

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `0.9374315404417182`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.1768368929625` km, velocity `5.000000002919336e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraft_LT_powerFile

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `ElectricPropulsionSystemKey`: `AEPS_PolyFit_HTandHI` -> `NEXTC_PolyFit_HT`. case-scoped runnable probe: NEXTC_PolyFit_HT supports lower power than the staged AEPS polynomial model
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `PowerSystemsLibraryFile`: `default.emtg_powersystemsopt` -> `default.emtg_powersystemsopt`. tracked default library staged with public NLSII hardware; selected keys: 7kWarray_800Wbus
- `PropulsionSystemsLibraryFile`: `default.emtg_propulsionsystemopt` -> `default.emtg_propulsionsystemopt`. tracked default library staged with public NLSII hardware; selected keys: NEXTC_PolyFit_HT, DefaultChemicalPropulsionSystem

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.970004274458945`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.0986922606826` km, velocity `5.999999999617422e-08` km/s, mass `1334.5307` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraft_LT_propFile

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `ElectricPropulsionSystemKey`: `AEPS_PolyFit_HTandHI` -> `NEXTC_PolyFit_HT`. case-scoped runnable probe: NEXTC_PolyFit_HT supports lower power than the staged AEPS polynomial model
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- `PowerSystemsLibraryFile`: `default.emtg_powersystemsopt` -> `default.emtg_powersystemsopt`. tracked default library staged with public NLSII hardware; selected keys: 5kW_basic
- `PropulsionSystemsLibraryFile`: `default.emtg_propulsionsystemopt` -> `default.emtg_propulsionsystemopt`. tracked default library staged with public NLSII hardware; selected keys: NEXTC_PolyFit_HT, DefaultChemicalPropulsionSystem

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.593846000416175`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.0986922606826` km, velocity `5.999999999617422e-08` km/s, mass `1334.5307` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraft_LT_spacecraftFile

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `spacecraft_file`: `docs/0_Users/tutorial/Tutorial_EMTG_Files/Config_Files/hardware_models/spacecraft_LT_spacecraftFile.emtg_spacecraftopt` -> `testatron/HardwareModels/default_2stage.emtg_spacecraftopt` (review status: `provisional`). The single-stage candidate causes EMTG to terminate before configuration completes. This candidate's first stage is the already runtime-validated schema used by the paired multi-stage file case; its second stage is unused because this case requests no stage transition.

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `0.5991802756437867`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.0986922606826` km, velocity `5.999999999617422e-08` km/s, mass `1334.5307` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_Chem_TrackACSProp

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `6.00000000239298e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_Chemmargin

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.4780078530312` km, velocity `2.999999981767587e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_Emargin

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.792500403663411e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.000000000143778e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_ThrotMaxThrusters

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.709999196217396e-10`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.999999999617422e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_ThrotMinThrusters

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.745569354147605e-10`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.000000000143778e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_ThrotSharpness

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.79265098654291e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.999999999617422e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_TrackACSProp

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.818157076005633e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.999999999617422e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_eng0

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.000000000143778e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_eng3

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `2.397590070923883e-09`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.000000000143778e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_eng3_polyArray

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `4.159034167061648e-08`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.999999999617422e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_eng3_powmod1

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.004650117542027e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.999999999617422e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_eng5

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.000000000143778e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_maxEprop

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.792500403663411e-07`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.000000000143778e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_powdecay

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `1.123531268021338e-09`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.999999999964367e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LT_powsrc0

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `7.454747930069061e-10`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3209239691496` km, velocity `5.000000000143778e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LV_FixedInitMass

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.5406320691109` km, velocity `1.999999987845058e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_LVmargin

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.7312110364437` km, velocity `1.000000082740371e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_chemPropTankConstr

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.7312090992928` km, velocity `1.999999998947288e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_dutyCycle

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Seed-bound violation retained: `{'index': 30, 'description': 'j0p0PSFB_Step1: virtual chemical fuel', 'value': -8e-09, 'lower_bound': 0.0, 'upper_bound': 5000.0}`.
- Seed-bound violation retained: `{'index': 42, 'description': 'j0p0PSFB_Step2: virtual chemical fuel', 'value': -7.5e-09, 'lower_bound': 0.0, 'upper_bound': 5000.0}`.
- Seed-bound violation retained: `{'index': 54, 'description': 'j0p0PSFB_Step3: virtual chemical fuel', 'value': -7e-09, 'lower_bound': 0.0, 'upper_bound': 5000.0}`.
- Seed-bound violation retained: `{'index': 66, 'description': 'j0p0PSFB_Step4: virtual chemical fuel', 'value': -6.5e-09, 'lower_bound': 0.0, 'upper_bound': 5000.0}`.
- Seed-bound violation retained: `{'index': 78, 'description': 'j0p0PSFB_Step5: virtual chemical fuel', 'value': -6e-09, 'lower_bound': 0.0, 'upper_bound': 5000.0}`.
- Seed-bound violation retained: `{'index': 90, 'description': 'j0p0PSFB_Step6: virtual chemical fuel', 'value': -5.5e-09, 'lower_bound': 0.0, 'upper_bound': 5000.0}`.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2154186666012` km, velocity `2.999999999808711e-08` km/s, mass `1539.3035` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_dutyCycleReal

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2148047685623` km, velocity `2.999999999808711e-08` km/s, mass `1538.9123` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_maxChemOx

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.7312090992928` km, velocity `1.999999998947288e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_powMargin

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.7197967320681` km, velocity `1.999999987845058e-08` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### spacecraft_options/spacecraftoptions_varinitmass

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.5884216427803` km, velocity `2.000000000335067e-08` km/s, mass `1050.4468` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

## state_representation_tests

### state_representation_tests/FreePointArrival_IncomingBplaneRpTA_testatron

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_August2018.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `sun_saturn_orientation_arrival_universe`: `testatron/universe/Sun_SaturnOrientation.emtg_universe` -> `testatron/replacement_resources/Sun_SaturnOrientation_StateRepresentation_Arrival.emtg_universe` (review status: `provisional`). Historical universe file is unavailable in the repository and reachable Git history. Body 13 retains the reconstructed Saturn ephemeris and constants but is named Saturn so the current boundary-event writer emits the immutable baseline identity Saturn_BE rather than Saturn_BE_BE. The separate Saturn-centered journey requires pinned sat441.bsp for physical Saturn and satellite ephemerides.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `168.5399384498596` km, velocity `0.0006713799999999992` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### state_representation_tests/FreePointArrival_OutgoingBplaneRpTA_testatron

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_August2018.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `sun_saturn_orientation_arrival_universe`: `testatron/universe/Sun_SaturnOrientation.emtg_universe` -> `testatron/replacement_resources/Sun_SaturnOrientation_StateRepresentation_Arrival.emtg_universe` (review status: `provisional`). Historical universe file is unavailable in the repository and reachable Git history. Body 13 retains the reconstructed Saturn ephemeris and constants but is named Saturn so the current boundary-event writer emits the immutable baseline identity Saturn_BE rather than Saturn_BE_BE. The separate Saturn-centered journey requires pinned sat441.bsp for physical Saturn and satellite ephemerides.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `168.373881816864` km, velocity `0.0006706200000001772` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### state_representation_tests/FreePointDeparture_IncomingBplaneRpTA_testatron

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_August2018.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `sun_saturn_orientation_departure_universe`: `testatron/universe/Sun_SaturnOrientation.emtg_universe` -> `testatron/replacement_resources/Sun_SaturnOrientation_StateRepresentation.emtg_universe` (review status: `provisional`). Historical universe file is unavailable in the repository and reachable Git history. This case-scoped candidate preserves the one-journey state-representation departure cases' required body indices and ICRF/TrueOfDate body-orientation inputs.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `103.28635950014` km, velocity `1.200000028234172e-07` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### state_representation_tests/FreePointDeparture_OutgoingBplaneRpTA_testatron

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_August2018.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `sun_saturn_orientation_departure_universe`: `testatron/universe/Sun_SaturnOrientation.emtg_universe` -> `testatron/replacement_resources/Sun_SaturnOrientation_StateRepresentation.emtg_universe` (review status: `provisional`). Historical universe file is unavailable in the repository and reachable Git history. This case-scoped candidate preserves the one-journey state-representation departure cases' required body indices and ICRF/TrueOfDate body-orientation inputs.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `103.28635950014` km, velocity `1.200000028234172e-07` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### state_representation_tests/PeriapseArrival_IncomingBplaneRpTA_testatron

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_August2018.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `sun_saturn_orientation_arrival_universe`: `testatron/universe/Sun_SaturnOrientation.emtg_universe` -> `testatron/replacement_resources/Sun_SaturnOrientation_StateRepresentation_Arrival.emtg_universe` (review status: `provisional`). Historical universe file is unavailable in the repository and reachable Git history. Body 13 retains the reconstructed Saturn ephemeris and constants but is named Saturn so the current boundary-event writer emits the immutable baseline identity Saturn_BE rather than Saturn_BE_BE. The separate Saturn-centered journey requires pinned sat441.bsp for physical Saturn and satellite ephemerides.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `171.2910454273224` km, velocity `0.0006840000000001289` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### state_representation_tests/PeriapseArrival_OutgoingBplaneRpTA_testatron

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_August2018.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved
- Replacement resources:
  - `sun_saturn_orientation_arrival_universe`: `testatron/universe/Sun_SaturnOrientation.emtg_universe` -> `testatron/replacement_resources/Sun_SaturnOrientation_StateRepresentation_Arrival.emtg_universe` (review status: `provisional`). Historical universe file is unavailable in the repository and reachable Git history. Body 13 retains the reconstructed Saturn ephemeris and constants but is named Saturn so the current boundary-event writer emits the immutable baseline identity Saturn_BE rather than Saturn_BE_BE. The separate Saturn-centered journey requires pinned sat441.bsp for physical Saturn and satellite ephemerides.

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `171.5424246788025` km, velocity `0.0006851600000001845` km/s, mass `0` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

## transcription_tests

### transcription_tests/CoastPhase_EMintercept

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.3374776244164` km, velocity `2.999999892949745e-08` km/s, mass `1507.8748` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### transcription_tests/FBLT_EMintercept

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.0986621994525` km, velocity `5.999999999617422e-08` km/s, mass `1335.3429` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### transcription_tests/MGALT_EMintercept

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `total_deterministic_deltav`: IPOPT - SNOPT = `0.5991803502593807`.
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.0986922606826` km, velocity `5.999999999617422e-08` km/s, mass `1334.5307` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### transcription_tests/MGAnDSMs_EMintercept

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `106.9449155777693` km, velocity `5.999999999617422e-08` km/s, mass `1423.8908` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### transcription_tests/PSBI_EMintercept

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2140486836433` km, velocity `3.000000070585429e-08` km/s, mass `1530.3205` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### transcription_tests/PSFB_EMintercept

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.2140486836433` km, velocity `3.000000070585429e-08` km/s, mass `1530.3205` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.

### transcription_tests/SundmanCoastPhase_EMintercept

- Classification: `mismatch_snopt`.
- Repeatability: `stable`.
- Replay: `mismatch_snopt`; acceptable: `False`.

#### Case-Specific Runtime Changes
- `LaunchVehicleLibraryFile`: `NLSII_April2017.emtg_launchvehicleopt` -> `LaunchVehicles_PubliclyDistributable_NLSII.emtg_launchvehicleopt`. public replacement library; LaunchVehicleKey preserved

#### Replay Mismatches
- `journey_endpoints`: maximum absolute deltas: epoch `0` days, position `107.4574293792248` km, velocity `1.999999987845058e-08` km/s, mass `1640.9042` kg.

#### Refinement
- Not run because the replay comparison was not acceptable.
