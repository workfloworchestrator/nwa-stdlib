def identity(x):
    return x


def compose(f, g):
    '''
    Get the composition f of g

    >>> compose(fst, list)({2,3,4})
    2
    '''
    return lambda x: f(g(x))


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
