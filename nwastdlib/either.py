from functools import reduce

from typing import Generic, List, TypeVar

α = TypeVar('a')
β = TypeVar('b')

class Either(Generic[α, β]):
    """The Either data type.

    ``Either α β`` represents a value two possibilities: ``Left α`` or ``Right β``"""

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
    """Fold a list of Either to an Either of that.

    >>> sequence([Either.Right(1), Either.Right(2)])
    Right [1, 2]
    """
    def iter(acc, e):
        return acc.flatmap(lambda rs: e.map(lambda x: rs + [x]))

    return reduce(iter, eithers, Either.Right([]))
