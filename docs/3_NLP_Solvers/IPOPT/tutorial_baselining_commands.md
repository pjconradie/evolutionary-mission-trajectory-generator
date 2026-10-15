
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
4. Inspect both attempt directories, `repeatability.json`, and `result.json`
   before proceeding to the next case.
5. Do not run corpus baselining concurrently; both workflows use the normal
   reusable IPOPT Docker build volume.

```zsh
tutorial_baselining_case() {
	EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/benchmarks" \
	python -m pytest tests/integration/test_tutorial_baselining.py -q \
		--tutorials \
		--tutorial-baselining-filter "$1"
}
```

The command executes each applicable tutorial stage in two fresh attempts. A
normal tutorial case performs replay followed by refinement in both attempts.
The deliberate-infeasible Force Models case is intentionally replay-only.
Each staged refinement applies the versioned tutorial policy: `seed_MBH=0`,
`MBH_RNG_seed=12345`, a 600-second IPOPT limit, and 32,000 IPOPT major
iterations. The staged `compatibility.json` records the policy version, hash,
and applied settings.

## Complete Tutorial Case List

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

These 17 commands produce 33 tutorial stage outcomes: 17 replay stages and 16
refinement stages.

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

Tutorial summary, decision-log, verification-reference, and promotion commands
will be added after their corresponding implementation phases.
