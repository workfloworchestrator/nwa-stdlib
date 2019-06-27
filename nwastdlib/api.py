"""Module containing functions to share basic API logic."""

from flask import request

from . import Either


def request_json():
    """Get the json dict in the current connexion request, or an unsupported media type error (415)."""
    if request.is_json:
        return Either.Right(request.get_json())
    else:
        return Either.Left((None, 415))
