# Network Automation Standard Library

[![pypi_version](https://img.shields.io/pypi/v/nwa-stdlib?color=%2334D058&label=pypi%20package)](https://pypi.org/project/nwa-stdlib)
[![Supported python versions](https://img.shields.io/pypi/pyversions/nwa-stdlib.svg?color=%2334D058)](https://pypi.org/project/nwa-stdlib)
[![codecov](https://codecov.io/github/workfloworchestrator/nwa-stdlib/graph/badge.svg?token=9XWVHKKF06)](https://codecov.io/github/workfloworchestrator/nwa-stdlib)

This library contains the functions and utilities that are shared by most Network Automation projects built at SURF.

## Installation

To install the package from PyPI:

```bash
pip install nwa-stdlib
```

## Development

### Virtual Environment

Steps to setup a virtual environment.

#### Step 1:

Create and activate a python3 virtualenv.

#### Step 2:

Install flit to enable you to develop on this repository:

```bash
pip install flit
```

#### Step 3:

To install all development dependencies:

```bash
flit install --deps develop
```

All steps combined into 1 command:

```bash
python -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install flit && flit install --deps develop
```

### Unit tests

Activate the virtualenv and run the unit tests with:

```bash
pytest
```

### Pre-commit

This project uses [pre-commit](https://pre-commit.com/) to automatically run a number of checks before making a git commit.
The same checks will be performed in the CI pipeline so this can save you some time.

First ensure you have pre-commit installed.
It is recommended to install it outside the virtualenv.
On Linux and Mac, pre-commit is available in most package managers. Alternatively you can install it globally with [pipx](https://github.com/pypa/pipx).

Once pre-commit is installed, go into the project root and enable it:
```bash
pre-commit install
```

This should output `pre-commit installed at .git/hooks/pre-commit`. The next time you run `git commit` the pre-commit hooks will validate your changes.

### Bump version

Depending on the feature type, run bumpversion (patch|minor|major) to increment the version you are working on. For
example to update the increment the patch version use
```bash
bumpversion patch
```

## Supported Python versions

nwa-stdlib must support the same python versions as [orchestrator-core](https://github.com/workfloworchestrator/orchestrator-core).

Exceptions to this rule are:
* **A new python version is released:** nwa-stdlib should support the new version before orchestrator-core does
* **Support for an old python version is dropped:** nwa-stdlib should drop the python version after orchestrator-core does
