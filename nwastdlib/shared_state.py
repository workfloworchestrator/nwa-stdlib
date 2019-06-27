from typing import ClassVar, Dict, Type


class SharedState(type):
    """
    Type to imperatively share object state between modules.

    Use `SharedState` as the metaclass of your own imperative state class. Note
    that constructor of a state object is invoked only once.

    >>> class MyState(metaclass=SharedState):
    ...     pass

    Every "instance" then yields exactly the same object.

    >>> id(MyState()) == id(MyState())
    True

    >>> class MyNewState(MyState):
    ...     pass

    Derived state objects are unique too.

    >>> id(MyNewState()) == id(MyNewState())
    True

    However, derived state object are /different/ from their parent.

    >>> id(MyState()) == id(MyNewState())
    False
    """

    __instances: ClassVar[Dict[Type, object]] = {}

    def __call__(cls, *args, **kwargs):
        instance = cls.__instances.get(cls)
        if instance is None:
            instance = cls.__instances[cls] = super(SharedState, cls).__call__(*args, **kwargs)
        return instance
