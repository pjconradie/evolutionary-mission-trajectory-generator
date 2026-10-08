# Baselining Commands

Run these from the repository root. `baselining_case` uses the supported Docker-backed pytest launcher and replaces only the selected case's evidence root. The immutable source pairs under `testatron/tests` are never modified.

## How To Use This File

1. Open a terminal and change to the repository root.
2. Copy the entire function block below, paste it into that terminal, and press Enter. This defines `baselining_case` and `promote_if_matched` for that terminal session only.
3. Copy and run one `baselining_case 'group/case'` line from the numbered lists. Do not paste a whole group unless you intend to run every listed case.
4. Read that case's `result.json` and `repeatability.json` under `testatron/ipopt/tests/tests/baselining/` before running the next case.
5. Run `promote_if_matched 'group/case'` only after the case is stable `matched_snopt` and manually approved in the decision log. Add `--replace-promoted` only when intentionally refreshing an existing curated package.

For example, after pasting the function block, run case 3 with:

```zsh
baselining_case 'global_mission_options/globalmissionoptions_MGALT_constrDryMass'
```

```zsh
baselining_case() {
	EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/tests" \
	pytest tests/integration/test_baselining.py -q \
		-k baselining_cli_writes_fixed_mirrored_layout \
		--baselining-filter "$1"
}

promote_if_matched() {
	local case_id="$1"
	shift
	python testatron/ipopt_characterization.py \
		--promote-baseline "$case_id" \
		--approve-baseline \
		--output-root "$PWD/testatron/ipopt/tests/tests" \
		"$@"
}
```

Run each command in order. Run the promotion command only after that case has stable `matched_snopt` evidence and manual approval; it refuses all other classifications.

## 1-28: `global_mission_options`

```zsh
baselining_case 'global_mission_options/globalmissionoptions_MGALT_DLAbounds'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_RLAbounds'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_constrDryMass'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_constrFinalMass'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_includeInitialImpulse'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_numtimesteps'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj0'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj1'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj14'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj15'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj17'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj18'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj19'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj20'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj22'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj23'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj3'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj4'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj5'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj8'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_obj9'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_postFlybyCoast'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_postLaunchTCM'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_postlaunchCoast'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_preFlybyCoast'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_preFlybyTCM'
baselining_case 'global_mission_options/globalmissionoptions_MGALT_timeboundsOFF'
baselining_case 'global_mission_options/globalmissionoptions_MGAnDSMs_obj0'
```

## 29-61: `journey_options`

```zsh
baselining_case 'journey_options/AerodynamicDrag_EarthOrbit_Maneuver'
baselining_case 'journey_options/EME_stageAfterArrival'
baselining_case 'journey_options/EME_stageBeforeArrival'
baselining_case 'journey_options/EarthMarsVenus_FlybyDeparture'
baselining_case 'journey_options/EarthMars_Depart2-2_Arrive2-2'
baselining_case 'journey_options/EarthToMarsBallisticRendezvous'
baselining_case 'journey_options/EarthToMarsParkingOrbit'
baselining_case 'journey_options/EarthToMarsParkingOrbit_PatchedConic'
baselining_case 'journey_options/EarthToMarsPeri'
baselining_case 'journey_options/EarthToMarsPeri_boundedAggFlightTime'
baselining_case 'journey_options/EarthToMarsPeri_boundedarrivaldate'
baselining_case 'journey_options/EarthToMarsPeri_boundedtime'
baselining_case 'journey_options/EarthToMarsPeri_ovverrideproptype'
baselining_case 'journey_options/EarthToMarsRendezvous'
baselining_case 'journey_options/EarthToMars_ForcedInitialCoast'
baselining_case 'journey_options/EarthToMars_ForcedTerminalCoast'
baselining_case 'journey_options/EarthToMars_JourneyEndDeltaV'
baselining_case 'journey_options/EarthToMars_OverrideDutyCycle'
baselining_case 'journey_options/EarthToMars_coastphasematchpt'
baselining_case 'journey_options/EarthToMars_dep1-2_atMars'
baselining_case 'journey_options/EarthToMars_fixedEndMassInc'
baselining_case 'journey_options/EarthToMars_fixedStartingMassInc'
baselining_case 'journey_options/EarthToMars_overrideTimesteps'
baselining_case 'journey_options/EarthToMars_variableMassInc'
baselining_case 'journey_options/LEO_to_GEO'
baselining_case 'journey_options/default_PSBI_fixed_inertial_control'
baselining_case 'journey_options/default_force_unit_magnitude_control'
baselining_case 'journey_options/default_with_Jupiter_perturbation'
baselining_case 'journey_options/default_with_Jupiter_perturbations_PSBI'
baselining_case 'journey_options/default_zeroControl_intercept_MGALT'
baselining_case 'journey_options/default_zeroControl_intercept_PSBI'
baselining_case 'journey_options/escape_from_KSC_FreePointDirectDeparture_along_velocity_vector'
baselining_case 'journey_options/park_to_SOI_FBLT'
```

