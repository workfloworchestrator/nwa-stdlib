from typing import Any, Callable, TypeVar

α = TypeVar('α')
β = TypeVar('β')
γ = TypeVar('γ')


def identity(x: α) -> α:
    return x


def const(x: α) -> Callable[[Any], α]:
    '''
    Convert a value `x` to a function that always results in `x`

    >>> const(1)(2)
    1
    '''
    return lambda *_: x


def lazyconst(f: Callable[[], α]) -> Callable[[Any], α]:
    '''
    Convert a function `() -> α` to a function that always results in `α`.

    >>> lazyconst(lambda: 42)(1)
    42
    '''
    return lambda *_: f()


def compose(f: Callable[[β], γ], g: Callable[[α], β]) -> Callable[[α], γ]:
    '''
    Get the composition f of g

    >>> head = lambda xs: xs[0]
    >>> compose(head, list)({2,3,4})
    2
    '''
    return lambda x: f(g(x))


def curry(f: Callable[[α, β], γ]) -> Callable[[α], Callable[[β], γ]]:
    '''
    Convert a function `f` on two arguments into two functions.

    >>> def f(a, b):
    ...     return (a,b)

    >>> curry(f)('a')('b')
    ('a', 'b')
    '''
    return lambda a: lambda b: f(a, b)


def flip(f: Callable[[α, β], γ]) -> Callable[[β, α], γ]:
    '''
    Convert a function `f` on two arguments to takes its arguments in reverse order.

    >>> def f(a, b):
    ...     return (a,b)

    >>> flip(f)('a', 'b')
    ('b', 'a')
    '''
    return lambda b, a: f(a, b)


def unkwargs(f):
    '''
    Convert a function `f` on keyword arguments to a function on a single
    argument.

    >>> def f(a, b, c):
    ...     return (a,b,c)

    >>> arg = dict(a=1,b=2,c=3)

    >>> f(arg)
    Traceback (most recent call last):
        ...
    TypeError: f() missing 2 required positional arguments: 'b' and 'c'

    >>> unkwargs(f)(arg)
    (1, 2, 3)
    '''
    return lambda x: f(**x)


def complement(f: Callable[[α], bool]) -> Callable[[α], bool]:
    '''
    Get the complement of function f.

    >>> complement(const(True))()
    False

    >>> complement(const(False))()
    True
    '''
    return lambda *a: not f(*a)
