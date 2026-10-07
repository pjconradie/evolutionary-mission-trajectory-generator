"""Verify reproducible Testatron IPOPT baselining in the pinned toolchain."""

import json

import pytest

from _docker_support import artifact_directory, build_volume_name, run_probe


pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
    pytest.mark.ipopt_backend,
    pytest.mark.ipopt_tests,
    pytest.mark.solver_runtime,
]


@pytest.mark.parametrize(
    "case_id",
    (
        "global_mission_options/globalmissionoptions_MGALT_DLAbounds",
        "transcription_tests/SundmanCoastPhase_EMintercept",
    ),
)
def test_baselining_repeatability_in_pinned_toolchain(
    case_id, toolchain_image, repository_root, tmp_path_factory
):
    """Require two fresh seeded runs to retain identical evidence conclusions."""
    artifacts = artifact_directory(tmp_path_factory) / case_id.replace("/", "-")
    source = f"/repo/testatron/tests/{case_id}.emtgopt"
    baseline = f"/repo/testatron/tests/{case_id}.emtg"
    script = f'''set -eu
cmake --build /build --target EMTGv9 -j2 >/tmp/baselining-build.log 2>&1 \\
    || {{ tail -n 150 /tmp/baselining-build.log; exit 20; }}
PYTHONPATH=/repo:/repo/PyEMTG python - <<'PY'
import json
from pathlib import Path

from testatron import ipopt_characterization

first, second, comparison = ipopt_characterization.run_repeatable_baselining_case(
    {source!r},
    {baseline!r},
    "/build/src/EMTGv9",
    "/artifacts",
    180.0,
    "/repo/PyEMTG",
)
summary = {{
    "first_classification": first.classification,
    "second_classification": second.classification,
    "stable": comparison["stable"],
    "differences": comparison["differences"],
}}
Path("/artifacts/repeatability-summary.json").write_text(
    json.dumps(summary, indent=2) + "\\n"
)
if not comparison["stable"]:
    raise SystemExit("fresh baselining runs produced materially different evidence")
PY
test -s /artifacts/repeatability-summary.json
printf 'EMTG_CHECK baselining_repeatability=passed\\n'
'''
    checks = run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name=f"baselining-repeat-{case_id.rsplit('/', 1)[-1].lower()}",
        tmp_path_factory=tmp_path_factory,
        build_volume=build_volume_name(toolchain_image, "ipopt"),
        writable_artifacts=artifacts,
        timeout=900,
    )

    summary = json.loads((artifacts / "repeatability-summary.json").read_text())
    assert checks["baselining_repeatability"] == "passed"
    assert summary["stable"]
    assert summary["first_classification"] == summary["second_classification"]