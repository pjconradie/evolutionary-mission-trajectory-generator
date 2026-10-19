"""Unit tests for EMTG archive staging and validation."""

import stat
import tarfile
from pathlib import PurePosixPath

import pytest

from emtg_toolchain.archive import (
    ARCHIVE_ROOT,
    ArchiveEntry,
    build_payload_manifest,
    create_archive,
    stage_payload,
    validate_archive,
    validate_checksum,
    validate_manifest,
    write_checksum,
    write_text_file,
)


pytestmark = pytest.mark.unit


def _repository(tmp_path):
    repository = tmp_path / "repository"
    (repository / "Universe" / "ephemeris_files").mkdir(parents=True)
    (repository / "HardwareModels").mkdir()
    (repository / "Universe" / "Earth.emtg_universe").write_text("Earth\n")
    (repository / "Universe" / "ephemeris_files" / "naif0012.tls").write_text("tls\n")
    (repository / "Universe" / "ephemeris_files" / "pck00010.tpc").write_text("tpc\n")
    (repository / "HardwareModels" / "default.emtg_launchvehicleopt").write_text("hardware\n")
    executable = repository / "EMTGv9"
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o755)
    return repository, executable


def test_manifest_contains_only_allowlisted_runtime_assets(tmp_path):
    repository, executable = _repository(tmp_path)
    (repository / "Universe" / "ephemeris_files" / "de430.bsp").write_text("excluded\n")

    entries = build_payload_manifest(repository, executable)

    destinations = {entry.destination.as_posix() for entry in entries}
    assert f"{ARCHIVE_ROOT}/bin/EMTGv9" in destinations
    assert f"{ARCHIVE_ROOT}/universe/Earth.emtg_universe" in destinations
    assert f"{ARCHIVE_ROOT}/universe/ephemeris_data/naif0012.tls" in destinations
    assert f"{ARCHIVE_ROOT}/hardware/default.emtg_launchvehicleopt" in destinations
    assert not any(destination.endswith(".bsp") for destination in destinations)


def test_manifest_rejects_unsafe_or_duplicate_destinations(tmp_path):
    repository, executable = _repository(tmp_path)
    with pytest.raises(ValueError, match="unsafe archive destination"):
        validate_manifest([ArchiveEntry(executable, PurePosixPath("emtg", "..", "bad"))])
    with pytest.raises(ValueError, match="duplicate archive destination"):
        validate_manifest(
            [
                ArchiveEntry(executable, PurePosixPath("emtg", "bin", "EMTGv9")),
                ArchiveEntry(executable, PurePosixPath("emtg", "bin", "EMTGv9")),
            ]
        )


def test_archive_is_safe_and_preserves_executable_mode(tmp_path):
    repository, executable = _repository(tmp_path)
    stage = tmp_path / "stage"
    stage_payload(build_payload_manifest(repository, executable), stage)
    write_text_file(stage, PurePosixPath("emtg", "README.md"), "runtime\n")
    archive = tmp_path / "emtg.tar.gz"

    create_archive(stage, archive)
    validate_archive(archive)

    with tarfile.open(archive, "r:gz") as opened:
        executable_member = opened.getmember("emtg/bin/EMTGv9")
        assert executable_member.mode & stat.S_IXUSR
        assert all(
            not member.name.startswith("/") and ".." not in PurePosixPath(member.name).parts
            for member in opened.getmembers()
        )


def test_checksum_manifest_must_name_and_match_archive(tmp_path):
    archive = tmp_path / "emtg.tar.gz"
    archive.write_bytes(b"archive")
    checksum = tmp_path / "emtg.tar.gz.sha256"

    write_checksum(archive, checksum)
    validate_checksum(archive, checksum)

    checksum.write_text("0" * 64 + "  different.tar.gz\n", encoding="ascii")
    with pytest.raises(ValueError, match="does not name"):
        validate_checksum(archive, checksum)
