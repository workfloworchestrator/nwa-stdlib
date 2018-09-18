# Network Automation Standard Library

This library contains the functions and utilities that are shared by most
Network Automation projects.

## Getting started

If you want to use a virtual environment first create the environment:

```
python3 -m venv .venv
source .venv/bin/activate
```
And then run the following commands:

```
pip install flake8 --quiet
python setup.py check
python setup.py test
```

If you want to enhance of develop bug fixes for `nwastdlib` it's easiest to run the following commands:

```
pip install -e '.[test]'
```

This will install the `nwastdlib` in editable mode in the current virtual environment. A simple:

```
pytest
```

will then all run tests.


Projects that depend on nwa-stdlib import the project using the git commit. Update the necessary `requirement.txt` files
to get your changes in. To check the syntax before push:

```
flake8 nwastdlib
```

## OAuth2

The package oauth contains OAuth2 supporting functionality. For the usage see the integration tests or the 
core-db and core-admin projects:

* [Enable ResourceServer acces-token checks](https://gitlab.surfnet.nl/automation/coredb/blob/master/coredb/__main__.py)
* [Enable Client access-token retrieval](https://gitlab.surfnet.nl/automation/core-admin/blob/master/web/__init__.py)
* [Enable Server-to-Server access-token](https://gitlab.surfnet.nl/automation/nwa-stdlib/blob/master/nwastdlib/oauth/oauth_credentials.py)
* [Add access-token to API requests](https://gitlab.surfnet.nl/automation/core-admin/blob/master/web/utils.py)

The following applications are involved in authorization:

* [OAuth2 AuthorizationServer](https://auth.staging.automation.surf.net/info)
* [Authorization-Admin](https://auth-admin.staging.automation.surf.net)
* [OAuth Resource Servers](https://www.oauth.com/oauth2-servers/the-resource-server/)
* [OAuth Clients](https://www.oauth.com/oauth2-servers/oauth2-clients/)