## 62-66: `output_options`

```zsh
baselining_case 'output_options/outputoptions_frameICRF'
baselining_case 'output_options/outputoptions_frameJ2000BCF'
baselining_case 'output_options/outputoptions_frameTODBCF'
baselining_case 'output_options/outputoptions_frameTODBCI'
baselining_case 'output_options/outputoptions_outputjourneywaittimes'
```

## 67-76: `physics_options`

```zsh
baselining_case 'physics_options/Earth_to_SmallBody_SAM'
baselining_case 'physics_options/physicsoptions_SPICEphem'
baselining_case 'physics_options/physicsoptions_add3rdbody'
baselining_case 'physics_options/physicsoptions_addJ2'
baselining_case 'physics_options/physicsoptions_addSRP'
baselining_case 'physics_options/physicsoptions_periapseCartesian'
baselining_case 'physics_options/physicsoptions_periapseIncomingBplane'
baselining_case 'physics_options/physicsoptions_periapseSphericalAZFPA'
baselining_case 'physics_options/physicsoptions_periapseSphericalRADEC'
baselining_case 'physics_options/physicsoptions_shortspline'
```

## 77-89: `script_constraint_tests`

```zsh
baselining_case 'script_constraint_tests/EVM_MGAnDSMs_bEnd_but_not_pEnd_maneuverMagnitude'
baselining_case 'script_constraint_tests/EVM_MGAnDSMs_flybyDeparture_distance_from_Earth'
baselining_case 'script_constraint_tests/EVM_MGAnDSMs_pEnd_and_Bend_maneuverMagnitude'
baselining_case 'script_constraint_tests/EVM_MGAnDSMs_pEndbutnotBend_maneuverMagnitude'
baselining_case 'script_constraint_tests/EVM_PSBI_pEnd_bpt'
baselining_case 'script_constraint_tests/EVM_PSBI_pEnd_distance'
baselining_case 'script_constraint_tests/EVM_pEndRRP_arrival'
baselining_case 'script_constraint_tests/EVM_pEnd_distance'
baselining_case 'script_constraint_tests/EarthMarsLikePointFreePointChemRendezvous_RPRconjunction'
baselining_case 'script_constraint_tests/EarthMarsLikePointFreePointChemRendezvous_RRPconjunction'
baselining_case 'script_constraint_tests/EarthMars_RPRangle_force_conjunction'
baselining_case 'script_constraint_tests/EarthMars_RRPangle_force_conjunction'
baselining_case 'script_constraint_tests/ShuttlePark_to_Molniya'
```

## 90-94: `solver_options`

```zsh
baselining_case 'solver_options/solveroptions_ACEfeasibility'
baselining_case 'solver_options/solveroptions_MBH_RNG_seed'
baselining_case 'solver_options/solveroptions_NLPstepsub1'
baselining_case 'solver_options/solveroptions_noChaperone'
baselining_case 'solver_options/solveroptions_skip1stNLP'
```

## 95-124: `spacecraft_options`

