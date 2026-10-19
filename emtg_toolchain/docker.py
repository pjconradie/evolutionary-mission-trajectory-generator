"""Docker orchestration for building the EMTG IPOPT runtime archive."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Iterable


PLATFORM = "linux/amd64"
CSPICE_SHA256 = "60a95b51a6472f1afe7e40d77ebdee43c12bb5b8823676ccc74692ddfede06ce"
IMAGE_LABEL = "org.emtg.pytest.toolchain=true"
RUNTIME_IMAGE_LABEL = "org.emtg.archive-runtime=true"
RUNTIME_BASE_IMAGE = (
    "python:3.12-slim-bookworm@"
    "sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254"
)
PACKAGE_CACHE_LABEL = "org.emtg.package-build=true"


def run_command(
    command: list[str],
    *,
    description: str,
    timeout: int = 3600,
    log_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a Docker command and expose stdout/stderr on failure."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except OSError as error:
        raise RuntimeError(f"{description} could not start: {error}") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"{description} exceeded {timeout} seconds") from error
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"{description} failed ({result.returncode}): {detail}")
    return result


def toolchain_image_tag(repository_root: Path) -> str:
    """Return the content-addressed canonical builder image tag."""
    dockerfile = repository_root / "tests" / "docker" / "Dockerfile.toolchain"
    digest = hashlib.sha256(dockerfile.read_bytes() + CSPICE_SHA256.encode("ascii"))
    return f"emtg-pytest-toolchain:{digest.hexdigest()[:16]}"


def source_fingerprint(repository_root: Path) -> str:
    """Hash every source input that affects the EMTGv9 native build."""
    digest = hashlib.sha256()
    inputs = [repository_root / "CMakeLists.txt", repository_root / "src"]
    files = []
    for source in inputs:
        if source.is_file():
            files.append(source)
        else:
            files.extend(path for path in source.rglob("*") if path.is_file())
    for path in sorted(files):
        relative = path.relative_to(repository_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def package_build_cache_identity(repository_root: Path, image: str) -> str:
    """Return the complete identity required for safe CMake-cache reuse."""
    digest = hashlib.sha256()
    for value in (
        image,
        source_fingerprint(repository_root),
        PLATFORM,
        "EMTG_NLP_SOLVER=IPOPT",
        "CSPICE_DIR=/opt/emtg-deps/cspice",
        "GSL_PATH=/opt/emtg-deps/gsl",
        "BOOST_ROOT=/usr",
    ):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def package_build_volume_name(cache_identity: str) -> str:
    """Return an exact Docker volume name for one package-build identity."""
    return f"emtg-package-ipopt-{cache_identity[:16]}"


def ensure_toolchain_image(repository_root: Path) -> str:
    """Build the canonical source-builder image if its tag is absent."""
    if shutil.which("docker") is None:
        raise RuntimeError("Docker CLI is not installed")
    tag = toolchain_image_tag(repository_root)
    inspected = subprocess.run(
        ["docker", "image", "inspect", tag],
        capture_output=True,
        text=True,
        check=False,
    )
    if inspected.returncode == 0:
        return tag

    source_dockerfile = repository_root / "tests" / "docker" / "Dockerfile.toolchain"
    source_cspice = repository_root / "depend" / "cspice-c_pc_linux_gcc_64bit" / "cspice.tar.Z"
    with tempfile.TemporaryDirectory(prefix="emtg-toolchain-context-") as context:
        context_root = Path(context)
        shutil.copy2(source_dockerfile, context_root / "Dockerfile")
        shutil.copy2(source_cspice, context_root / "cspice.tar.Z")
        run_command(
            [
                "docker", "build", "--platform", PLATFORM,
                "--label", IMAGE_LABEL,
                "--build-arg", f"CSPICE_SHA256={CSPICE_SHA256}",
                "--tag", tag,
                str(context_root),
            ],
            description="EMTG toolchain image build",
        )
    return tag


def build_emtg(
    repository_root: Path,
    stage_root: Path,
    *,
    cold: bool = False,
    log_path: Path | None = None,
) -> tuple[str, str]:
    """Compile IPOPT EMTG in the existing builder and stage the executable."""
    image = ensure_toolchain_image(repository_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    cache_identity = package_build_cache_identity(repository_root, image)
    build_directory = "/tmp/emtg-build" if cold else "/build"
    script = r"""
set -eu
rm -rf /tmp/emtg-source
mkdir -p /tmp/emtg-source /stage/bin
if [ -n "${EMTG_PACKAGE_CACHE_ID:-}" ]; then
    if [ -f /build/.emtg-package-cache-id ] \
        && [ "$(cat /build/.emtg-package-cache-id)" != "$EMTG_PACKAGE_CACHE_ID" ]; then
        find /build -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    fi
else
    rm -rf /tmp/emtg-build
