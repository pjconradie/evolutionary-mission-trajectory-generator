"""Command-line interface for creating EMTG IPOPT runtime archives."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .archive import (
    ARCHIVE_ROOT,
    ArchiveEntry,
    build_payload_manifest,
    create_archive,
    stage_payload,
    validate_archive,
    validate_checksum,
    write_checksum,
    write_text_file,
)
from .docker import build_emtg
from .runtime import render_runtime_requirements, validate_ldd_output


def _repository_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    required = (
        root / "CMakeLists.txt",
        root / "src",
        root / "tests" / "docker" / "Dockerfile.toolchain",
        root / "depend" / "cspice-c_pc_linux_gcc_64bit" / "cspice.tar.Z",
        root / "Universe",
        root / "HardwareModels",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise argparse.ArgumentTypeError(
            "not an EMTG repository; missing: " + ", ".join(missing)
        )
    return root


def _output_path(value: str) -> Path:
    output = Path(value).expanduser().resolve()
    if output.suffixes[-2:] != [".tar", ".gz"]:
        raise argparse.ArgumentTypeError("output must end in .tar.gz")
    if "<" in output.name or ">" in output.name:
        raise argparse.ArgumentTypeError(
            "output filename must use a concrete release version, not <version>"
        )
    if output.exists() or output.with_name(f"{output.name}.sha256").exists():
        raise argparse.ArgumentTypeError("output archive or checksum already exists")
    return output


def _commit_sha(repository_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("could not determine EMTG Git commit SHA")
    return result.stdout.strip()


def _archive_readme() -> str:
    return """# EMTG IPOPT Runtime Archive

Extract this archive into `/opt/toolkit` to obtain:

```text
/opt/toolkit/emtg/bin/EMTGv9
```

Install the Debian packages in `RUNTIME_REQUIREMENTS.txt` before running EMTG.
Invoke the fixed executable with an options file and no shell:

```bash
/opt/toolkit/emtg/bin/EMTGv9 /opt/work/request.emtgopt
```

The archive includes base universe and standard public hardware data. The
third-party deployment environment must provide request-specific inputs and
mission SPICE kernels, keep them read-only where possible, and use an isolated
writable run directory for outputs.
"""


def package(
    repository_root: Path,
    output: Path,
    *,
    cold: bool = False,
    build_log_path: Path | None = None,
) -> None:
    """Build, validate, and publish a runtime archive and checksum."""
    output.parent.mkdir(parents=True, exist_ok=True)
    build_mode = "cold" if cold else "hot"
    print(f"[1/5] Building IPOPT EMTG ({build_mode} build)")
    with tempfile.TemporaryDirectory(
        prefix=f".{output.stem}-", dir=output.parent
    ) as temporary:
        temporary_root = Path(temporary)
        build_stage = temporary_root / "build"
        ldd_output, package_versions = build_emtg(
            repository_root,
            build_stage,
            cold=cold,
            log_path=build_log_path,
        )
        print("[2/5] Validating EMTG runtime linkage")
        if build_log_path is not None:
            build_log_path.with_name("source-EMTGv9.ldd").write_text(
                ldd_output,
                encoding="utf-8",
            )
            build_log_path.with_name("source-runtime-packages.tsv").write_text(
                package_versions,
                encoding="utf-8",
            )
        report = validate_ldd_output(ldd_output)

        print("[3/5] Staging archive runtime payload")
        archive_stage = temporary_root / "archive"
        entries: list[ArchiveEntry] = build_payload_manifest(
            repository_root, build_stage / "bin" / "EMTGv9"
        )
        stage_payload(entries, archive_stage)
        write_text_file(
            archive_stage,
            Path(ARCHIVE_ROOT) / "RUNTIME_REQUIREMENTS.txt",
            render_runtime_requirements(
                report,
                commit_sha=_commit_sha(repository_root),
                build_mode=build_mode,
                build_time=datetime.now(timezone.utc),
            ),
        )
        write_text_file(
            archive_stage,
            Path(ARCHIVE_ROOT) / "README.md",
            _archive_readme(),
        )

        print("[4/5] Creating archive and SHA-256 checksum")
        temporary_archive = temporary_root / output.name
        temporary_checksum = temporary_root / f"{output.name}.sha256"
        create_archive(archive_stage, temporary_archive)
        write_checksum(temporary_archive, temporary_checksum)
        validate_archive(temporary_archive)
        validate_checksum(temporary_archive, temporary_checksum)
        print("[5/5] Publishing validated archive")
        shutil.move(str(temporary_archive), output)
        shutil.move(str(temporary_checksum), output.with_name(f"{output.name}.sha256"))


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(prog="emtg-toolchain")
    commands = parser.add_subparsers(dest="command", required=True)
    package_parser = commands.add_parser("package", help="create an EMTG runtime archive")
    package_parser.add_argument("--emtg-repo", required=True, type=_repository_root)
    package_parser.add_argument("--output", required=True, type=_output_path)
    package_parser.add_argument(
        "--cold",
        action="store_true",
        help="compile EMTG without reusing the package CMake build cache",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command and present expected operational errors concisely."""
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "package":
            package(arguments.emtg_repo, arguments.output, cold=arguments.cold)
            checksum = arguments.output.with_name(f"{arguments.output.name}.sha256")
            print(f"Published EMTG archive: {arguments.output}")
            print(f"Published SHA-256 checksum: {checksum}")
            print(
                "Next: baseline this exact archive with "
                "--release-archive after verifying its checksum."
            )
            return 0
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(1, f"emtg-toolchain: error: {error}\n")
    parser.error(f"unsupported command: {arguments.command}")
    return 2
