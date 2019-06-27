"""Module that contains utility functions for Swagger."""

import tempfile
from pathlib import Path
from typing import Dict, Union

from ruamel.yaml import YAML

from . import Either


class SwaggerFile(object):
    def __init__(self, filename: Union[str, Path]) -> None:
        self.filename = Path(filename)
        self.substitutions: Dict = {}

    def set_host(self, host):
        self.substitutions["host"] = host
        return self

    def write(self, target=None):
        """Write the swagger file with its top-level substitutions to `target` (a tempfile by default).

        The substitutions can be performed only on top-level key,value combinations. Key,value combinations of nested
        dictionaries cannot be substituted.

        Note: `target` will be closed as a result of this call.
        """
        target = target or tmpfile()
        try:
            if self.filename.suffix != ".yaml":
                return Either.Left(f"Expected a YAML file. Got a {self.filename.suffix} file instead.")

            yaml = YAML(typ="safe")
            swagger_def = yaml.load(self.filename)
            swagger_def.update(self.substitutions)

            with target:
                yaml.dump(swagger_def, target)
            return Either.Right(target.name)

        except Exception as e:
            return Either.Left(e)


def tmpfile():
    return tempfile.NamedTemporaryFile(mode="w", prefix="swagger-", suffix=".yaml", delete=False)
