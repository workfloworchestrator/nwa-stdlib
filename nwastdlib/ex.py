"""Module containing functions to deal with `Exception`s."""

#  Copyright 2019 SURF.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import random
import string
import traceback


def format_ex(ex, stacklimit=None):
    """
    Format an exception with a pseudo-random key and the shown exception.

    Returns a tuple of the exception string and key.
    """
    key = "".join(random.choices(string.ascii_letters + string.digits, k=6))
    s = show_ex(ex, stacklimit)
    return key, "[{}] {}".format(key, s)


def show_ex(ex, stacklimit=None):
    """
    Show an exception, including its class name, message and (limited) stacktrace.

    >>> try:
    ...     raise Exception("Something went wrong")
    ... except Exception as e:
    ...     print(show_ex(e))
    Exception: Something went wrong
    ...
    """
    tbfmt = "".join(traceback.format_tb(ex.__traceback__, stacklimit))
    return "{}: {}\n{}".format(type(ex).__name__, ex, tbfmt)