```zsh
baselining_case 'spacecraft_options/Earth_to_SmallBody_SAM_RTG'
baselining_case 'spacecraft_options/Earth_to_SmallBody_SAM_solar_power'
baselining_case 'spacecraft_options/default_SCfile_PM'
baselining_case 'spacecraft_options/spacecraft_LT_multiStage_spacecraftFile'
baselining_case 'spacecraft_options/spacecraft_LT_powerFile'
baselining_case 'spacecraft_options/spacecraft_LT_propFile'
baselining_case 'spacecraft_options/spacecraft_LT_spacecraftFile'
baselining_case 'spacecraft_options/spacecraftoptions_Chem_TrackACSProp'
baselining_case 'spacecraft_options/spacecraftoptions_Chemmargin'
baselining_case 'spacecraft_options/spacecraftoptions_LT_Emargin'
baselining_case 'spacecraft_options/spacecraftoptions_LT_ThrotMaxThrusters'
baselining_case 'spacecraft_options/spacecraftoptions_LT_ThrotMinThrusters'
baselining_case 'spacecraft_options/spacecraftoptions_LT_ThrotSharpness'
baselining_case 'spacecraft_options/spacecraftoptions_LT_TrackACSProp'
baselining_case 'spacecraft_options/spacecraftoptions_LT_eng0'
baselining_case 'spacecraft_options/spacecraftoptions_LT_eng3'
baselining_case 'spacecraft_options/spacecraftoptions_LT_eng3_polyArray'
baselining_case 'spacecraft_options/spacecraftoptions_LT_eng3_powmod1'
baselining_case 'spacecraft_options/spacecraftoptions_LT_eng5'
baselining_case 'spacecraft_options/spacecraftoptions_LT_maxEprop'
baselining_case 'spacecraft_options/spacecraftoptions_LT_powdecay'
baselining_case 'spacecraft_options/spacecraftoptions_LT_powsrc0'
baselining_case 'spacecraft_options/spacecraftoptions_LV_FixedInitMass'
baselining_case 'spacecraft_options/spacecraftoptions_LVmargin'
baselining_case 'spacecraft_options/spacecraftoptions_chemPropTankConstr'
baselining_case 'spacecraft_options/spacecraftoptions_dutyCycle'
baselining_case 'spacecraft_options/spacecraftoptions_dutyCycleReal'
baselining_case 'spacecraft_options/spacecraftoptions_maxChemOx'
baselining_case 'spacecraft_options/spacecraftoptions_powMargin'
baselining_case 'spacecraft_options/spacecraftoptions_varinitmass'
```

## 125-130: `state_representation_tests`

```zsh
baselining_case 'state_representation_tests/FreePointArrival_IncomingBplaneRpTA_testatron'
baselining_case 'state_representation_tests/FreePointArrival_OutgoingBplaneRpTA_testatron'
baselining_case 'state_representation_tests/FreePointDeparture_IncomingBplaneRpTA_testatron'
baselining_case 'state_representation_tests/FreePointDeparture_OutgoingBplaneRpTA_testatron'
baselining_case 'state_representation_tests/PeriapseArrival_IncomingBplaneRpTA_testatron'
baselining_case 'state_representation_tests/PeriapseArrival_OutgoingBplaneRpTA_testatron'
```

## 131-137: `transcription_tests`

```zsh
baselining_case 'transcription_tests/CoastPhase_EMintercept'
baselining_case 'transcription_tests/FBLT_EMintercept'
baselining_case 'transcription_tests/MGALT_EMintercept'
baselining_case 'transcription_tests/MGAnDSMs_EMintercept'
baselining_case 'transcription_tests/PSBI_EMintercept'
baselining_case 'transcription_tests/PSFB_EMintercept'
baselining_case 'transcription_tests/SundmanCoastPhase_EMintercept'
```

## Promotion

For a reviewed, stable `matched_snopt` case:

```zsh
promote_if_matched 'group/case'
```

# Summarise baselining directory

```zsh
python testatron/ipopt_characterization.py --summarize-baselining --output-root "$PWD/testatron/ipopt/tests/tests" 
```

with expected output

```zsh
Wrote baselining summary for n case(s): root/testatron/ipopt/tests/tests/baselining/baselining-summary.json

```

# What it does

This defines two `zsh` functions in the current terminal. Defining them does not run EMTG or promote anything.

`baselining_case()` accepts one argument, `$1`, the case ID. For example:

```zsh
baselining_case 'global_mission_options/globalmissionoptions_MGALT_constrDryMass'
```

It runs the Docker-backed pytest launcher for that one case. `EMTG_TEST_ARTIFACT_DIR=...` applies only to that pytest process and tells it where to write evidence. `-q` reduces pytest output; `-k baselining_cli_writes_fixed_mirrored_layout` selects the baselining launcher test.

`promote_if_matched()` also accepts a case ID. It runs the promotion CLI with explicit approval. Promotion still refuses unless the existing evidence has stable `matched_snopt`, accepted refinement, and matching immutable hashes.

The functions remain available only in the current terminal shell session: until you close that terminal, start a new terminal/tab, or otherwise replace/reset that shell. They do not persist after reopening a terminal.