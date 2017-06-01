from typing import Any, Callable, TypeVar

α = TypeVar('a')
β = TypeVar('b')
γ = TypeVar('c')


def identity(x: α) -> α:
    return x


def const(x: α) -> Callable[[Any], α]:
    '''
    Convert a value `x` to a function that always results in `x`

    >>> const(1)(2)
    1
    '''
    return lambda *_: x


def compose(f: Callable[[β], γ], g: Callable[[α], β]) -> Callable[[α], γ]:
    '''
    Get the composition f of g

    >>> compose(fst, list)({2,3,4})
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


def fst(xs):
    '''
    Get the first element from an indexed iterable data structure (e.g. tuple,
    list).

    Note: this depends on bounds checking of the data structure. Most iterable
    data structures in Python raise an IndexError when the index is out of
    bounds.

    >>> fst([1,2,3])
    1

    >>> fst(())
    Traceback (most recent call last):
        ...
    IndexError: tuple index out of range
    '''
    return xs[0]


def snd(xs):
    '''
    Get the second element from an indexed iterable data structure (e.g. tuple,
    list).

    Note: this depends on bounds checking of the iterable data structure. Most
    iterable data structures in Python raise an IndexError when the index is
    out of bounds.

    >>> snd([1,2,3])
    2
    '''
    return xs[1]


def elem(x, xs):
    '''
    Get whether `x` is in `xs`.

    >>> elem(1, range(1,100))
    True

    >>> elem(100, range(1,100))
    False
    '''
    try:
        return xs.index(x) >= 0
    except ValueError:
        return False
