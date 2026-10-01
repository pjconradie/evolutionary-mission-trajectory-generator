# OSIRIS-REx Earth–Bennu trajectory reconstruction

This mission folder contains a reproducible EMTG optimization that starts from a fixed OSIRIS-REx in-flight state, models an Earth gravity assist, and arrives at Bennu. It is intended to reconstruct the interplanetary trajectory and minimize deterministic $\Delta v$ after the supplied in-flight state. It does **not** optimize or include launch and injection costs.

The pipeline runs low-fidelity, single-phase, and high-fidelity optimizations in sequence. Its UTC event-date targets are based on NASA's [OSIRIS-REx mission timeline](https://science.nasa.gov/mission/osiris-rex/in-depth/): the first deep-space maneuver (DSM-1) on 2016-12-28, Earth encounter on 2017-09-22, and Bennu arrival on 2018-12-03.

## Mission inputs and assumptions

### Fixed initial state

The input is [initial_state.yaml](../initial_state.yaml). The state is specified at ET 526676400.2 seconds past J2000 (2016-09-09 UTC), in the J2000 frame, with position in km and velocity in km/s. Its origin is the solar-system barycenter (SSB). The script validates those units and dimensions, obtains the Sun's SSB state from SPICE at the same epoch, and subtracts the Sun state to form the Sun-relative Cartesian state required by the EMTG departure options. It also converts the epoch to MJD(TDB).

The state is fixed; departure state components and waiting time are not free optimization variables. The initial impulse is excluded from the cost. The first DSM's **epoch** is constrained to the flown DSM-1 UTC calendar day; its magnitude is optimized and is not asserted to match flight telemetry.

### Ephemerides and universe files

SPICE kernels used by preparation are stored in [universe/ephemeris_files](../universe/ephemeris_files/):

- `naif0012.tls` supplies leap-second data for UTC/ET conversions.
- `de430.bsp` supplies planetary and solar ephemerides.
- `bennu_refdrmc_v1.bsp` supplies Bennu ephemeris.
- `pck00010.tpc` supplies planetary constants.

The SPK files must cover the state epoch and trajectory event epochs. The mission uses a tutorial Sun universe and stages the repository Earth universe for Earth-centered high-fidelity legs. `prepare` creates the expected `Sun.emtg_universe` symlink and copies `Universe/Earth.emtg_universe` only if a mission-local Earth universe does not already exist. Do not replace or modify the supplied kernels or mission-specific universe data without checking coverage and provenance.

UTC target calendar days are converted with the staged LSK and SPICE to MJD(TDB). EMTG's arrival bounds are inclusive, so the end of each day is moved inward by one second. The converted state, UTC target dates, source URL, and MJD(TDB) bounds are recorded in [config/state_conversion.json](../config/state_conversion.json) when preparation runs.

## Formulation

The low-fidelity problem uses EMTG MGAnDSMs (`mission_type=6`), a fixed Sun-centered free-point departure, Earth in the flyby sequence, and Bennu as the destination. It minimizes deterministic $\Delta v$ with IPOPT. The initial impulse is excluded from the objective; the optimized DSMs and terminal rendezvous maneuver contribute to it. Total flight time is bounded between 300 and 900 days. The Bennu arrival is constrained to 2018-12-03 UTC, and the first DSM epoch to 2016-12-28 UTC.

The pipeline's later stages apply target bounds as follows:

| Stage | Earth encounter | Bennu arrival | First DSM |
| --- | --- | --- | --- |
| Low fidelity | Not tightly date-bounded | 2018-12-03 UTC | 2016-12-28 UTC |
| Single phase | 2017-09-22 UTC | 2018-12-03 UTC | 2016-12-28 UTC |
| High fidelity | Earth periapsis, 2017-09-22 UTC | 2018-12-03 UTC | 2016-12-28 UTC |

In high fidelity, the two sphere-of-influence transition journeys remain unbounded in time to allow the Earth flyby geometry to be bracketed. The Earth periapsis and Bennu rendezvous journeys carry the date bounds.

## Requirements

- macOS or Linux with Docker available and its daemon running. On macOS, the runner attempts to launch Docker Desktop if needed.
- Python 3 with PyYAML and SPICEyPy installed in the host environment. These are required by the preparation script and are not listed in the repository's current `requirements.txt`.
- The repository's SPICE kernels and universe assets described above.
- Network access the first time the repository's Docker toolchain image must be built; an existing compatible image may be reused.

The optimizer and PyEMTG conversion stages run in a Linux `linux/amd64` Docker container. A named Docker volume persists the CMake build between stages. The runner generates `.emtg-source` under the mission directory to provide CMake with the expected source/config layout. It is generated infrastructure and should not be hand-edited. The repository is mounted read-only at `/repo`; this mission directory is mounted read-write at `/mission`.

