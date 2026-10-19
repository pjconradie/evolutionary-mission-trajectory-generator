"""Unit tests for release-baseline evidence."""

import hashlib
from pathlib import Path

import pytest

from emtg_toolchain.release import (
    build_commit_from_requirements,
    build_mode_from_requirements,
    release_baseline_record,
)


pytestmark = pytest.mark.unit


def test_release_baseline_record_identifies_exact_archive_and_reference(tmp_path):
    archive = tmp_path / "emtg-ipopt-1.0.tar.gz"
    archive.write_bytes(b"archive")
    reference = tmp_path / "tutorial_baselining_verification.json"
    reference.write_text("{}\n", encoding="utf-8")
    requirements = "Build commit: `abc123`\nBuild mode: `cold`\n"
    verification = {"case_count": 17, "stage_count": 33, "acceptable": True}

    record = release_baseline_record(
        archive=archive,
        requirements=requirements,
        verification=verification,
        verification_reference=reference,
        evidence_root=tmp_path / "evidence",
    )

    assert record["archive"] == {
        "filename": "emtg-ipopt-1.0.tar.gz",
        "path": str(archive),
        "sha256": hashlib.sha256(b"archive").hexdigest(),
    }
    assert record["archive_build_mode"] == "cold"
    assert record["source_commit"] == "abc123"
    assert record["verification"]["acceptable"] is True


def test_build_commit_requires_archive_manifest_value():
    with pytest.raises(ValueError, match="do not declare"):
        build_commit_from_requirements("Target platform: `linux/amd64`\n")


def test_release_baseline_requires_cold_archive_manifest():
    with pytest.raises(ValueError, match="must have a cold"):
        release_baseline_record(
            archive=Path("archive.tar.gz"),
            requirements="Build commit: `abc123`\nBuild mode: `hot`\n",
            verification={"case_count": 17, "stage_count": 33, "acceptable": True},
            verification_reference=Path("reference.json"),
            evidence_root=Path("evidence"),
        )


def test_build_mode_requires_archive_manifest_value():
    with pytest.raises(ValueError, match="do not declare"):
        build_mode_from_requirements("Build commit: `abc123`\n")
