"""Unit tests for content-addressed package build-cache identities."""

import subprocess

import pytest

from emtg_toolchain import docker
from emtg_toolchain.docker import (
    package_build_cache_identity,
    package_build_volume_name,
    run_archive_runtime,
    source_fingerprint,
)


pytestmark = pytest.mark.unit


def _source_tree(tmp_path):
    repository = tmp_path / "repository"
    (repository / "src").mkdir(parents=True)
    (repository / "CMakeLists.txt").write_text("project(EMTG)\n")
    (repository / "src" / "main.cpp").write_text("int main() { return 0; }\n")
    return repository


def test_source_fingerprint_is_stable_and_changes_with_source_content(tmp_path):
    repository = _source_tree(tmp_path)

    first = source_fingerprint(repository)
    assert source_fingerprint(repository) == first

    (repository / "src" / "main.cpp").write_text("int main() { return 1; }\n")
    assert source_fingerprint(repository) != first


def test_package_cache_identity_includes_builder_and_source_inputs(tmp_path):
    repository = _source_tree(tmp_path)
    first = package_build_cache_identity(repository, "builder:one")
    second = package_build_cache_identity(repository, "builder:two")

    assert first != second
    assert package_build_volume_name(first) == f"emtg-package-ipopt-{first[:16]}"


def test_archive_runtime_mounts_at_requested_absolute_path(tmp_path, monkeypatch):
    observed = {}

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(docker.subprocess, "run", fake_run)

    run_archive_runtime(
        "archive-runtime:test",
        tmp_path,
        "case.emtgopt",
        60,
        mount_path="/artifacts",
    )

    command = observed["command"]
    assert f"type=bind,src={tmp_path.resolve()},dst=/artifacts" in command
    assert command[-1] == (
        "cd /artifacts && timeout 60 "
        "/opt/toolkit/emtg/bin/EMTGv9 /artifacts/case.emtgopt"
    )


def test_archive_runtime_rejects_relative_mount_path(tmp_path):
    with pytest.raises(ValueError, match="must be absolute"):
        run_archive_runtime(
            "archive-runtime:test",
            tmp_path,
            "case.emtgopt",
            60,
            mount_path="artifacts",
        )
