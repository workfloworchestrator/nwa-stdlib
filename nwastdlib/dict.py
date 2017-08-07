'''
Module containing utility functions for lists.
'''
from typing import Callable, Dict, Set, TypeVar
from .either import Either
from .maybe import Maybe

k = TypeVar('k')
α = TypeVar('α')


def filterWithKey(p: Callable[[k, α], bool], d: Dict[k, α]) -> Dict[k, α]:
    '''
    Filter the items of a dict with a predicate on key and value

    >>> d = dict(a=1, b=2)

    >>> filterWithKey(lambda k, v: k == 'a', d)
    {'a': 1}
    '''
    return {k: v for k, v in d.items() if p(k, v)}


def filterByKey(ks: Set[k], d: Dict[k, α]) -> Dict[k, α]:
    '''
    Filter all items of a dict where the key exists in a key space.

    >>> d = dict(a=1, b=2)

    >>> filterByKey({'a'}, d)
    {'a': 1}
    '''
    return filterWithKey(lambda k, v: k in ks, d)


def getByKeys(ks: Set[k], d: Dict[k, α]) -> Either[k, Dict[k, α]]:
    '''
    For all keys in a key space get their corresponding value from a dict.

    >>> d = dict(a=1, b=2)

    >>> getByKeys({'a'}, d)
    Right {'a': 1}

    >>> getByKeys({'a', 'c'}, d)
    Left 'c'
    '''
    def get(k):
        return lookup(k, d).maybe(
            Either.Left(k),
            lambda v: Either.Right((k, v))
        )

    return Either.sequence([get(k) for k in ks]).map(dict)


def lookup(k: k, d: Dict[k, α]) -> Maybe[α]:
    '''
    Lookup the value associated with a key in a dict.

    >>> d = dict(a=1, b=2)

    >>> lookup("a", d)
    Some 1

    >>> lookup("c", d)
    Nothing
    '''
    return Maybe.of(d.get(k, None))


def delete(key: k, d: Dict[k, α]) -> Dict[k, α]:
    '''
    Delete a key from a dict.

    >>> d = dict(a=1, b=2)

    >>> delete("a", d)
    {'b': 2}

    >>> delete("c", d)
    {'a': 1, 'b': 2}
    '''
    return {k: v for k, v in d.items() if k != key}
