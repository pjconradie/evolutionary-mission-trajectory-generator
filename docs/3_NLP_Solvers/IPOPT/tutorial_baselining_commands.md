
# Tutorial Baselining Commands

Run these commands from the repository root. `tutorial_baselining_case` uses
the Docker-backed tutorial launcher and replaces only the selected tutorial
case's evidence below `testatron/ipopt/tests/benchmarks/baselining/`. It never
modifies inputs, reference packages, hardware, universe files, ephemerides, or
seed artifacts beneath `docs/0_Users/tutorial/Tutorial_EMTG_Files/`.

## How To Use This File

1. Open a terminal and change to the repository root.
2. Copy the function below into that terminal.
3. Run one `tutorial_baselining_case 'group/case'` command at a time.

```zsh
tutorial_baselining_case() {
	EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/benchmarks" \
	python -m pytest tests/integration/test_tutorial_baselining.py -q \
		--tutorials \
		--tutorial-baselining-filter "$1"
}
```

### Complete tutorial case list

```zsh
tutorial_baselining_case 'Config_Files/LowSIRIS-REx'
tutorial_baselining_case 'Config_Files/LowSIRIS-REx_high_thrust'
tutorial_baselining_case 'Config_Files/LowSIRIS-REx_high_thrust_low_c3'

tutorial_baselining_case 'Journey_Boundaries/EVM'
tutorial_baselining_case 'Journey_Boundaries/EVM_freepoint'

tutorial_baselining_case 'OSIRIS-REx/OSIRIS-REx'

tutorial_baselining_case 'Force_Models/LowSIRIS-REx_forcemodel_nlp'
tutorial_baselining_case 'Force_Models/LowSIRIS-REx'
tutorial_baselining_case 'Force_Models/LowSIRIS-REx_forcemodel'

tutorial_baselining_case 'LowSIRIS-REx/LowSIRIS-REx_FBLT'
tutorial_baselining_case 'LowSIRIS-REx/LowSIRIS-REx'

tutorial_baselining_case 'Constraint_Scripting/EVM_freepoint_boundary_constraint'
tutorial_baselining_case 'Constraint_Scripting/EVM_freepoint'
tutorial_baselining_case 'Constraint_Scripting/EVM_freepoint_maneuver_constraint'

tutorial_baselining_case 'Flybys/EVM'
tutorial_baselining_case 'Flybys/HighFidelity'
tutorial_baselining_case 'Flybys/EVM_singlePhase'
```

## Promotion

1. Copy the function below into that terminal.
2. Run one `promote_tutorial_if_matched 'group/case'` command at a time.

```zsh
promote_tutorial_if_matched() {
	local case_id="$1"
	shift
	.venv/bin/python testatron/ipopt_characterization.py \
		--promote-tutorial-baseline "$case_id" \
		--approve-baseline \
		--output-root "$PWD/testatron/ipopt/tests/benchmarks" \
		--tutorial-verification-reference \
		"$PWD/testatron/ipopt/tests/tutorial_baselining_verification.json" \
		"$@"
}
```

### Complete tutorial promotion case list

```zsh
promote_tutorial_if_matched 'Config_Files/LowSIRIS-REx'
promote_tutorial_if_matched 'Config_Files/LowSIRIS-REx_high_thrust'
promote_tutorial_if_matched 'Config_Files/LowSIRIS-REx_high_thrust_low_c3'

promote_tutorial_if_matched 'Journey_Boundaries/EVM'
promote_tutorial_if_matched 'Journey_Boundaries/EVM_freepoint'

promote_tutorial_if_matched 'OSIRIS-REx/OSIRIS-REx'

promote_tutorial_if_matched 'Force_Models/LowSIRIS-REx_forcemodel_nlp'
promote_tutorial_if_matched 'Force_Models/LowSIRIS-REx'
promote_tutorial_if_matched 'Force_Models/LowSIRIS-REx_forcemodel'

promote_tutorial_if_matched 'LowSIRIS-REx/LowSIRIS-REx_FBLT'
promote_tutorial_if_matched 'LowSIRIS-REx/LowSIRIS-REx'

promote_tutorial_if_matched 'Constraint_Scripting/EVM_freepoint_boundary_constraint'
promote_tutorial_if_matched 'Constraint_Scripting/EVM_freepoint'
promote_tutorial_if_matched 'Constraint_Scripting/EVM_freepoint_maneuver_constraint'

promote_tutorial_if_matched 'Flybys/EVM'
promote_tutorial_if_matched 'Flybys/HighFidelity'
promote_tutorial_if_matched 'Flybys/EVM_singlePhase'
```

## Evidence Layout

For `group/case`, the launcher writes:

```text
testatron/ipopt/tests/benchmarks/baselining/group/case/
├── attempt-1/
│   ├── inventory.json
│   ├── replay/
│   ├── refinement/                 # omitted for replay-only cases
│   └── result.json
├── attempt-2/
│   ├── inventory.json
│   ├── replay/
│   ├── refinement/                 # omitted for replay-only cases
│   └── result.json
├── repeatability.json
└── result.json
```

`inventory.json` records the immutable tutorial inputs staged for the attempt
and reports `dependency_blocked` rather than running EMTG when a required
hardware, universe, ephemeris, or seed file is unavailable.
