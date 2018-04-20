"""Provides do-notation for monadic structures like Either and Maybe.

>>> from nwastdlib import Maybe

>>> @do(Maybe)
... def mconcat(msg, name):
...     a = yield msg
...     b = yield name
...     mreturn(f"{a}, {b}!")

>>> mconcat(Maybe.Some("Hello"), Maybe.Some("World"))
Some 'Hello, World!'

>>> mconcat(Maybe.Nothing(), Maybe.Some("World"))
Nothing
"""
from functools import wraps


def do(M):
    def decorate(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            it = f(*args, **kwargs)

            def send(val):
                try:
                    return it.send(val).flatmap(send)
                except StopIteration as e:
                    return e.value
                except ReturnMonadic as e:
                    return M.unit(e.value)

            return send(None)

        return wrapper

    return decorate


def mreturn(value):
    raise ReturnMonadic(value)


class ReturnMonadic(Exception):
    def __init__(self, value):
        self.value = value
