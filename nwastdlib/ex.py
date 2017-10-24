"""Module containing functions to deal with `Exception`s"""

import random
import string
import traceback


def format_ex(ex, stacklimit=None):
    '''
    Format an exception with a pseudo-random key and the shown exception.

    Returns a tuple of the exception string and key.
    '''
    key = "".join(random.choices(string.ascii_letters + string.digits, k=6))
    s = show_ex(ex, stacklimit)
    return (key, "[%s] %s" % (key, s))


def show_ex(ex, stacklimit=None):
    '''
    Show an exception, including its class name, message and (limited) stack
    trace.

    >>> try:
    ...     raise Exception("Something went wrong")
    ... except Exception as e:
    ...     print(show_ex(e))
    Exception: Something went wrong
    ...
    '''
    tbfmt = "".join(traceback.format_tb(ex.__traceback__, stacklimit))
    return "%s: %s\n%s" % (type(ex).__name__, ex, tbfmt)
