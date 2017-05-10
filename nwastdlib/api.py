"""
Module containing functions to share basic API logic.
"""

from . import Either

import connexion


def request_json():
    """
    Get the json dict in the current connexion request, or an unsupported media
    type error (415).
    """
    if connexion.request.is_json:
        return Either.Right(connexion.request.get_json())
    else:
        return Either.Left((None, 415))
