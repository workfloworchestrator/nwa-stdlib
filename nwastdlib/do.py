"""Provides do-notation for monadic structures like Either and Maybe.

>>> from nwastdlib import Maybe

>>> @do(Maybe)
... def mconcat(msg, name):
...     a = yield msg
...     b = yield name
...     return Maybe.Some(f"{a}, {b}!")

>>> mconcat(Maybe.Some("Hello"), Maybe.Some("World"))
Some 'Hello, World!'

>>> mconcat(Maybe.Nothing(), Maybe.Some("World"))
Nothing
"""
from functools import wraps
from typing import TypeVar, Callable, Any
from inspect import isgenerator

from nwastdlib import Maybe, Either

T = TypeVar('T', Either, Maybe)


def do(M: T) -> Callable[[Callable], Callable]:
    def decorate(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            it = f(*args, **kwargs)
            assert isgenerator(it), "Function is not a generator"

            def send(val: Any) -> Any:
                try:
                    return it.send(val).flatmap(send)
                except StopIteration as e:
                    return e.value

            return send(None)

        return wrapper

    return decorate