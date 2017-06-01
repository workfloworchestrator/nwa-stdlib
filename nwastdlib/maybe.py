from typing import Any, Callable, Generic, TypeVar
from .f import const, identity

α = TypeVar('a')
β = TypeVar('b')
Self = 'Maybe[α]'


class Maybe(Generic[α]):
    """
    The Maybe data type to represent an optional value.
    """

    def map(self: Self, f: Callable[[α], β]) -> 'Maybe[β]':
        """
        >>> inc = lambda n: n + 1

        >>> Maybe.Some(1).map(inc)
        Some 2

        >>> Maybe.Nothing().map(inc)
        Nothing
        """
        return self.flatmap(lambda a: Maybe.Some(f(a)))

    def flatmap(self: Self, f: Callable[[α], 'Maybe[β]']) -> 'Maybe[β]':
        """
        >>> Maybe.Some(1).flatmap(lambda _: Maybe.Some(2))
        Some 2

        >>> Maybe.Some(1).flatmap(lambda _: Maybe.Nothing())
        Nothing

        >>> Maybe.Nothing().flatmap(lambda _: Maybe.Some(1))
        Nothing
        """
        raise NotImplementedError("Abstract function `flatmap` must be implemented by the type constructor")

    def maybe(self: Self, b: β, f: Callable[[α], β]) -> β:
        """
        >>> Maybe.Some(1).maybe(0, identity)
        1

        >>> Maybe.Nothing().maybe(0, identity)
        0
        """
        raise NotImplementedError("Abstract function `maybe` must be implemented by the type constructor")

    def isNothing(self: Self) -> bool:
        """
        Return True iff self is Nothing.

        >>> Maybe.Some(1).isNothing()
        False

        >>> Maybe.Nothing().isNothing()
        True
        """
        return self.maybe(
            True,
            const(False)
        )

    def isSome(self: Self) -> bool:
        """
        Return True iff self is Some.

        >>> Maybe.Some(1).isSome()
        True

        >>> Maybe.Nothing().isSome()
        False
        """

        return self.maybe(
            False,
            const(True)
        )

    def __eq__(self: Self, other: Any) -> bool:
        """
        Test two instances for value equality.

        >>> Maybe.Some(1) == Maybe.Some(1)
        True

        >>> Maybe.Some(1) == Maybe.Some(2)
        False

        >>> Maybe.Some(1) == Maybe.Nothing()
        False

        >>> Maybe.Nothing() == Maybe.Nothing()
        True
        """
        if isinstance(other, Maybe):
            return self.maybe(
                other.isNothing(),
                lambda x: other.maybe(False, x.__eq__)
            )
        else:
            return False

    def __repr__(self: Self) -> str:
        """
        Show the instance.

        >>> repr(Maybe.Some('value'))
        "Some 'value'"

        >>> repr(Maybe.Nothing())
        'Nothing'
        """
        return self.maybe(
            "Nothing",
            lambda a: "Some %s" % repr(a)
        )


class __Nothing(Maybe):
    def __init__(self):
        """
        Nothing data constructor.

        >>> Maybe.Nothing()
        Nothing
        """
        pass

    def flatmap(self, f):
        return self

    def maybe(self, b, f):
        return b


class __Some(Maybe):
    def __init__(self, a: α):
        """
        Some data constructor

        >>> Maybe.Some('value')
        Some 'value'

        >>> Maybe.Some(None)
        Traceback (most recent call last):
            ...
        AssertionError: Some must contain a value
        """
        assert a, "Some must contain a value"
        self.value = a

    def flatmap(self, f):
        return f(self.value)

    def maybe(self, b, f):
        return f(self.value)


Maybe.Nothing = __Nothing
Maybe.Some = __Some
