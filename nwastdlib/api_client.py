"""
Module containing functions to share basic API client logic.
"""

import sys

from collections import namedtuple
from urllib3.exceptions import MaxRetryError

from .either import Either
from .ex import format_ex
from .list import elem


class ApiClientProxy():
    '''
    Proxy over a swagger API client instance that allows passing request
    headers.

    Where the API client is reused, this proxy is intended to be used on a
    per-request basis.
    '''

    def __init__(self, target, request_headers):
        self.target = target
        self.request_headers = request_headers

    def call_api(self, resource_path, method, path_params=None, query_params=None, header_params=None, body=None,
                 post_params=None, files=None, response_type=None, auth_settings=None, async_req=None,
                 _return_http_data_only=None, collection_formats=None, _preload_content=True, _request_timeout=None):
        all_headers = {**self.request_headers, **header_params}
        return self.target.call_api(resource_path, method, path_params, query_params, all_headers, body, post_params,
                                    files, response_type, auth_settings, async_req, _return_http_data_only,
                                    collection_formats, _preload_content, _request_timeout)

    def __getattr__(self, name):
        return getattr(self.target, name)

    def __repr__(self):
        return "[ApiClientProxy] %s" % repr(self.target)


Error = namedtuple("Error", ["status", "key", "message"])


def run_api_call(name, get_client):
    '''
    Generic function to call an API as a client. The result is mapped to an Either.

    Given the generic nature, errors are presented with the `Error` struct.
    '''
    def log_error(ex):
        (key, err) = format_ex(ex)
        print(err, file=sys.stderr)
        return key

    def handle_api_ex(key, e):
        if e.status == 404:
            return Either.Left(Error(404, key, "Not found"))
        if elem(e.status, range(400, 500)):
            return Either.Left(Error(e.status, key, f"Error communicating to {name}. Response status code was {e.status} with payload: {e.body}"))
        if elem(e.status, range(500, 600)):
            return Either.Left(Error(e.status, key, f"Received server error {e.status} from {name} with payload: {e.body}"))
        return Either.Left(Error(e.status, key, "Error while accessing %s" % name))

    def iter(f):
        try:
            client = get_client()
            return Either.Right(f(client))
        except MaxRetryError as e:
            key = log_error(e)
            return Either.Left(Error(503, key, "Failed to establish a connection to %s" % (name)))
        except Exception as e:
            key = log_error(e)
            # Each swagger-generated client uses its own 'ApiException' class.
            # They all quack likewise so use a class name test only.
            if e.__class__.__name__ == "ApiException":
                return handle_api_ex(key, e)
            else:
                return Either.Left(
                    Error(500, key, "%s: %s\nThis is most likely a programming error" % (e.__class__.__name__, e)))

    return iter
