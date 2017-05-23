"""
Module that contains utility functions for Swagger.
"""

import re
import tempfile
from functools import reduce

from . import Either


class SwaggerFile(object):
    def __init__(self, filename):
        self.filename = filename
        self.substititions = dict()

    def set_host(self, host):
        self.substititions['host'] = host
        return self

    def write(self, target=None):
        """
        Write the swagger file with its substitutions to `target` (a tempfile by default).

        Note: `target` will be closed as a result of this call.
        """
        target = target or tmpfile()
        try:
            with open(self.filename, 'r') as f:
                source = f.read()

            def sub(s, kv):
                re.compile('%s: "[^"]*"' % kv[0]).sub('%s: "%s"' % kv, s)
            output = reduce(sub, self.substititions.items(), source)

            with target:
                target.write(output)
                return Either.Right(target.name)

        except Exception as e:
            return Either.Left(e)


def tmpfile():
    return tempfile.NamedTemporaryFile(mode='w', prefix='swagger-', suffix='.yaml', delete=False)
