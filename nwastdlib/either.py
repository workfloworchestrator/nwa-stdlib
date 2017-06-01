from functools import reduce
from .f import const, identity

from typing import Generic, List, TypeVar

α = TypeVar('a')
β = TypeVar('b')


class Either(Generic[α, β]):
    """The Either data type.

    ``Either α β`` represents a value two possibilities: ``Left α`` or ``Right β``
    """

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

        >>> Either.Right(1).flatmap(const('invalid type'))
        Traceback (most recent call last):
            ...
        TypeError: f must return an Either type
        """
        raise NotImplementedError("Abstract function `flatmap` must be implemented by the type constructor")

    def either(self, f, g):
        """
        Either α β -> (α -> γ) -> (β -> γ) -> γ

        >>> always = lambda x: lambda y: x
        >>> Either.Left(None).either(always('left'), always('right'))
        'left'

        >>> Either.Right(None).either(always('left'), always('right'))
        'right'
        """
        raise NotImplementedError("Abstract function `either` must be implemented by the type constructor")

    def bimap(self, f, g):
        """nn
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

        >>> Either.Right(1) == Either.Right(2)
        False

        >>> Either.Right(1) == 1
        False
        """
        if isinstance(other, Either):
            return self.either(
                lambda x: other.either(x.__eq__, const(False)),
                lambda x: other.either(const(False), x.__eq__)
            )
        else:
            return False

    def __repr__(self):
        """Show

        >>> repr(Either.Left('error'))
        "Left 'error'"

        >>> repr(Either.Right(1))
        'Right 1'
        """
        return self.either(
            lambda a: "Left %s" % repr(a),
            lambda b: "Right %s" % repr(b)
        )


class __Left(Either):
    def __init__(self, a: α):
        """
        Left data constructor

        >>> Either.Left(1)
        Left 1

        >>> Either.Left(None)
        Left None
        """
        self.value = a

    def flatmap(self, f):
        return self

    def either(self, f, g):
        return f(self.value)


class __Right(Either):
    def __init__(self, b: β):
        """
        Right data constructor

        >>> Either.Right(1)
        Right 1

        >>> Either.Right(None)
        Right None
        """
        self.value = b

    def flatmap(self, f):
        x = f(self.value)
        if not isinstance(x, Either):
            raise TypeError("f must return an Either type")
        return x

    def either(self, f, g):
        return g(self.value)


Either.Left = __Left
Either.Right = __Right
Either.unit = __Right


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
