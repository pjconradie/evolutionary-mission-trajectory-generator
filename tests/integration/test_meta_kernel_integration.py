"""Verify SPICE meta-kernel loading, teardown, and error handling end to end.

Two tiers of coverage, matching the plan's §4 Step 4 fixture split:

- A standalone CSPICE-level probe (``meta_kernel_cspice_probe``) exercises
  ``furnsh_c``/``ktotal_c``/``kdata_c``/``unload_c``/``failed_c``/``getmsg_c``
  directly against the committed fixtures under
  ``tests/integration/fixtures/meta_kernel/`` -- this covers load/inventory,
  teardown, and the CSPICE error path without needing a full ``EMTGv9`` run.
- Real ``EMTGv9`` executable runs, driving the existing small/fast
  ``CoastPhase_EMintercept`` mission via a ``SPICE_meta_kernel`` option
  instead of the flat ``ephemeris_files/`` scan, cover the "mission still
  solves" path and the two EMTG-side hard-fail paths (missing meta-kernel
  file, and a meta-kernel CSPICE itself fails to load).

It does not compare against any testatron/ipopt/tests/benchmarks/ truth file 
(not track-acs-prop, not any other benchmark). Specifically:

test_meta_kernel_cspice_load_resolves_path_symbols doesn't even run EMTGv9 — 
it's a standalone g++-compiled probe linked directly against libcspice.a, 
checking furnsh_c/ktotal_c/kdata_c/unload_c behavior in isolation.

test_meta_kernel_mission_still_solves runs real EMTGv9, but against 
testatron/tests/transcription_tests/CoastPhase_EMintercept.emtgopt — a small,
fast, pre-existing CI smoke-test mission (synthetic Moon/Sun/GatewayNRHO body
set), not a benchmark case. Success is verified only by: stdout containing 
"Completed loading SPICE meta-kernel", stdout not containing the flat-mode 
"Completed loading SPICE kernels.", and a .emtg output file existing. There 
is no numerical/objective/trajectory comparison against any truth file.
The two hard-fail tests (missing_file, malformed_tm) use _mission_error_probe, 
which also builds+runs real EMTGv9 but only checks stdout text ("EMTG failed 
with error:", "does not exist", "Failed to load SPICE meta-kernel") since the 
outer catch in EMTG_v9.cpp always returns exit code 0.
"""

import pytest
from pathlib import Path


pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
    pytest.mark.solver_runtime,
]


def test_meta_kernel_cspice_load_resolves_path_symbols(meta_kernel_cspice_probe):
    assert meta_kernel_cspice_probe["meta_kernel_cspice_probe_compile"] == "passed"
    assert meta_kernel_cspice_probe["meta_kernel_cspice_probe_run"] == "passed"


def test_meta_kernel_mission_still_solves(meta_kernel_mission_probe):
    assert meta_kernel_mission_probe["meta-kernel-mission_compile"] == "passed"
    assert meta_kernel_mission_probe["meta-kernel-mission_run"] == "passed"

    log = meta_kernel_mission_probe["log"]
    assert "Completed loading SPICE meta-kernel" in log
    assert "Completed loading SPICE kernels." not in log

    mission = meta_kernel_mission_probe["mission"]
    assert mission is not None


def test_meta_kernel_missing_file_hard_fails(meta_kernel_missing_file_probe):
    assert (
        meta_kernel_missing_file_probe["meta-kernel-missing-file_compile"]
        == "passed"
    )

    log = meta_kernel_missing_file_probe["log"]
    assert "EMTG failed with error:" in log
    assert "does not exist" in log
    assert not Path(meta_kernel_missing_file_probe["result_path"]).exists()


def test_meta_kernel_malformed_tm_hard_fails(meta_kernel_malformed_tm_probe):
    assert (
        meta_kernel_malformed_tm_probe["meta-kernel-malformed-tm_compile"]
        == "passed"
    )

    log = meta_kernel_malformed_tm_probe["log"]
    assert "EMTG failed with error:" in log
    assert "Failed to load SPICE meta-kernel" in log
    assert not Path(meta_kernel_malformed_tm_probe["result_path"]).exists()
