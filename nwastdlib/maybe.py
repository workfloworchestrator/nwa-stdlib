from typing import Any, Callable, Generic, Optional, TypeVar
from .f import const, identity

α = TypeVar('α')
β = TypeVar('β')


class Maybe(Generic[α]):
    """
    The Maybe data type to represent an optional value.
    """

    @staticmethod
    def of(optional: Optional[α]) -> 'Maybe[α]':
        """
        Maybe type constructor from Optional value.

        >>> Maybe.of(1)
        Some 1

        >>> Maybe.of(None)
        Nothing
        """
        if optional is None:
            return Maybe.Nothing()
        else:
            return Maybe.Some(optional)

    def __init__(self):
        """
        Enforce using specific data type constructors.

        >>> Maybe()
        Traceback (most recent call last):
            ...
        AssertionError: Maybe is an abstract type; use a specific type constructor

        >>> Maybe('value')
        Traceback (most recent call last):
            ...
        TypeError: __init__() takes 1 positional argument but 2 were given
        """
        raise AssertionError("Maybe is an abstract type; use a specific type constructor")

    def map(self, f: Callable[[α], β]) -> 'Maybe[β]':
        """
        >>> inc = lambda n: n + 1

        >>> Maybe.Some(1).map(inc)
        Some 2

        >>> Maybe.Nothing().map(inc)
        Nothing
        """
        return self.flatmap(lambda a: Maybe.Some(f(a)))

    def flatmap(self, f: Callable[[α], 'Maybe[β]']) -> 'Maybe[β]':
        """
        >>> Maybe.Some(1).flatmap(lambda _: Maybe.Some(2))
        Some 2

        >>> Maybe.Some(1).flatmap(lambda _: Maybe.Nothing())
        Nothing

        >>> Maybe.Nothing().flatmap(lambda _: Maybe.Some(1))
        Nothing

        >>> Maybe.Some(1).flatmap(const('invalid type'))
        Traceback (most recent call last):
            ...
        TypeError: f must return a Maybe type
        """
        raise NotImplementedError("Abstract function `flatmap` must be implemented by the type constructor")

    def maybe(self, b: β, f: Callable[[α], β]) -> β:
        """
        >>> Maybe.Some(1).maybe(0, identity)
        1

        >>> Maybe.Nothing().maybe(0, identity)
        0
        """
        raise NotImplementedError("Abstract function `maybe` must be implemented by the type constructor")

    def isNothing(self) -> bool:
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

    def isSome(self) -> bool:
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

    def __eq__(self, other: Any) -> bool:
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

    def __repr__(self) -> str:
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

        >>> Maybe.Some(False)
        Some False

        >>> Maybe.Some(None)
        Traceback (most recent call last):
            ...
        AssertionError: Some must contain a value
        """
        assert a is not None, "Some must contain a value"
        self.value = a

    def flatmap(self, f):
        x = f(self.value)
        if not isinstance(x, Maybe):
            raise TypeError("f must return a Maybe type")
        return x

    def maybe(self, b, f):
        return f(self.value)


Maybe.Nothing = const(__Nothing())
Maybe.Some = __Some
