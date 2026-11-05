"""Host-runnable, dependency-free unit coverage for SPICE_meta_kernel.

Most of these tests exercise the pure-Python PyEMTG/MissionOptions.py mirror
of the new ``SPICE_meta_kernel`` option. One test
(``test_spice_meta_kernel_round_trips_through_native_missionoptions``) instead
host-compiles and runs the real C++ ``missionoptions.cpp`` parse/write path
via the pre-existing ``src/Testing/missionoptions_tests`` testbed driver,
mirroring the pattern used by tests/test_cpp_contracts.py. ``doubleType.h``'s
GSAD dependency is guarded by ``#ifdef AD_INSTRUMENTATION`` (off by default),
so this translation unit only needs ``boost::filesystem``, not GSL/GSAD/
CSPICE, and is therefore safe to host-compile here.

Verifying the actual CSPICE load/unload/error-handling behavior still
requires the compiled EMTGv9 executable and a real CSPICE runtime, so that
coverage lives in tests/integration/test_meta_kernel_integration.py instead,
under the Docker toolchain image.
"""

import shutil
import subprocess

import MissionOptions
import pytest


pytestmark = pytest.mark.unit


MINIMAL_OPTIONS_HEADER = "#EMTGv9 .emtgopt file version 2\n\n"


def _write_minimal_options_file(path, extra_lines=()):
    with open(path, "w") as options_file:
        options_file.write(MINIMAL_OPTIONS_HEADER)
        for line in extra_lines:
            options_file.write(line + "\n")
    return path


def test_default_spice_meta_kernel_is_empty(tmp_path):
    options_path = _write_minimal_options_file(tmp_path / "default.emtgopt")

    options = MissionOptions.MissionOptions(str(options_path))

    assert options.SPICE_meta_kernel == ""


def test_parsing_spice_meta_kernel_round_trips_through_pyemtg(tmp_path):
    source_path = _write_minimal_options_file(
        tmp_path / "source.emtgopt",
        extra_lines=["SPICE_meta_kernel meta_kernel.tm"],
    )

    options = MissionOptions.MissionOptions(str(source_path))
    assert options.SPICE_meta_kernel == "meta_kernel.tm"

    written_path = tmp_path / "written.emtgopt"
    options.write_options_file(str(written_path))

    reread = MissionOptions.MissionOptions(str(written_path))
    assert reread.SPICE_meta_kernel == "meta_kernel.tm"


def test_parsing_spice_meta_kernel_round_trips_nested_path(tmp_path):
    nested_value = "/opt/emtg/input/kernel-set/meta_kernel.tm"
    source_path = _write_minimal_options_file(
        tmp_path / "source.emtgopt",
        extra_lines=[f"SPICE_meta_kernel {nested_value}"],
    )

    options = MissionOptions.MissionOptions(str(source_path))
    assert options.SPICE_meta_kernel == nested_value

    written_path = tmp_path / "written.emtgopt"
    options.write_options_file(str(written_path))

    reread = MissionOptions.MissionOptions(str(written_path))
    assert reread.SPICE_meta_kernel == nested_value


def test_default_spice_meta_kernel_is_omitted_unless_writeall(tmp_path):
    options_path = _write_minimal_options_file(tmp_path / "default.emtgopt")
    options = MissionOptions.MissionOptions(str(options_path))

    without_writeall = tmp_path / "without_writeall.emtgopt"
    options.write_options_file(str(without_writeall), writeAll=False)
    assert "SPICE_meta_kernel" not in without_writeall.read_text()

    with_writeall = tmp_path / "with_writeall.emtgopt"
    options.write_options_file(str(with_writeall), writeAll=True)
    assert "SPICE_meta_kernel " in with_writeall.read_text()


def test_empty_spice_meta_kernel_survives_writeall_round_trip(tmp_path):
    # write_options_file(writeAll=True) emits "SPICE_meta_kernel \n" for an
    # empty value (trailing space, no token after it). The reader's
    # line.rstrip("\n\r ") strips that trailing space before splitting, so a
    # naive linecell[1] lookup would raise IndexError instead of parsing back
    # to "". This is the regression this test guards against.
    options_path = _write_minimal_options_file(tmp_path / "default.emtgopt")
    options = MissionOptions.MissionOptions(str(options_path))
    assert options.SPICE_meta_kernel == ""

    with_writeall = tmp_path / "with_writeall.emtgopt"
    options.write_options_file(str(with_writeall), writeAll=True)

    reread = MissionOptions.MissionOptions(str(with_writeall))
    assert reread.SPICE_meta_kernel == ""


def _compile_missionoptions_testbed(repository_root, build_dir, extra_boost_flags=()):
    compiler = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        return None, None, "No host C++ compiler is available"

    sources = [
        repository_root / "src" / "Core" / "missionoptions.cpp",
        repository_root / "src" / "Core" / "journeyoptions.cpp",
        repository_root / "src" / "Utilities" / "file_utilities.cpp",
        repository_root
        / "src"
        / "Testing"
        / "missionoptions_tests"
        / "missionoptions_testbed_driver.cpp",
    ]
    executable = build_dir / "missionoptions_testbed"
    compile_result = subprocess.run(
        [
            compiler,
            "-std=c++17",
            f"-I{repository_root / 'src' / 'Core'}",
            f"-I{repository_root / 'src' / 'Utilities'}",
            f"-I{repository_root / 'src' / 'Math'}",
            *extra_boost_flags,
            *[str(source) for source in sources],
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if compile_result.returncode != 0:
        return None, compile_result, None
    return executable, compile_result, None


def test_spice_meta_kernel_round_trips_through_native_missionoptions(
    repository_root, tmp_path
):
    # Exercises the real C++ parse/write path (not just PyEMTG) by
    # host-compiling the pre-existing missionoptions_testbed driver
    # (src/Testing/missionoptions_tests/missionoptions_testbed_driver.cpp).
    # doubleType.h's GSAD include is gated behind #ifdef AD_INSTRUMENTATION
    # (off by default), so this is dependency-light: only boost::filesystem
    # is required, no GSL/GSAD/CSPICE.
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    executable, compile_result, skip_reason = _compile_missionoptions_testbed(
        repository_root, build_dir
    )
    if skip_reason is not None:
        pytest.skip(skip_reason)
    if executable is None:
        # Likely a host without boost::filesystem on the default include/lib
        # search path (e.g. a Homebrew install not on the default paths).
        # Retry once with common Homebrew locations before giving up.
        executable, compile_result, skip_reason = _compile_missionoptions_testbed(
            repository_root,
            build_dir,
            extra_boost_flags=(
                "-I/opt/homebrew/opt/boost/include",
                "-L/opt/homebrew/opt/boost/lib",
                "-lboost_filesystem",
            ),
        )
        if executable is None:
            pytest.skip(
                "boost::filesystem is not available to the host compiler: "
                f"{compile_result.stderr}"
            )

    # The driver's working directory layout: it reads the given .emtgopt
    # path and writes tests/newdefault.emtgopt relative to the current
    # working directory, so run it from a scratch directory.
    run_dir = tmp_path / "run"
    (run_dir / "tests").mkdir(parents=True)
    source_options = run_dir / "source.emtgopt"
    source_options.write_text(
        MINIMAL_OPTIONS_HEADER + "SPICE_meta_kernel meta_kernel.tm\n"
    )

    run_result = subprocess.run(
        [str(executable), str(source_options)],
        cwd=run_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert run_result.returncode == 0, run_result.stderr

    written_options = (run_dir / "tests" / "newdefault.emtgopt").read_text()
    assert "SPICE_meta_kernel meta_kernel.tm" in written_options

