"""Module containing utility functions for lists."""
from functools import reduce
from typing import Callable, List, Tuple, TypeVar

from .f import complement
from .maybe import Maybe

α = TypeVar("α")


def fst(xs: List[α]) -> α:
    """
    Get the first element from an indexed iterable data structure (e.g. tuple, list).

    Note: this depends on bounds checking of the data structure. Most iterable
    data structures in Python raise an IndexError when the index is out of
    bounds.

    >>> fst([1,2,3])
    1

    >>> fst(())
    Traceback (most recent call last):
        ...
    IndexError: tuple index out of range
    """
    return xs[0]


def elem(x: α, xs: List[α]) -> bool:
    """
    Get whether `x` is in `xs`.

    >>> elem(1, range(1,100))
    True

    >>> elem(100, range(1,100))
    False
    """
    try:
        return xs.index(x) >= 0
    except ValueError:
        return False


def mhead(xs: List[α]) -> Maybe[α]:
    """
    Maybe get the head of the list.

    >>> mhead([])
    Nothing

    >>> mhead([1])
    Some 1
    """
    return Maybe.Some(xs[0]) if len(xs) > 0 else Maybe.Nothing()


def find(p: Callable[[α], bool], xs: List[α]) -> Maybe[α]:
    """
    Find the first element in `xs` that matches the predicate `p`.

    >>> find(lambda x: x > 1, [1,2,3])
    Some 2

    >>> find(lambda x: x < 1, [1,2,3])
    Nothing
    """
    g = (x for x in xs if p(x))
    try:
        return Maybe.Some(next(g))
    except StopIteration:
        return Maybe.Nothing()


def empty(xs: List[α]) -> bool:
    """
    Test whether a list is empty.

    More specifically, it tests whether the `len' of a list equals 0 (zero).

    >>> empty([])
    True

    >>> empty([1])
    False
    """
    return len(xs) == 0


def nonempty(xs: List[α]) -> bool:
    """
    Complement of `empty`.

    >>> nonempty([])
    False

    >>> nonempty([1])
    True
    """
    return complement(empty)(xs)


def flatten(xs: List[List[α]]) -> List[α]:
    """
    Flatten a List of Lists.

    >>> flatten([[1],[2],[3],[4]])
    [1, 2, 3, 4]

    >>> flatten([])
    []

    >>> flatten([[]])
    []
    """
    return [item for sublist in xs for item in sublist]


def partition(p: Callable[[α], bool], xs: List[α]) -> Tuple[List[α], List[α]]:
    """
    Return a pair of lists of elements that /do/ match and element that /don't/ match the predicate.

    >>> partition(lambda x: x < 3, [1,2,3,4,5])
    ([1, 2], [3, 4, 5])
    """

    def it(acc, e):
        a, b = acc
        return ([*a, e], b) if p(e) else (a, [*b, e])

    initializer: Tuple[List[α], List[α]] = ([], [])

    return reduce(it, xs, initializer)
