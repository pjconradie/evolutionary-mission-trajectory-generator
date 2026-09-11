"""Reusable Docker orchestration for EMTG integration tests."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest


PLATFORM = "linux/amd64"
CHECK_PREFIX = "EMTG_CHECK "
COMMAND_TIMEOUT_SECONDS = 3600
CSPICE_SHA256 = "60a95b51a6472f1afe7e40d77ebdee43c12bb5b8823676ccc74692ddfede06ce"
IMAGE_LABEL = "org.emtg.pytest.toolchain=true"


def docker_available() -> tuple[bool, str]:
    """Return whether the Docker CLI and daemon are available."""
    if shutil.which("docker") is None:
        return False, "Docker CLI is not installed"
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, f"Docker daemon check failed: {error}"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return False, f"Docker daemon is unavailable: {detail}"
    return True, ""


def require_docker() -> None:
    """Skip the current test when Docker cannot be used."""
    available, reason = docker_available()
    if not available:
        pytest.skip(reason)


def parse_checks(output: str) -> dict[str, str]:
    """Parse successful machine-readable checks from probe output."""
    checks = {}
    for line in output.splitlines():
        if line.startswith(CHECK_PREFIX):
            key, value = line[len(CHECK_PREFIX) :].split("=", 1)
            checks[key] = value
    return checks


def _artifact_directory(tmp_path_factory) -> Path:
    configured = os.environ.get("EMTG_TEST_ARTIFACT_DIR")
    directory = (
        Path(configured).expanduser().resolve()
        if configured
        else tmp_path_factory.getbasetemp() / "docker-artifacts"
    )
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _run(command: list[str], *, timeout: int, description: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        pytest.fail(
            f"{description} exceeded {timeout} seconds\n"
            f"stdout:\n{error.stdout or ''}\nstderr:\n{error.stderr or ''}"
        )


def toolchain_image_tag(repository_root: Path) -> str:
    """Return the content-addressed local toolchain image tag."""
    dockerfile = repository_root / "tests" / "docker" / "Dockerfile.toolchain"
    digest = hashlib.sha256()
    digest.update(dockerfile.read_bytes())
    digest.update(CSPICE_SHA256.encode("ascii"))
    return f"emtg-pytest-toolchain:{digest.hexdigest()[:16]}"


def ensure_toolchain_image(repository_root: Path, tmp_path_factory) -> str:
    """Build the content-addressed toolchain image when it is absent."""
    require_docker()
    tag = toolchain_image_tag(repository_root)
    inspect = _run(
        ["docker", "image", "inspect", tag],
        timeout=30,
        description="Toolchain image inspection",
    )
    if inspect.returncode == 0:
        return tag

    context_root = tmp_path_factory.mktemp("emtg-toolchain-context")
    shutil.copy2(
        repository_root / "tests" / "docker" / "Dockerfile.toolchain",
        context_root / "Dockerfile",
    )
    shutil.copy2(
        repository_root
        / "depend"
        / "cspice-c_pc_linux_gcc_64bit"
        / "cspice.tar.Z",
        context_root / "cspice.tar.Z",
    )
    result = _run(
        [
            "docker", "build", "--platform", PLATFORM,
            "--label", IMAGE_LABEL,
            "--build-arg", f"CSPICE_SHA256={CSPICE_SHA256}",
            "--tag", tag,
            str(context_root),
        ],
        timeout=COMMAND_TIMEOUT_SECONDS,
        description="Toolchain image build",
    )
    log = _artifact_directory(tmp_path_factory) / "toolchain-image-build.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        pytest.fail(
            f"Toolchain image build exited with {result.returncode}; log: {log}\n"
            f"stdout tail:\n{result.stdout[-12000:]}\n"
            f"stderr tail:\n{result.stderr[-12000:]}"
        )
    return tag


def build_clean_toolchain_image(repository_root: Path, tmp_path_factory) -> str:
    """Build a uniquely tagged toolchain image without reusable layer cache."""
    require_docker()
    tag = f"{toolchain_image_tag(repository_root)}-clean-{uuid.uuid4().hex}"
    context_root = tmp_path_factory.mktemp("emtg-clean-toolchain-context")
    shutil.copy2(
        repository_root / "tests" / "docker" / "Dockerfile.toolchain",
        context_root / "Dockerfile",
    )
    shutil.copy2(
        repository_root
        / "depend"
        / "cspice-c_pc_linux_gcc_64bit"
        / "cspice.tar.Z",
        context_root / "cspice.tar.Z",
    )
    result = _run(
        [
            "docker", "build", "--no-cache", "--platform", PLATFORM,
            "--label", IMAGE_LABEL,
            "--build-arg", f"CSPICE_SHA256={CSPICE_SHA256}",
            "--tag", tag,
            str(context_root),
        ],
        timeout=COMMAND_TIMEOUT_SECONDS,
        description="Clean toolchain image build",
    )
    log = _artifact_directory(tmp_path_factory) / "clean-toolchain-image-build.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        _run(
            ["docker", "image", "rm", "--force", tag],
            timeout=60,
            description="Partial clean toolchain image removal",
        )
        pytest.fail(
            f"Clean toolchain image build exited with {result.returncode}; log: {log}\n"
            f"stdout tail:\n{result.stdout[-12000:]}\n"
            f"stderr tail:\n{result.stderr[-12000:]}"
        )
    return tag


def remove_toolchain_image(tag: str) -> None:
    """Remove exactly one temporary toolchain image."""
    result = _run(
        ["docker", "image", "rm", "--force", tag],
        timeout=60,
        description="Clean toolchain image removal",
    )
    if result.returncode != 0:
        pytest.fail(result.stderr or result.stdout)


def build_volume_name(image_tag: str, backend: str) -> str:
    """Return an exact-name backend cache volume."""
    image_hash = image_tag.rsplit(":", 1)[-1]
    return f"emtg-pytest-{backend.lower()}-{image_hash}"


@contextlib.contextmanager
def build_volume_lock(volume_name: str):
    """Serialize access to one persistent CMake build volume."""
    lock_path = Path(tempfile.gettempdir()) / f"{volume_name}.lock"
    with lock_path.open("w", encoding="ascii") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def run_probe(
    *,
    image: str,
    repository_root: Path,
    script: str,
    probe_name: str,
    tmp_path_factory,
    build_volume: str | None = None,
    timeout: int = COMMAND_TIMEOUT_SECONDS,
) -> dict[str, str]:
    """Run one probe in a disposable amd64 container and return its checks."""
    require_docker()
    container_name = f"emtg-pytest-{probe_name}-{uuid.uuid4().hex}"
    command = [
        "docker", "run", "--rm", "--name", container_name,
        "--label", "org.emtg.pytest.container=true",
        "--platform", PLATFORM,
        "--mount", f"type=bind,src={repository_root},dst=/repo,readonly",
    ]
    if build_volume:
        create = _run(
            ["docker", "volume", "create", "--label", IMAGE_LABEL, build_volume],
            timeout=30,
            description=f"{probe_name} build-volume creation",
        )
        if create.returncode != 0:
            pytest.fail(create.stderr or create.stdout)
        command.extend(["--mount", f"type=volume,src={build_volume},dst=/build"])
    command.extend([image, "sh", "-c", script])

    lock = build_volume_lock(build_volume) if build_volume else contextlib.nullcontext()
    with lock:
        try:
            result = _run(command, timeout=timeout, description=f"{probe_name} probe")
        finally:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

    log = _artifact_directory(tmp_path_factory) / f"{probe_name}.log"
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        pytest.fail(
            f"{probe_name} probe exited with {result.returncode}; log: {log}\n"
            f"stdout tail:\n{result.stdout[-12000:]}\n"
            f"stderr tail:\n{result.stderr[-12000:]}"
        )
    return parse_checks(result.stdout)
