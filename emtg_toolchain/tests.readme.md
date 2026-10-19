
Test collection
```zsh
python -m pytest tests/emtg_toolchain/unit --unit --collect-only -q
```

```zsh
% python -m pytest tests/emtg_toolchain/unit --unit --collect-only -q
tests/emtg_toolchain/unit/test_emtg_archive_unit.py::test_manifest_contains_only_allowlisted_runtime_assets
tests/emtg_toolchain/unit/test_emtg_archive_unit.py::test_manifest_rejects_unsafe_or_duplicate_destinations
...
tests/emtg_toolchain/unit/test_runtime.py::test_runtime_requirements_parser_reads_generated_package_list
tests/emtg_toolchain/unit/test_runtime.py::test_runtime_requirements_parser_rejects_missing_package_list

17 tests collected in 0.02s
```


Run the focused archive-toolchain unit suite from the repository root:
```zsh
python -m pytest tests/emtg_toolchain/unit --unit -q
```

```zsh
% python -m pytest tests/emtg_toolchain/unit --unit -q
.................                                                                                                                                                                                   [100%]
17 passed in 0.08s
```


To run individual modules:

```zsh
python -m pytest tests/emtg_toolchain/unit/test_cli.py --unit -q

python -m pytest tests/emtg_toolchain/unit/test_emtg_archive_unit.py --unit -q

python -m pytest tests/emtg_toolchain/unit/test_runtime.py --unit -q
```

```zsh
% python -m pytest tests/emtg_toolchain/unit/test_cli.py --unit -q
python -m pytest tests/emtg_toolchain/unit/test_emtg_archive_unit.py --unit -q
python -m pytest tests/emtg_toolchain/unit/test_runtime.py --unit -q
....                                                                                                                                                                                                [100%]
4 passed in 0.04s
....                                                                                                                                                                                                [100%]
4 passed in 0.03s
.........                                                                                                                                                                                           [100%]
9 passed in 0.01s
```