"""Docker-backed integration tests for the EMTG runtime archive."""

from pathlib import PurePosixPath

import pytest

from emtg_toolchain import cli
from emtg_toolchain.archive import ARCHIVE_ROOT, read_archive_text, validate_archive, validate_checksum
from emtg_toolchain.docker import build_archive_runtime_image, remove_image, run_command
from emtg_toolchain.runtime import parse_runtime_requirements


pytestmark = [
    pytest.mark.integration,
    pytest.mark.docker,
    pytest.mark.toolchain,
    pytest.mark.ipopt_backend,
    pytest.mark.solver_runtime,
]


def test_archive_extracts_into_clean_bookworm_runtime(
    repository_root,
    emtg_toolchain_artifact_root,
    emtg_archive_cold,
):
    """Package EMTG and validate its binary in a compiler-free runtime image."""
    artifact_root = emtg_toolchain_artifact_root
    output = artifact_root / "emtg-ipopt.tar.gz"
    cli.package(
        repository_root,
        output,
        cold=emtg_archive_cold,
        build_log_path=artifact_root / "source-build.log",
    )
    (artifact_root / "archive-build-mode.txt").write_text(
        f"{'cold' if emtg_archive_cold else 'hot'}\n",
        encoding="ascii",
    )
    checksum = output.with_name(f"{output.name}.sha256")
    validate_archive(output)
    validate_checksum(output, checksum)

    requirements = read_archive_text(
        output,
        PurePosixPath(ARCHIVE_ROOT, "RUNTIME_REQUIREMENTS.txt"),
    )
    packages = parse_runtime_requirements(requirements)
    image = build_archive_runtime_image(
        output,
        packages,
        log_path=artifact_root / "runtime-image-build.log",
    )
    (artifact_root / "runtime-image.txt").write_text(f"{image}\n", encoding="utf-8")
    try:
        result = run_command(
            [
                "docker", "run", "--rm", "--platform", "linux/amd64", image,
                "sh", "-c",
                "ldd /opt/toolkit/emtg/bin/EMTGv9"
                " && ! ldd /opt/toolkit/emtg/bin/EMTGv9 | grep -F 'not found'"
                " && ! ldd /opt/toolkit/emtg/bin/EMTGv9 | grep -i snopt"
                " && ! ldd /opt/toolkit/emtg/bin/EMTGv9 | grep -F libcspice.so",
            ],
            description="EMTG archive runtime linkage validation",
            log_path=artifact_root / "runtime-ldd.log",
        )
    finally:
        remove_image(image)

    assert "libipopt.so" in result.stdout
