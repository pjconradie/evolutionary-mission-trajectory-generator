"""Verify reproducible Testatron IPOPT baselining in the pinned toolchain."""

import json
import shlex

import pytest

from conftest import _backend_source_script
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
    script = _backend_source_script("IPOPT") + f'''
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


def test_baselining_cli_writes_fixed_mirrored_layout(
    request, toolchain_image, repository_root, tmp_path_factory
):
    """Exercise selected CLI batches through the pinned Docker workflow."""
    filters = request.config.getoption("baselining_filter") or [
        "global_mission_options/globalmissionoptions_MGALT_DLAbounds"
    ]
    filter_arguments = " ".join(
        f"--filter {shlex.quote(case_filter)}" for case_filter in filters
    )
    artifacts = artifact_directory(tmp_path_factory)
    script = _backend_source_script("IPOPT") + f'''
cmake --build /build --target EMTGv9 -j2 >/tmp/baselining-build.log 2>&1 \\
    || {{ tail -n 150 /tmp/baselining-build.log; exit 20; }}
PYTHONPATH=/repo:/repo/PyEMTG python /repo/testatron/ipopt_characterization.py \\
    --baselining \\
    {filter_arguments} \\
    --emtg /build/src/EMTGv9 \\
    --output-root /artifacts \\
    --timeout 180.0
PYTHONPATH=/repo:/repo/PyEMTG python - <<'PY'
import json
from pathlib import Path

batch_root = Path("/artifacts/baselining")
case_roots = sorted(path.parent for path in batch_root.glob("*/*/result.json"))
if not case_roots:
    raise SystemExit("fixed baselining batch layout is incomplete")
for case_root in case_roots:
    required_paths = (
        case_root / "attempt-1" / "result.json",
        case_root / "attempt-2" / "result.json",
        case_root / "repeatability.json",
        case_root / "result.json",
    )
    if not all(path.is_file() for path in required_paths):
        raise SystemExit(f"fixed baselining batch layout is incomplete: {{case_root}}")
    if not json.loads((case_root / "repeatability.json").read_text())["stable"]:
        raise SystemExit(f"fixed baselining batch produced unstable evidence: {{case_root}}")
Path("/artifacts/batch-summary.json").write_text(
    json.dumps(
        {{
            "case_ids": [str(case_root.relative_to(batch_root)) for case_root in case_roots],
            "stable": True,
        }},
        indent=2,
    )
    + "\\n"
)
PY
test -s /artifacts/batch-summary.json
printf 'EMTG_CHECK baselining_batch_layout=passed\\n'
'''
    checks = run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=script,
        probe_name="baselining-batch-layout",
        tmp_path_factory=tmp_path_factory,
        build_volume=build_volume_name(toolchain_image, "ipopt"),
        writable_artifacts=artifacts,
        timeout=900,
    )

    summary = json.loads((artifacts / "batch-summary.json").read_text())
    assert checks["baselining_batch_layout"] == "passed"
    assert summary["stable"]
    assert summary["case_ids"]
    for case_id in summary["case_ids"]:
        case_root = artifacts / "baselining" / case_id
        assert (case_root / "attempt-1" / "result.json").is_file()
        assert (case_root / "attempt-2" / "result.json").is_file()
        assert (case_root / "repeatability.json").is_file()
        assert (case_root / "result.json").is_file()