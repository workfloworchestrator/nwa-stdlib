from functools import reduce
from .f import identity

from typing import Generic, List, TypeVar

α = TypeVar('a')
β = TypeVar('b')


class Either(Generic[α, β]):
    """The Either data type.

    ``Either α β`` represents a value two possibilities: ``Left α`` or ``Right β``
    """

    @classmethod
    def Left(cls, a: α):
        """Left data constructor"""
        return cls(a, None)

    @classmethod
    def Right(cls, b: β):
        """Right data constructor"""
        return cls(None, b)

    unit = Right

    def __init__(self, a: α, b: β):
        self.value = (a, b)

    def map(self, f):
        """Either α β -> (β -> γ) -> Either α γ

        >>> Either.Right(1).map(lambda x: x + 1)
        Right 2

        >>> Either.Left(1)
        Left 1
        """
        return self.flatmap(lambda b: Either.Right(f(b)))

    def flatmap(self, f):
        """Either α β -> (β -> Either γ) -> Either α γ

        >>> Either.Right(1).flatmap(lambda x: Either.Right(x + 1))
        Right 2

        >>> Either.Right(1).flatmap(lambda x: Either.Left(x + 1))
        Left 2

        >>> Either.Left(1).flatmap(lambda x: Either.Right(x + 1))
        Left 1
        """
        (a, b) = self.value
        if a is not None:
            return self
        else:
            return f(b)

    def either(self, f, g):
        """
        Either α β -> (α -> γ) -> (β -> γ) -> γ
        """
        (a, b) = self.value
        if a is not None:
            return f(a)
        else:
            return g(b)

    def bimap(self, f, g):
        """
        Map over both Left and Right at the same time

        >>> Either.Right(1).bimap(lambda _: 2, lambda _: 3)
        Right 3

        >>> Either.Left(1).bimap(lambda _: 2, lambda _: 3)
        Left 2
        """
        return self.either(
            lambda c: Either.Left(f(c)),
            lambda d: Either.Right(g(d))
        )

    def first(self, f):
        """
        Map over the first argument

        >>> Either.Left(1).first(lambda _: 2)
        Left 2

        >>> Either.Right(1).first(lambda _: 3)
        Right 1
        """
        return self.bimap(f, identity)

    second = map

    def __eq__(self, other):
        """Test two instances for value equality, such that:

        >>> Either.Right(1) == Either.Right(1)
        True

        >>> Either.Left(1) == Either.Left(1)
        True

        >>> Either.Left(1) == Either.Right(1)
        False

        >>> Either.Right(1) == 1
        False
        """
        if isinstance(other, Either):
            return self.value == other.value
        else:
            return False

    def __repr__(self):
        """Show

        >>> repr(Either.Left('error'))
        "Left 'error'"

        >>> repr(Either.Right(1))
        'Right 1'
        """
        (a, b) = self.value
        if a is not None:
            return "Left %s" % repr(a)
        else:
            return "Right %s" % repr(b)


def sequence(eithers: List[Either[α, β]]) -> Either[α, List[β]]:
    """Fold an iterable of Either to an Either of iterable.

    The iterable's class must have constructor that returns an empty instance
    given no arguments, and a non-empty instance given a singleton tuple.

    >>> sequence([Either.Right(1), Either.Right(2)])
    Right [1, 2]

    >>> sequence((Either.Right(2), Either.Right(3)))
    Right (2, 3)
    """
    unit = eithers.__class__
    empty = unit()

    def iter(acc, e):
        return acc.flatmap(lambda rs: e.map(lambda x: rs + unit((x,))))

    return reduce(iter, eithers, Either.Right(empty))
