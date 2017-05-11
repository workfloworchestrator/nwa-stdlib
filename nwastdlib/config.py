import os
from .either import Either, sequence
from .f import identity


def get_config(var, default=None, parse=identity):
    mx = os.environ.get(var)
    x = parse(mx) if mx is not None else default
    if x is None:
        return Either.Left("Missing config for %s" % var)
    return Either.Right(x)


class Config(object):
    def __init__(self, *values):
        self.values = values

    def unwrap(self):
        '''Extract the config values or fail with the first Left'''

        def invalid_config(err):
            raise InvalidConfigException(err)

        return sequence(self.values).either(
            invalid_config,
            identity
        )


class InvalidConfigException(Exception):
    pass
