"""Verify Docker probe artifact and source-isolation contracts."""

import pytest

from _docker_support import run_probe


pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
    pytest.mark.toolchain,
]


def test_probe_logs_honor_configured_artifact_directory(
    monkeypatch,
    tmp_path,
    tmp_path_factory,
    toolchain_image,
    repository_root,
):
    artifact_root = tmp_path / "configured-artifacts"
    monkeypatch.setenv("EMTG_TEST_ARTIFACT_DIR", str(artifact_root))

    checks = run_probe(
        image=toolchain_image,
        repository_root=repository_root,
        script=r'''
set -eu
test ! -w /repo
if touch /repo/emtg-read-only-probe 2>/dev/null; then
    rm -f /repo/emtg-read-only-probe
    exit 31
fi
touch /tmp/emtg-ephemeral-write
printf 'EMTG_CHECK source_mount=read_only\n'
''',
        probe_name="artifact-contract-success",
        tmp_path_factory=tmp_path_factory,
    )

    assert checks["source_mount"] == "read_only"
    success_log = artifact_root / "artifact-contract-success.log"
    assert success_log.is_file()
    assert "EMTG_CHECK source_mount=read_only" in success_log.read_text(
        encoding="utf-8"
    )
    assert not (repository_root / "emtg-read-only-probe").exists()

    failure_log = artifact_root / "artifact-contract-failure.log"
    with pytest.raises(
        pytest.fail.Exception,
        match=str(failure_log),
    ):
        run_probe(
            image=toolchain_image,
            repository_root=repository_root,
            script="printf 'expected probe failure\\n'; exit 32",
            probe_name="artifact-contract-failure",
            tmp_path_factory=tmp_path_factory,
        )

    assert failure_log.is_file()
    assert "expected probe failure" in failure_log.read_text(encoding="utf-8")