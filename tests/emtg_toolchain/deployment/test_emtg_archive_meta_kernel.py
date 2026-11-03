"""Deployment verification for the extracted EMTG archive's SPICE meta-kernel support.

Proves the packaged, compiler-free archive-runtime container (no ``/repo``
mount, unlike the toolchain dev container used by
tests/integration/test_meta_kernel_tutorial_baselining.py) can load SPICE
kernels via a committed ``meta_kernel.tm`` fixture instead of the flat
universe ephemeris directory, and still reproduce the promoted tutorial
baselines exactly.
"""

from __future__ import annotations

import shutil
from pathlib import Path, PurePosixPath

import pytest

from emtg_toolchain import cli
from emtg_toolchain.archive import (
    ARCHIVE_ROOT,
    read_archive_text,
    validate_archive,
    validate_checksum,
)
from emtg_toolchain.docker import build_archive_runtime_image, remove_image
from emtg_toolchain.runtime import parse_runtime_requirements
from testatron import ipopt_characterization

from test_emtg_archive_tutorials import _runtime_stage

pytestmark = [
    pytest.mark.tutorials,
    pytest.mark.docker,
    pytest.mark.ipopt_backend,
    pytest.mark.solver_runtime,
]

# The 8 promoted tutorial cases with a committed meta_kernel.tm fixture under
# testatron/ipopt/tests/meta_kernel/fixtures/<case_id>/ (see
# docs/3_NLP_Solvers/IPOPT/meta_kernel_baselining_commands.md). There is no
# dynamic generation and no flat-mode fallback for the other 9 registered
# tutorial cases: requesting one of them here is a configuration error.
META_KERNEL_CASE_IDS = (
    "Config_Files/LowSIRIS-REx",
    "Config_Files/LowSIRIS-REx_high_thrust",
    "Config_Files/LowSIRIS-REx_high_thrust_low_c3",
    "Flybys/EVM",
    "Force_Models/LowSIRIS-REx",
    "Force_Models/LowSIRIS-REx_forcemodel_nlp",
    "LowSIRIS-REx/LowSIRIS-REx",
    "OSIRIS-REx/OSIRIS-REx",
)


def test_extracted_archive_reproduces_tutorials_via_meta_kernel(
    repository_root,
    emtg_toolchain_artifact_root,
    emtg_archive_cold,
    request,
):
    """Require every selected meta-kernel case to match its promoted baseline."""
    artifact_root = emtg_toolchain_artifact_root
    release_archive = request.config.getoption("--release-archive")
    filters = request.config.getoption("tutorial_baselining_filter") or list(
        META_KERNEL_CASE_IDS
    )
    cases = ipopt_characterization.discover_tutorial_cases(filters)
    unsupported = [case.case_id for case in cases if case.case_id not in META_KERNEL_CASE_IDS]
    if unsupported:
        pytest.fail(
            "No committed meta-kernel fixture for tutorial case(s): "
            f"{unsupported}. Supported cases: {list(META_KERNEL_CASE_IDS)}"
        )
    if not cases:
        pytest.fail(f"No tutorial case matches baselining filter(s): {filters}")

    if release_archive is None:
        archive = artifact_root / "emtg-ipopt.tar.gz"
        cli.package(
            repository_root,
            archive,
            cold=emtg_archive_cold,
            build_log_path=artifact_root / "source-build.log",
        )
    else:
        archive = release_archive.expanduser().resolve()
        checksum = archive.with_name(f"{archive.name}.sha256")
        if not archive.is_file():
            raise ValueError(f"release archive does not exist: {archive}")
        if not checksum.is_file():
            raise ValueError(f"release archive checksum does not exist: {checksum}")
        validate_archive(archive)
        validate_checksum(archive, checksum)
        shutil.copy2(checksum, artifact_root / checksum.name)
    requirements = read_archive_text(
        archive, PurePosixPath(ARCHIVE_ROOT, "RUNTIME_REQUIREMENTS.txt")
    )
    image = build_archive_runtime_image(
        archive,
        parse_runtime_requirements(requirements),
        log_path=artifact_root / "runtime-image-build.log",
    )
    (artifact_root / "runtime-image.txt").write_text(f"{image}\n", encoding="utf-8")
    output_root = artifact_root / "evidence"
    schema_cache: dict[Path, list[str]] = {}

    def stage_runner(case, stage, artifacts):
        artifacts = Path(artifacts)
        artifacts.mkdir(parents=True, exist_ok=True)
        spice_meta_kernel = ipopt_characterization.stage_tutorial_meta_kernel(
            case, artifacts, repository_root=repository_root
        )
        return _runtime_stage(
            image=image,
            case=case,
            stage=stage,
            artifacts=artifacts,
            repository_root=repository_root,
            schema_cache=schema_cache,
            spice_meta_kernel=spice_meta_kernel,
        )

    try:
        print(
            f"Verifying archive meta-kernel tutorials: {len(cases)} case(s), "
            "two attempts per case"
        )
        for index, case in enumerate(cases, start=1):
            print(f"[{index}/{len(cases)}] Starting {case.case_id}")
            result = ipopt_characterization.run_repeatable_tutorial_baselining_case(
                case,
                stage_runner,
                output_root=output_root,
                repository_root=repository_root,
            )
            assert result["repeatability"]["stable"], case.case_id
            assert result["classification"] == "matched_tutorial_reference", (
                case.case_id,
                result,
            )
            print(f"[{index}/{len(cases)}] Completed {case.case_id}")
    finally:
        remove_image(image)