fi
ln -s /repo/src /tmp/emtg-source/src
ln -s /repo/tests /tmp/emtg-source/tests
cp /repo/CMakeLists.txt /tmp/emtg-source/CMakeLists.txt
cat >/tmp/emtg-source/EMTG-Config.cmake <<'CMAKE'
set(CSPICE_DIR /opt/emtg-deps/cspice)
set(SNOPT_ROOT_DIR /tmp/emtg-intentionally-missing-snopt)
set(GSL_PATH /opt/emtg-deps/gsl)
set(BOOST_ROOT /usr)
set(Boost_NO_BOOST_CMAKE ON)
CMAKE
cmake -S /tmp/emtg-source -B "$EMTG_BUILD_DIRECTORY" -DEMTG_NLP_SOLVER=IPOPT
cmake --build "$EMTG_BUILD_DIRECTORY" --target EMTGv9 -j2
install -m 755 "$EMTG_BUILD_DIRECTORY"/src/EMTGv9 /stage/bin/EMTGv9
if [ -n "${EMTG_PACKAGE_CACHE_ID:-}" ]; then
    printf '%s\n' "$EMTG_PACKAGE_CACHE_ID" >/build/.emtg-package-cache-id
fi
ldd /stage/bin/EMTGv9 >/stage/EMTGv9.ldd
dpkg-query -W -f='${Package}\t${Version}\n' \
  coinor-libipopt1v5 libgsl27 libboost-filesystem1.74.0 \
  libboost-system1.74.0 libboost-serialization1.74.0 \
  libgomp1 libgfortran5 csh >/stage/runtime-packages.tsv
"""
    command = [
        "docker", "run", "--rm", "--platform", PLATFORM,
        "--mount", f"type=bind,src={repository_root.resolve()},dst=/repo,readonly",
        "--mount", f"type=bind,src={stage_root.resolve()},dst=/stage",
    ]
    if cold:
        command.extend(["--env", f"EMTG_BUILD_DIRECTORY={build_directory}"])
    else:
        volume_name = package_build_volume_name(cache_identity)
        run_command(
            ["docker", "volume", "create", "--label", PACKAGE_CACHE_LABEL, volume_name],
            description=f"package build-cache volume creation ({volume_name})",
            timeout=30,
        )
        command.extend(
            [
                "--mount", f"type=volume,src={volume_name},dst=/build",
                "--env", f"EMTG_PACKAGE_CACHE_ID={cache_identity}",
                "--env", f"EMTG_BUILD_DIRECTORY={build_directory}",
            ]
        )
    command.extend([image, "sh", "-c", script])
    run_command(
        command,
        description="EMTG IPOPT build",
        log_path=log_path,
    )
    ldd_output = (stage_root / "EMTGv9.ldd").read_text(encoding="utf-8")
    package_versions = (stage_root / "runtime-packages.tsv").read_text(encoding="utf-8")
    return ldd_output, package_versions


def build_archive_runtime_image(
    archive_path: Path,
    packages: Iterable[str],
    *,
    log_path: Path | None = None,
) -> str:
    """Cold-build a compiler-free Bookworm image containing one EMTG archive."""
    package_arguments = " ".join(packages)
    archive_digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()[:16]
    tag = f"emtg-archive-runtime:{archive_digest}-{uuid.uuid4().hex[:8]}"
    with tempfile.TemporaryDirectory(prefix="emtg-archive-runtime-context-") as context:
        context_root = Path(context)
        shutil.copy2(archive_path, context_root / "emtg.tar.gz")
        (context_root / "Dockerfile").write_text(
            f"""FROM {RUNTIME_BASE_IMAGE}

RUN apt-get update -qq \\
    && DEBIAN_FRONTEND=noninteractive apt-get install -qq -y --no-install-recommends \\
        tar {package_arguments} \\
    && rm -rf /var/lib/apt/lists/*

COPY emtg.tar.gz /tmp/emtg.tar.gz
RUN mkdir -p /opt/toolkit \\
    && tar -xzf /tmp/emtg.tar.gz -C /opt/toolkit \\
    && test -x /opt/toolkit/emtg/bin/EMTGv9 \\
    && rm /tmp/emtg.tar.gz \\
    && ! command -v cmake \\
    && ! command -v gcc \\
    && ! command -v g++

LABEL {RUNTIME_IMAGE_LABEL}
""",
            encoding="utf-8",
        )
        run_command(
            [
                "docker", "build", "--no-cache", "--platform", PLATFORM,
                "--label", RUNTIME_IMAGE_LABEL,
                "--tag", tag,
                str(context_root),
            ],
            description="clean EMTG archive runtime image build",
            log_path=log_path,
        )
    return tag


def remove_image(tag: str) -> None:
    """Remove one exact test-only image tag."""
    run_command(
        ["docker", "image", "rm", "--force", tag],
        description=f"archive runtime image removal ({tag})",
        timeout=60,
    )


def run_archive_runtime(
    image: str,
    work_directory: Path,
    options_name: str,
    timeout_seconds: int,
    *,
    mount_path: str = "/work",
) -> subprocess.CompletedProcess[str]:
    """Run the packaged executable in an isolated clean-runtime container."""
    if not mount_path.startswith("/"):
        raise ValueError("archive runtime mount path must be absolute")
    command = [
        "docker", "run", "--rm", "--platform", PLATFORM,
        "--mount", f"type=bind,src={work_directory.resolve()},dst={mount_path}",
        image,
        "sh", "-c",
        (
            f"cd {mount_path} && timeout {timeout_seconds} "
            f"/opt/toolkit/emtg/bin/EMTGv9 {mount_path}/{options_name}"
        ),
    ]
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds + 120,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"archive runtime container exceeded {timeout_seconds + 120} seconds"
        ) from error
