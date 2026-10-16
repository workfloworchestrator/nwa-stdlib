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

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and create the development environment:

```bash
uv sync --locked --group test --group dev
```

Run project commands through that environment with `uv run`, for example:

```bash
uv run pytest
```

### Unit tests

Run the unit tests through the uv-managed environment:

```bash
uv run pytest
```

### Pre-commit

This project uses [prek](https://prek.j178.dev/), a fast drop-in replacement for [pre-commit](https://pre-commit.com/), to automatically run a number of checks before making a git commit.
The same checks will be performed in the CI pipeline so this can save you some time.

prek is part of the `dev` dependency group, so it is available after `uv sync`.
Go into the project root and enable it:
```bash
uv run prek install
```

This should output `prek installed at .git/hooks/pre-commit`. The next time you run `git commit` the hooks will validate your changes.
To run the hooks manually on all files, use `uv run prek run --all-files`.

### Set the package version

When a release version has been assigned, update the package metadata on a clean branch with `uv version`:

```bash
uv version 1.12.2
```

Specify the full version explicitly so release candidates can be represented, for example `uv version 1.12.2rc1`.

## Supported Python versions

nwa-stdlib must support the same python versions as [orchestrator-core](https://github.com/workfloworchestrator/orchestrator-core).

Exceptions to this rule are:
* **A new python version is released:** nwa-stdlib should support the new version before orchestrator-core does
* **Support for an old python version is dropped:** nwa-stdlib should drop the python version after orchestrator-core does
