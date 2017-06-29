'''
Module containing utility functions for lists.
'''
from typing import Callable, List, TypeVar

from .f import complement
from .maybe import Maybe

α = TypeVar('a')


def fst(xs: List[α]) -> α:
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


def snd(xs: List[α]) -> α:
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


def elem(x: α, xs: List[α]) -> bool:
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


def find(p: Callable[[α], bool], xs: List[α]) -> Maybe[α]:
    '''
    Find the first element in `xs` that matches the predicate `p`.

    >>> find(lambda x: x > 1, [1,2,3])
    Some 2

    >>> find(lambda x: x < 1, [1,2,3])
    Nothing
    '''
    g = (x for x in xs if p(x))
    try:
        return Maybe.Some(next(g))
    except StopIteration:
        return Maybe.Nothing()


def empty(xs: List[α]) -> bool:
    '''
    Test whether a list is empty.

    >>> empty([])
    True

    >>> empty([1])
    False
    '''
    return len(xs) == 0


def nonEmpty(xs: List[α]) -> bool:
    '''
    Complement of `empty`.

    >>> nonEmpty([])
    False

    >>> nonEmpty([1])
    True
    '''
    return complement(empty)(xs)
