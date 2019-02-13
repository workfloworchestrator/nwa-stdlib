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
from inspect import isgenerator
from typing import TypeVar, Callable, NoReturn, Any

from nwastdlib import Maybe, Either

T = TypeVar('T', Either, Maybe)


def do(M: T) -> Callable[[Callable], Callable]:
    def decorate(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            assert isgenerator(f), "Function must be a Generator"
            it = f(*args, **kwargs)

            def send(val: Any) -> Any:
                try:
                    return it.send(val).flatmap(send)
                except StopIteration as e:
                    return e.value
                except ReturnMonadic as e:
                    return M.unit(e.value)

            return send(None)

        return wrapper

    return decorate


def mreturn(value: Any) -> NoReturn:
    raise ReturnMonadic(value)


class ReturnMonadic(Exception):
    def __init__(self, value):
        self.value = value
