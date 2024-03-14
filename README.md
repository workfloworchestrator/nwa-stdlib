# Network Automation Standard Library

[![pypi_version](https://img.shields.io/pypi/v/nwa-stdlib?color=%2334D058&label=pypi%20package)](https://pypi.org/project/nwa-stdlib)
[![Supported python versions](https://img.shields.io/pypi/pyversions/nwa-stdlib.svg?color=%2334D058)](https://pypi.org/project/nwa-stdlib)
[![codecov](https://codecov.io/github/workfloworchestrator/nwa-stdlib/graph/badge.svg?token=9XWVHKKF06)](https://codecov.io/github/workfloworchestrator/nwa-stdlib)

This library contains the functions and utilities that are shared by most
Network Automation projects built at SURF.

## Getting started

If you want to use a virtual environment first create the environment:

```bash
pip install flit
```
And then run the following commands:

If you want to enhance or develop bug fixes for `nwastdlib` it's easiest to run the following commands:
```bash
flit install --deps develop --symlink
```

## Development
Depending on the feature type, run bumpversion (patch|minor|major) to increment the version you are working on. For
example to update the increment the patch version use
```bash
bumpversion patch
```

## To run tests
```
pytest
```

## Supported Python versions

nwa-stdlib must support the same python versions as [orchestrator-core](https://github.com/workfloworchestrator/orchestrator-core).

Exceptions to this rule are:
* **A new python version is released:** nwa-stdlib should support the new version before orchestrator-core does
* **Support for an old python version is dropped:** nwa-stdlib should drop the python version after orchestrator-core does
