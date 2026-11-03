
# Meta Kernel Tutorial Baselining Commands

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
meta_kernel_tutorial_baselining_case() {
	EMTG_TEST_ARTIFACT_DIR="$PWD/testatron/ipopt/tests/meta_kernel" \
	python -m pytest tests/integration/test_meta_kernel_tutorial_baselining.py -q \
		--tutorials \
		--tutorial-baselining-filter "$1"
}
```

### Complete tutorial case list

```zsh
tutorial_baselining_case 'Config_Files/LowSIRIS-REx'
tutorial_baselining_case 'Config_Files/LowSIRIS-REx_high_thrust'
tutorial_baselining_case 'Config_Files/LowSIRIS-REx_high_thrust_low_c3'

tutorial_baselining_case 'OSIRIS-REx/OSIRIS-REx'

tutorial_baselining_case 'Force_Models/LowSIRIS-REx_forcemodel_nlp'
tutorial_baselining_case 'Force_Models/LowSIRIS-REx'

tutorial_baselining_case 'LowSIRIS-REx/LowSIRIS-REx'

tutorial_baselining_case 'Flybys/EVM'
```
