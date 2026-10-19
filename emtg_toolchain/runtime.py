"""Runtime-linkage validation and manifest rendering for EMTG archives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


BASE_OS = "Debian 12 Bookworm"
TARGET_PLATFORM = "linux/amd64"
REQUIRED_RUNTIME_PACKAGES = (
    "coinor-libipopt1v5",
    "libgsl27",
    "libboost-filesystem1.74.0",
    "libboost-system1.74.0",
    "libboost-serialization1.74.0",
    "libgomp1",
    "libgfortran5",
    "csh",
)
_REQUIRED_LINKAGE_PACKAGES = ("coinor-libipopt1v5",)
_ALWAYS_REQUIRED_PACKAGES = ("csh",)

_LIBRARY_PACKAGES = {
    "libipopt.so": "coinor-libipopt1v5",
    "libgsl.so": "libgsl27",
    "libboost_filesystem.so": "libboost-filesystem1.74.0",
    "libboost_system.so": "libboost-system1.74.0",
    "libboost_serialization.so": "libboost-serialization1.74.0",
    "libgomp.so": "libgomp1",
    "libgfortran.so": "libgfortran5",
}


@dataclass(frozen=True)
class LinkageReport:
    """Validated dynamic-linkage information for the packaged executable."""

    ldd_output: str
    packages: tuple[str, ...]


def validate_ldd_output(ldd_output: str) -> LinkageReport:
    """Reject unsupported linkage and return required runtime package names."""
    normalized = ldd_output.lower()
    forbidden = {
        "not found": "unresolved shared library",
        "snopt": "SNOPT dependency",
        "libcspice.so": "dynamic CSPICE dependency",
        "/opt/emtg-deps": "builder-prefix dependency",
    }
    for needle, description in forbidden.items():
        if needle in normalized:
            raise ValueError(f"EMTGv9 linkage contains {description}: {needle}")

    detected = {
        package
        for library, package in _LIBRARY_PACKAGES.items()
        if library in normalized
    }
    missing = set(_REQUIRED_LINKAGE_PACKAGES) - detected
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"EMTGv9 linkage is missing required runtime libraries: {names}")

    packages = tuple(
        package
        for package in REQUIRED_RUNTIME_PACKAGES
        if package in detected or package in _ALWAYS_REQUIRED_PACKAGES
    )
    return LinkageReport(ldd_output=ldd_output, packages=packages)


def render_runtime_requirements(
    report: LinkageReport,
    *,
    commit_sha: str,
    build_time: datetime | None = None,
) -> str:
    """Render the runtime manifest shipped inside the archive."""
    timestamp = (build_time or datetime.now(timezone.utc)).replace(microsecond=0)
    package_lines = "\n".join(f"- `{package}`" for package in report.packages)
    return f"""# EMTG IPOPT Runtime Requirements

Target platform: `{TARGET_PLATFORM}`

Base OS: `{BASE_OS}`

Build commit: `{commit_sha}`

Build time: `{timestamp.isoformat().replace("+00:00", "Z")}`

Install these packages in the ADSGNC Debian runtime image:

{package_lines}

The archive does not include mission-specific SPICE SPK kernels. ADSGNC must
provide those kernels and all request-specific mission inputs separately.

## Verified dynamic linkage

```text
{report.ldd_output.rstrip()}
```
"""


def runtime_packages_as_apt_arguments(packages: Iterable[str]) -> list[str]:
    """Return a stable package list suitable for non-interactive apt install."""
    return list(dict.fromkeys(packages))


def parse_runtime_requirements(content: str) -> tuple[str, ...]:
    """Read the package list from a generated runtime requirements document."""
    packages = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- `") and stripped.endswith("`"):
            packages.append(stripped[3:-1])
    if not packages:
        raise ValueError("runtime requirements document does not declare packages")
    return tuple(runtime_packages_as_apt_arguments(packages))
