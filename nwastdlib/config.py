import os
from .either import Either
from .f import identity


def get_config(var, default=None, parse=identity, secret=None):
    if secret is None:
        mx = os.environ.get(var)
        try:
            x = parse(mx) if mx is not None else default
            if x is None:
                return Either.Left("Missing config for %s" % var)
            return Either.Right(x)
        except ValueError:
            return Either.Left("Invalid value for %s: %s" % (var, mx))
    else:
        try:
            with open("/run/secrets/%s" % secret) as f:
                x = parse(f.read()) if len(f.read()) > 0 else default
                if x is None:
                    Either.Left("Missing config for %s" % var)
                return Either.Right(x)
        except ValueError:
            return Either.Left("Invalid value for %s: %s" % (var, x))
        except Exception as e:
            if default is not None:
                return Either.Right(default)
            return Either.Left("Unexpected Error while reading file %s: %s" % (f, e))


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
