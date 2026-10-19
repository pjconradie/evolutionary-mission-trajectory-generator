"""Unit tests for archive CLI validation and publication."""

import pytest

from emtg_toolchain import cli


pytestmark = pytest.mark.unit


LDD_OUTPUT = """\
libipopt.so.1 => /lib/libipopt.so.1
libgsl.so.27 => /lib/libgsl.so.27
libboost_filesystem.so.1.74.0 => /lib/libboost_filesystem.so.1.74.0
libboost_system.so.1.74.0 => /lib/libboost_system.so.1.74.0
libboost_serialization.so.1.74.0 => /lib/libboost_serialization.so.1.74.0
libgomp.so.1 => /lib/libgomp.so.1
libgfortran.so.5 => /lib/libgfortran.so.5
"""


def _repository(tmp_path):
    repository = tmp_path / "repository"
    (repository / "tests" / "docker").mkdir(parents=True)
    (repository / "depend" / "cspice-c_pc_linux_gcc_64bit").mkdir(parents=True)
    (repository / "src").mkdir()
    (repository / "Universe" / "ephemeris_files").mkdir(parents=True)
    (repository / "HardwareModels").mkdir()
    (repository / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.8)\n")
    (repository / "tests" / "docker" / "Dockerfile.toolchain").write_text("FROM scratch\n")
    (repository / "depend" / "cspice-c_pc_linux_gcc_64bit" / "cspice.tar.Z").write_bytes(b"cspice")
    (repository / "Universe" / "Earth.emtg_universe").write_text("Earth\n")
    (repository / "Universe" / "ephemeris_files" / "naif0012.tls").write_text("tls\n")
    (repository / "Universe" / "ephemeris_files" / "pck00010.tpc").write_text("tpc\n")
    (repository / "HardwareModels" / "hardware.emtg_launchvehicleopt").write_text("hardware\n")
    return repository


def test_parser_rejects_non_archive_output(tmp_path):
    repository = _repository(tmp_path)
    parser = cli.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            ["package", "--emtg-repo", str(repository), "--output", str(tmp_path / "bad.zip")]
        )


def test_parser_rejects_literal_release_version_placeholder(tmp_path):
    repository = _repository(tmp_path)
    parser = cli.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "package",
                "--emtg-repo",
                str(repository),
                "--output",
                str(tmp_path / "emtg-ipopt-<version>.tar.gz"),
            ]
        )


def test_parser_rejects_existing_archive_or_checksum(tmp_path):
    repository = _repository(tmp_path)
    output = tmp_path / "emtg.tar.gz"
    output.write_bytes(b"existing")
    parser = cli.build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(
            ["package", "--emtg-repo", str(repository), "--output", str(output)]
        )


def test_parser_accepts_cold_package_build(tmp_path):
    repository = _repository(tmp_path)
    parser = cli.build_parser()

    arguments = parser.parse_args(
        [
            "package",
            "--cold",
            "--emtg-repo",
            str(repository),
            "--output",
            str(tmp_path / "emtg.tar.gz"),
        ]
    )

    assert arguments.cold


def test_package_publishes_archive_and_checksum_after_validation(
    tmp_path, monkeypatch, capsys
):
    repository = _repository(tmp_path)
    output = tmp_path / "output" / "emtg.tar.gz"

    def fake_build(_repository_root, stage_root, **_kwargs):
        executable = stage_root / "bin" / "EMTGv9"
        executable.parent.mkdir(parents=True)
        executable.write_text("#!/bin/sh\n")
        executable.chmod(0o755)
        return LDD_OUTPUT, ""

    monkeypatch.setattr(cli, "build_emtg", fake_build)
    monkeypatch.setattr(cli, "_commit_sha", lambda _root: "abc123")

    cli.package(repository, output)

    assert output.is_file()
    assert output.with_name("emtg.tar.gz.sha256").is_file()
    assert "[1/5] Building IPOPT EMTG (hot build)" in capsys.readouterr().out


def test_package_does_not_publish_outputs_when_build_fails(tmp_path, monkeypatch):
    repository = _repository(tmp_path)
    output = tmp_path / "output" / "emtg.tar.gz"
    monkeypatch.setattr(
        cli,
        "build_emtg",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("build failed")),
    )

    with pytest.raises(RuntimeError, match="build failed"):
        cli.package(repository, output)

    assert not output.exists()
    assert not output.with_name("emtg.tar.gz.sha256").exists()