## Running the mission

From the repository root, first install the host-side requirements if necessary, then run:

```sh
python -m pip install -r requirements.txt pyyaml spiceypy
python docs/2_Missions/osiris-rex/src/run_mission.py run
```

The integration test invokes the same complete pipeline. Set its opt-in variable to enable the potentially long Docker run:

```sh
RUN_OSIRIS_REX_INTEGRATION=1 python -m pytest docs/2_Missions/osiris-rex/tests/integration/test_pipeline.py -q
```

The state conversion and options-generation unit tests can be run without Docker:

```sh
python -m pytest docs/2_Missions/osiris-rex/tests/unit/test_state.py -q
```

The runner prepares the mission and then runs these stages:

1. Generate the Sun-relative initial state and low-fidelity options.
2. Optimize the low-fidelity MGAnDSMs mission.
3. Convert the low-fidelity options to a split single-phase trajectory, then run a fresh single-phase optimization with Earth and Bennu date constraints.
4. Generate high-fidelity options from the single-phase result and optimize them with IPOPT.

Each optimization stage deletes its prior result, failure marker, archive, and XFfile before launching EMTG, then verifies a feasible solution was produced. The current stage's output is used by the next conversion stage in the same run. Existing result files are not treated as initial solutions or carried forward to seed a rerun. Generated options and outputs are written under the mission directory; the source checkout is not modified by the container build.

## Outputs

- [config/OSIRIS_REx_Low.emtgopt](../config/OSIRIS_REx_Low.emtgopt): generated low-fidelity options.
- [config/state_conversion.json](../config/state_conversion.json): state conversion provenance and UTC-to-MJD(TDB) bounds.
- [config/high_fidelity](../config/high_fidelity/): generated high-fidelity options.
- [results/low](../results/low/): low-fidelity trajectory, log, and archive.
- [results/single_phase](../results/single_phase/): single-phase trajectory, log, and archive.
- [results/high_fidelity](../results/high_fidelity/): high-fidelity trajectory, log, and archive.
- [results](../results/): conversion logs and stage outputs.

The result files report maneuver magnitudes, event epochs, objective value, and feasibility metadata. EMTG commonly displays event epochs in ET/TDB-derived calendar notation, whereas NASA's event dates and the constraints above are UTC. Check the converted date bounds in `state_conversion.json` rather than interpreting a printed calendar-day label without its time scale.

## Current reference run

The checked-in generated results from the current pipeline run report:

| Stage | Flight time (approx.) | Deterministic $\Delta v$ (approx.) | Feasibility |
| --- | ---: | ---: | --- |
| [Low](../results/low/OSIRIS_REx_Low.emtg) | 815 days | 0.941 km/s | Feasible; best feasible attempt 6 |
| [Single phase](../results/single_phase/OSIRIS_REx_Low_singlePhase.emtg) | 816 days | 1.117 km/s | Feasible; best feasible attempt 22 |
| [High fidelity](../results/high_fidelity/OSIRIS_REx_Low_singlePhase_HighFidelity.emtg) | 816 days | 1.120 km/s | Feasible; best feasible attempt 1 |

These are results from this formulation and solver configuration, not proof of a global minimum or a telemetry-matched reconstruction. They should be regenerated when inputs, kernels, EMTG, or solver settings change. The optimized first DSM date is constrained, but its magnitude is free; do not interpret it as a measured flown magnitude. Since the trajectory starts from an in-flight state and excludes the initial impulse, these values are not the full launch-to-arrival mission $\Delta v$.

## Troubleshooting and reproducibility notes

- **Missing SPK or LSK:** check that `universe/ephemeris_files` contains a `.bsp` kernel and `naif0012.tls`, and that kernel coverage includes all configured dates.
- **Docker unavailable:** start Docker Desktop (macOS) or the Docker daemon, then rerun. The script checks the daemon before starting the pipeline.
- **First run builds the image:** when the preferred cached image lacks SciPy, the runner invokes the repository's focused IPOPT integration test to build/validate a compatible image before continuing.
- **CMake cache mismatch:** `/build` is persistent. The runner clears it if it belongs to another source directory and configures EMTG with IPOPT.
- **Result date appears one day later:** distinguish UTC from ET/TDB calendar rendering and compare the event epoch to the recorded MJD(TDB) bounds.
- **A stage fails:** inspect its `emtg.log` or conversion log under `results/`. The runner removes stale success artifacts first, so a failed current invocation is not mistaken for a prior successful result.

The implementation is in [src/osiris_rex.py](../src/osiris_rex.py) and [src/run_mission.py](../src/run_mission.py); tests are in [tests/unit/test_state.py](../tests/unit/test_state.py) and [tests/integration/test_pipeline.py](../tests/integration/test_pipeline.py).
