"""Run dependency-free native contracts with the host compiler."""

import shutil
import subprocess

import pytest


pytestmark = pytest.mark.unit


def test_nlp_pure_contract(repository_root, tmp_path):
    compiler = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if compiler is None:
        pytest.skip("No host C++ compiler is available")

    executable = tmp_path / "nlp_pure_contract"
    compile_result = subprocess.run(
        [
            compiler,
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            f"-I{repository_root / 'src' / 'InnerLoop'}",
            str(repository_root / "tests" / "cpp" / "test_nlp_pure_contract.cpp"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        [str(executable)], capture_output=True, text=True, check=False
    )
    assert run_result.returncode == 0, run_result.stderr