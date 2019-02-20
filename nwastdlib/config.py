import os
import os.path

from .either import Either
from .f import identity


def get_config(var, default=None, parse=identity, secret=None, secret_base_location="/run/secrets"):
    def from_environ():
        mx = os.environ.get(var)
        try:
            x = parse(mx) if mx is not None else default
            if x is None:
                return Either.Left(f"Missing config for {var}")
            return Either.Right(x)
        except ValueError:
            return Either.Left(f"Invalid value for {var}: {mx}")

    def from_file(filename):
        if not os.path.isfile(filename):
            return Either.Left(f"File {filename} does not exist. Can not resolve var {var}")
        try:
            with open(filename) as f:
                content = f.read()
                if len(content) == 0:
                    return Either.Left(f"Missing config for {var} in {filename}")
                x = parse(content.replace("\n", ""))
                return Either.Right(x)
        except ValueError:
            return Either.Left(f"Invalid value for {var}: {x}")
        except Exception as e:
            if default is not None:
                return Either.Right(default)
            return Either.Left(f"Unexpected Error while reading file {filename}: {e}")

    filename = (f"{secret_base_location}/{secret}")
    if not secret or not os.path.isfile(filename):
        return from_environ()
    return from_file(filename)


class Config(object):
    def __init__(self, *values):
        self.values = values

    def unwrap(self):
        '''Extract the config values or fail with the first Left'''

        def invalid_config(err):
            raise InvalidConfigException(err)

        return Either.sequence(self.values).either(
            invalid_config,
            identity
        )


class InvalidConfigException(Exception):
    pass
