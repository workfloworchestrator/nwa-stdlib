# Network Automation Standard Library

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
