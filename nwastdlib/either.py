from abc import abstractmethod, ABCMeta
from functools import reduce
from typing import Callable, Generic, Iterable, List, TypeVar, ClassVar, Type, Optional, Tuple

from .f import const, identity

α = TypeVar('α')
β = TypeVar('β')
γ = TypeVar('γ')
δ = TypeVar('δ')


class Either(Generic[α, β], metaclass=ABCMeta):
    """The Either data type.

    ``Either α β`` represents a value two possibilities: ``Left α`` or ``Right β``
    """

    Left: ClassVar[Type["Either"]]
    Right: ClassVar[Type["Either"]]
    unit: ClassVar[Type["Either"]]

    @abstractmethod
    def __init__(self, value: Optional[α] = None) -> None:
        raise NotImplementedError()

    @staticmethod
    def partition(xs: List['Either[α, β]']) -> Tuple[List[α], List[β]]:
        """
        >>> Either.partition([])
        ([], [])

        >>> Either.partition([Either.Left(1)])
        ([1], [])

        >>> Either.partition([Either.Right(1)])
        ([], [1])

        >>> Either.partition([Either.Left("foo"), Either.Right(7)])
        (['foo'], [7])
        """

        def fold(acc, e):
            return e.either(
                lambda x: (acc[0] + [x], acc[1]),
                lambda x: (acc[0], acc[1] + [x])
            )

        initializer: Tuple[List[α], List[β]] = ([], [])

        return reduce(fold, xs, initializer)

    def map(self, f: Callable[[β], γ]) -> 'Either[α, γ]':
        """
        >>> Either.Right(1).map(lambda x: x + 1)
        Right 2

        >>> Either.Left(1).map(lambda x: x + 1)
        Left 1
        """
        return self.flatmap(lambda b: Either.Right(f(b)))

    @abstractmethod
    def flatmap(self, f: Callable[[β], 'Either[α, γ]']) -> 'Either[α, γ]':
        """
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

    @abstractmethod
    def either(self, f: Callable[[α], γ], g: Callable[[β], γ]) -> γ:
        """
        >>> Either.Left(None).either(const('left'), const('right'))
        'left'

        >>> Either.Right(None).either(const('left'), const('right'))
        'right'
        """
        raise NotImplementedError("Abstract function `either` must be implemented by the type constructor")

    def bimap(self, f: Callable[[α], γ], g: Callable[[β], δ]) -> 'Either[γ, δ]':
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

    def first(self, f: Callable[[α], γ]) -> 'Either[γ, β]':
        """
        Map over the first argument.

        >>> Either.Left(1).first(lambda _: 2)
        Left 2

        >>> Either.Right(1).first(lambda _: 3)
        Right 1
        """
        return self.bimap(f, identity)

    second = map

    def isleft(self) -> bool:
        """
        Return True iff self is Left.

        >>> Either.Left(1).isleft()
        True

        >>> Either.Right(1).isleft()
        False
        """
        return self.either(const(True), const(False))

    def isright(self) -> bool:
        """
        Return True iff self is Right.

        >>> Either.Left(1).isright()
        False

        >>> Either.Right(1).isright()
        True
        """
        return self.either(const(False), const(True))

    def __eq__(self, other) -> bool:
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

    def __repr__(self) -> str:
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

    @staticmethod
    def sequence(eithers: Iterable["Either[α, β]"]) -> "Either[α, Iterable[β]]":
        """Fold an iterable of Either to an Either of iterable.

        The iterable's class must have constructor that returns an empty instance
        given no arguments, and a non-empty instance given a singleton tuple.

        >>> Either.sequence([Either.Right(1), Either.Right(2)])
        Right [1, 2]

        >>> Either.sequence((Either.Right(2), Either.Right(3)))
        Right (2, 3)

        >>> Either.sequence((Either.Right(3), Either.Left('x')))
        Left 'x'
        """
        unit = eithers.__class__
        empty = unit()  # type: ignore

        def iter(acc, e):
            return acc.flatmap(lambda rs: e.map(lambda x: rs + unit((x,))))

        return reduce(iter, eithers, Either.Right(empty))


class __Left(Either):
    def __init__(self, a: α) -> None:
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
    def __init__(self, b: β) -> None:
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
