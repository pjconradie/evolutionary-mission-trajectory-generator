
# OSIRIS-Rex

## Plan: OSIRIS-REx MGA-nDSM Pipeline

The initial state is confirmed as a fixed SSB-to-spacecraft state in J2000, with position in km and velocity in km/s. Since the mission uses the Sun as its central body, the pipeline will use SPICE to convert that state to Sun-relative coordinates at the stated ET epoch before building EMTG options.

**Steps**

1. **Validate and transform the initial state**
   - Read the state and epoch from `initial_state.yaml`.
   - Use SPICE to obtain the Sun’s SSB position and velocity at that epoch, then subtract them from the spacecraft SSB state.
   - Check the epoch, frame, units, kernels, and converted state; stop with a useful error if validation fails.

2. **Prepare low-fidelity mission inputs**
   - Stage the Sun-centered Universe, Earth and Bennu data, SPICE kernels, and a minimal valid spacecraft/hardware configuration under `osiris-rex`.
   - Configure MGAnDSMs with a fixed free-point, free-direct inertial Cartesian departure; an Earth flyby; and Bennu rendezvous with a chemical maneuver.
   - Minimize deterministic delta-V, including DSMs and the Bennu rendezvous maneuver—not fuel or mass. Keep required hardware inputs valid but ensure mass/fuel limits do not drive the solution.
   - Use the OSIRIS-REx tutorial as a topology and objective reference, not as a drop-in free-point configuration: tutorial and options.

3. **Manage Docker readiness and mission execution**
   - Prefer `emtg-pytest-toolchain:309abb32ff087c0b`, with the existing content-addressed build path as fallback.
   - Use disposable containers and existing mounts/build-volume patterns from Docker support.
   - Check daemon availability; if Docker Desktop is stopped on macOS, attempt to start it and wait with a timeout. If the engine remains unavailable, report that clearly.
   - Confirm the image can run and require a focused IPOPT solver probe to pass before starting mission stages, following integration fixtures and IPOPT tests.

4. **Run low-to-high fidelity**
   - Optimize and record the low-fidelity mission, including feasibility, solver status, delta-V breakdown, options, solution, and logs.
   - Convert the Earth encounter to SOI/periapse Journeys using the checked-in single-phase converter and high-fidelity driver. Verify the conversion supports this Sun-centered free-point start.
   - Retain and explicitly validate the Bennu terminal rendezvous: the existing converter does not automatically convert final arrival.
   - Run a separate optimization on the converted mission; conversion itself does not perform the solve. Compare the high- and low-fidelity results.

5. **Verify**
   - Test epoch/state parsing, SSB-to-Sun conversion, invalid SPICE inputs, generated options, and mocked Docker startup/probe failure cases.
   - Run the focused IPOPT health probe, then bounded low- and high-fidelity mission runs when the toolchain is available.
   - Verify options round-trip, mission topology, delta-V accounting, and output/provenance locations.

**Decisions and scope**

- Use the YAML state as fixed; interpret its frame/origin/units as J2000, SSB-to-spacecraft, km and km/s.
- Use the supplied `309abb32` image by preference, disposable containers, and an IPOPT solver probe for readiness.
- High fidelity covers the Earth flyby’s SOI/periapse treatment. Bennu arrival/capture modeling is excluded for now; the retained terminal treatment will be reported explicitly.
- Existing Docker support does not launch Docker Desktop or provide an application-container health check, so the orchestration must handle bounded Desktop startup and use the IPOPT probe as its readiness criterion.
- The checked-in high-fidelity driver generates converted options/initial guesses but does not optimize. The tutorial options use Windows paths and SNOPT, so they require adaptation.

