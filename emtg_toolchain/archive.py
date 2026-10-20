"""Safe staging and tarball creation for the EMTG runtime payload."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


ARCHIVE_ROOT = "emtg"
EPHEMERIS_FILES = ("naif0012.tls", "pck00010.tpc")


@dataclass(frozen=True)
class ArchiveEntry:
    """One source file and its destination beneath the archive root."""

    source: Path
    destination: PurePosixPath


def _archive_destination(*parts: str) -> PurePosixPath:
    return PurePosixPath(ARCHIVE_ROOT, *parts)


def build_payload_manifest(repository_root: Path, executable: Path) -> list[ArchiveEntry]:
    """Return the complete allowlisted runtime payload."""
    universe = repository_root / "Universe"
    hardware = repository_root / "HardwareModels"
    entries = [
        ArchiveEntry(executable, _archive_destination("bin", "EMTGv9")),
    ]
    entries.extend(
        ArchiveEntry(source, _archive_destination("universe", source.name))
        for source in sorted(universe.glob("*.emtg_universe"))
    )
    entries.extend(
        ArchiveEntry(
            universe / "ephemeris_files" / name,
            _archive_destination("universe", "ephemeris_data", name),
        )
        for name in EPHEMERIS_FILES
    )
    entries.extend(
        ArchiveEntry(source, _archive_destination("hardware", source.name))
        for source in sorted(hardware.iterdir())
        if source.is_file()
    )
    return entries


def validate_manifest(entries: Iterable[ArchiveEntry]) -> None:
    """Validate source availability and archive-relative destinations."""
    destinations: set[PurePosixPath] = set()
    for entry in entries:
        if not entry.source.is_file():
            raise ValueError(f"required archive input is missing: {entry.source}")
        destination = entry.destination
        if destination.is_absolute() or ".." in destination.parts:
            raise ValueError(f"unsafe archive destination: {destination}")
        if destination.parts[0] != ARCHIVE_ROOT:
            raise ValueError(f"archive destination must be under {ARCHIVE_ROOT}/: {destination}")
        if destination in destinations:
            raise ValueError(f"duplicate archive destination: {destination}")
        destinations.add(destination)


def stage_payload(entries: Iterable[ArchiveEntry], stage_root: Path) -> None:
    """Copy the allowlisted payload into a staging directory."""
    validate_manifest(entries)
    for entry in entries:
        destination = stage_root.joinpath(*entry.destination.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry.source, destination)
        if entry.destination == _archive_destination("bin", "EMTGv9"):
            destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def write_text_file(stage_root: Path, relative_path: PurePosixPath, content: str) -> Path:
    """Write a UTF-8 text file beneath the archive root."""
    destination = stage_root.joinpath(*relative_path.parts)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"unsafe archive destination: {relative_path}")
    if relative_path.parts[0] != ARCHIVE_ROOT:
        raise ValueError(f"archive destination must be under {ARCHIVE_ROOT}/: {relative_path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def _tar_filter(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    info.mtime = 0
    return info


def validate_archive(path: Path) -> None:
    """Validate tar member safety, root layout, and executable mode."""
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        if not members:
            raise ValueError("archive is empty")
        names = [PurePosixPath(member.name) for member in members]
        for name in names:
            if name.is_absolute() or ".." in name.parts:
                raise ValueError(f"unsafe archive member: {name}")
            if not name.parts or name.parts[0] != ARCHIVE_ROOT:
                raise ValueError(f"archive member is outside {ARCHIVE_ROOT}/: {name}")
        executable = archive.getmember(f"{ARCHIVE_ROOT}/bin/EMTGv9")
        if not executable.mode & stat.S_IXUSR:
            raise ValueError("archive EMTGv9 is not executable")


def create_archive(stage_root: Path, destination: Path) -> None:
    """Create a deterministic gzip tarball from a validated staging root."""
    archive_root = stage_root / ARCHIVE_ROOT
    if not archive_root.is_dir():
        raise ValueError(f"staging root does not contain {ARCHIVE_ROOT}/")
    with tarfile.open(destination, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        archive.add(archive_root, arcname=ARCHIVE_ROOT, filter=_tar_filter)
    validate_archive(destination)


def write_checksum(archive_path: Path, checksum_path: Path) -> None:
    """Write a standard sha256sum-compatible checksum manifest."""
    digest = hashlib.sha256()
    with archive_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    checksum_path.write_text(
        f"{digest.hexdigest()}  {archive_path.name}\n",
        encoding="ascii",
    )


def validate_checksum(archive_path: Path, checksum_path: Path) -> None:
    """Verify that a generated checksum manifest names and hashes the archive."""
    expected = checksum_path.read_text(encoding="ascii").strip().split()
    if len(expected) != 2 or expected[1] != archive_path.name:
        raise ValueError("checksum manifest does not name the archive")
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if digest != expected[0]:
        raise ValueError("checksum manifest does not match the archive")


def read_archive_text(path: Path, relative_path: PurePosixPath) -> str:
    """Read one UTF-8 file from the validated archive root."""
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"unsafe archive path: {relative_path}")
    if relative_path.parts[0] != ARCHIVE_ROOT:
        raise ValueError(f"archive path must be under {ARCHIVE_ROOT}/: {relative_path}")
    with tarfile.open(path, "r:gz") as archive:
        member = archive.extractfile(relative_path.as_posix())
        if member is None:
            raise ValueError(f"archive does not contain {relative_path}")
        return member.read().decode("utf-8")
