"""Unit tests for runtime linkage and dependency manifests."""

from datetime import datetime, timezone

import pytest

from emtg_toolchain.runtime import (
    REQUIRED_RUNTIME_PACKAGES,
    parse_runtime_requirements,
    render_runtime_requirements,
    runtime_packages_as_apt_arguments,
    validate_ldd_output,
)


pytestmark = pytest.mark.unit


LDD_OUTPUT = """\
linux-vdso.so.1 (0x0000)
libipopt.so.1 => /lib/libipopt.so.1 (0x0001)
libgsl.so.27 => /lib/libgsl.so.27 (0x0002)
libboost_filesystem.so.1.74.0 => /lib/libboost_filesystem.so.1.74.0 (0x0003)
libboost_system.so.1.74.0 => /lib/libboost_system.so.1.74.0 (0x0004)
libboost_serialization.so.1.74.0 => /lib/libboost_serialization.so.1.74.0 (0x0005)
libgomp.so.1 => /lib/libgomp.so.1 (0x0006)
libgfortran.so.5 => /lib/libgfortran.so.5 (0x0007)
"""


def test_valid_linkage_produces_required_runtime_packages():
    report = validate_ldd_output(LDD_OUTPUT)

    assert report.packages == REQUIRED_RUNTIME_PACKAGES


def test_linkage_requires_ipopt_but_uses_only_detected_libraries():
    report = validate_ldd_output("libipopt.so.1 => /lib/libipopt.so.1\n")

    assert report.packages == ("coinor-libipopt1v5", "csh")


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        ("libmissing.so => not found", "unresolved shared library"),
        ("libsnopt7.so => /lib/libsnopt7.so", "SNOPT dependency"),
        ("libcspice.so => /lib/libcspice.so", "dynamic CSPICE dependency"),
        ("libgsl.so => /opt/emtg-deps/gsl/libgsl.so", "builder-prefix dependency"),
    ],
)
def test_invalid_linkage_is_rejected(extra, expected):
    with pytest.raises(ValueError, match=expected):
        validate_ldd_output(f"{LDD_OUTPUT}{extra}\n")


def test_runtime_manifest_records_provenance_and_linkage():
    report = validate_ldd_output(LDD_OUTPUT)
    manifest = render_runtime_requirements(
        report,
        commit_sha="abc123",
        build_mode="cold",
        build_time=datetime(2026, 10, 19, tzinfo=timezone.utc),
    )

    assert "linux/amd64" in manifest
    assert "2026-10-19T00:00:00Z" in manifest
    assert "Build mode: `cold`" in manifest
    assert "`coinor-libipopt1v5`" in manifest
    assert LDD_OUTPUT.rstrip() in manifest


def test_apt_arguments_preserve_first_occurrence_order():
    assert runtime_packages_as_apt_arguments(["a", "b", "a"]) == ["a", "b"]


def test_runtime_requirements_parser_reads_generated_package_list():
    report = validate_ldd_output(LDD_OUTPUT)
    requirements = render_runtime_requirements(
        report, commit_sha="abc123", build_mode="cold"
    )

    assert parse_runtime_requirements(requirements) == REQUIRED_RUNTIME_PACKAGES


def test_runtime_requirements_parser_rejects_missing_package_list():
    with pytest.raises(ValueError, match="does not declare packages"):
        parse_runtime_requirements("# No packages\n")
