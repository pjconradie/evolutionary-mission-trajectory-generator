"""Release-baseline evidence for an existing EMTG runtime archive."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


_BUILD_COMMIT = re.compile(r"^Build commit: `(?P<commit>[^`]+)`$", re.MULTILINE)
_BUILD_MODE = re.compile(r"^Build mode: `(?P<mode>cold|hot)`$", re.MULTILINE)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_commit_from_requirements(requirements: str) -> str:
    """Return the source revision recorded in an archive manifest."""
    match = _BUILD_COMMIT.search(requirements)
    if match is None:
        raise ValueError("runtime requirements do not declare the build commit")
    return match.group("commit")


def build_mode_from_requirements(requirements: str) -> str:
    """Return the package-build mode recorded in an archive manifest."""
    match = _BUILD_MODE.search(requirements)
    if match is None:
        raise ValueError("runtime requirements do not declare the build mode")
    return match.group("mode")


def release_baseline_record(
    *,
    archive: Path,
    requirements: str,
    verification: dict,
    verification_reference: Path,
    evidence_root: Path,
) -> dict:
    """Create immutable-identifying evidence for one verified release archive."""
    build_mode = build_mode_from_requirements(requirements)
    if build_mode != "cold":
        raise ValueError(
            f"release archive must have a cold build mode, not {build_mode}"
        )
    return {
        "version": 1,
        "archive": {
            "filename": archive.name,
            "path": str(archive),
            "sha256": sha256_file(archive),
        },
        "archive_build_mode": build_mode,
        "source_commit": build_commit_from_requirements(requirements),
        "runtime_requirements": {"sha256": hashlib.sha256(
            requirements.encode("utf-8")
        ).hexdigest()},
        "tutorial_verification_reference": {
            "path": str(verification_reference),
            "sha256": sha256_file(verification_reference),
        },
        "verification": {
            "path": str(evidence_root / "verification.json"),
            "case_count": verification["case_count"],
            "stage_count": verification["stage_count"],
            "acceptable": verification["acceptable"],
        },
        "evidence_directory": str(evidence_root),
    }
