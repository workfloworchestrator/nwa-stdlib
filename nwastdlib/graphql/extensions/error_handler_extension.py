# Copyright 2019-2026 SURF.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from collections.abc import Callable, Collection, Generator, Iterable
from contextvars import ContextVar
from enum import StrEnum, auto
from http import HTTPStatus
from typing import Any

import structlog
from graphql import GraphQLError
from strawberry.extensions import SchemaExtension
from strawberry.types import ExecutionContext, Info

from nwastdlib.settings import nwa_settings

logger = structlog.stdlib.get_logger(__name__)

EXTENSION_ERROR_TYPE = "error_type"
EXTENSION_HTTP_STATUS_CODE = "http_status_code"

_error_bucket: ContextVar[None | list[GraphQLError]] = ContextVar("error_bucket", default=None)


class ErrorType(StrEnum):
    """These error types are returned in 'error_type' extension field on an error response.

    https://productionreadygraphql.com/2020-08-01-guide-to-graphql-errors
    https://engineering.zalando.com/posts/2021/04/modeling-errors-in-graphql.html

    We currently distinguish the following categories that are meaningful to the frontend/user:
     - NOT_AUTHENTICATED: unauthenticated user or expired token, user should authenticate
     - NOT_AUTHORIZED: user not allowed to perform operation on this resource
     - NOT_FOUND: a resource wasn't found, data inconsistency or wrong identifier
     - INTERNAL_ERROR: all other errors on the graphql server and/or backend systems. User may retry later
     - BAD_REQUEST: one or more query input parameters are not valid (i.e. dynamic sort/filter params)
    """

    NOT_AUTHENTICATED = auto()
    NOT_AUTHORIZED = auto()
    NOT_FOUND = auto()
    INTERNAL_ERROR = auto()
    BAD_REQUEST = auto()


def _http_attr(exception: Exception | None, part: str, field: str) -> Any:
    """Read `exception.<part>.<field>`, tolerating clients that raise on access.

    httpx's `.request` is a property that raises RuntimeError when unset, so plain getattr is unsafe.
    """
    try:
        return getattr(getattr(exception, part, None), field, None)
    except RuntimeError:
        return None


def _http_status_code(exception: Exception | None) -> int | None:
    """Status code from clients exposing `.response.status_code` (httpx, httpx2, requests)."""
    return _http_attr(exception, "response", "status_code")


def default_to_error_type(exception: Exception | None) -> ErrorType:
    if isinstance(exception, PermissionError):
        return ErrorType.NOT_AUTHORIZED

    match _http_status_code(exception):
        case HTTPStatus.UNAUTHORIZED:
            return ErrorType.NOT_AUTHENTICATED
        case HTTPStatus.FORBIDDEN:
            return ErrorType.NOT_AUTHORIZED
        case HTTPStatus.NOT_FOUND:
            return ErrorType.NOT_FOUND
        case _:
            return ErrorType.INTERNAL_ERROR


def _get_all_errors(execution_context: ExecutionContext) -> Iterable[GraphQLError]:
    # Errors from strawberry or exceptions raised by our code
    if execution_context.result and execution_context.result.errors:
        yield from execution_context.result.errors

    # Errors registered by our code
    if registered_errors := _error_bucket.get():
        yield from registered_errors


def _has_extension(error: GraphQLError, key: str) -> bool:
    return key in (error.extensions or {})


def _add_extension(error: GraphQLError, key: str, value: Any) -> None:
    if error.extensions is None:
        error.extensions = {}
    error.extensions[key] = value


def _get_extension(error: GraphQLError, key: str) -> Any | None:
    if error.extensions:
        return error.extensions.get(key, None)
    return None


def _process(error: GraphQLError, to_error_type: Callable[[Exception | None], ErrorType]) -> GraphQLError:
    exc = error.original_error
    if (status_code := _http_status_code(exc)) is not None and (url := _http_attr(exc, "request", "url")) is not None:
        _add_extension(error, EXTENSION_HTTP_STATUS_CODE, {f"{url}": status_code})
    if not _has_extension(error, EXTENSION_ERROR_TYPE):
        _add_extension(error, EXTENSION_ERROR_TYPE, str(to_error_type(exc)))

    error_type = _get_extension(error, EXTENSION_ERROR_TYPE)
    if error_type == ErrorType.INTERNAL_ERROR and not nwa_settings.DEBUG:
        logger.exception("Graphql Internal Server Error", error=error, exc_info=exc)
        error.message = "Internal Server Error"

    return error


class ErrorHandlerExtension(SchemaExtension):
    """Collect all raised and/or registered errors and enriches them with metadata.

    Disambiguation:
    - This class is a Strawberry extension that is executed on each graphql query, like a middleware.
    - The metadata added to each error is also called an 'extension' because it is a reserved field in the GraphQL spec.
    More details: https://spec.graphql.org/October2021/#sec-Errors.Error-result-format
    """

    to_error_type = staticmethod(default_to_error_type)

    def __init__(self, to_error_type: Callable[[Exception | None], ErrorType] | None = None, **kwargs) -> None:  # type: ignore
        if to_error_type:
            self.to_error_type = staticmethod(to_error_type)  # type: ignore
        super().__init__(**kwargs)

    def on_execute(self) -> Generator[None, None, None]:
        _error_bucket.set([])

        yield

        if not self.execution_context or self.execution_context.result is None:
            return

        self.execution_context.result.errors = [
            _process(error, self.to_error_type) for error in _get_all_errors(self.execution_context)
        ]


def _register(message: str, path: Collection[str | int], error_type: ErrorType) -> None:
    error = GraphQLError(message=message, path=path, extensions={EXTENSION_ERROR_TYPE: str(error_type)})
    if (errors := _error_bucket.get()) is None:
        logger.debug("ErrorHandlerExtension disabled, dropping error", error=error)
        return

    logger.debug("Registering error", error=error)
    errors.append(error)
    _error_bucket.set(errors)


def register_error(message: str, info: Info, error_type: ErrorType = ErrorType.INTERNAL_ERROR) -> None:
    """Register an error message.

    Use this to collect error messages from multiple resolvers and return them in the response.
    """
    _register(message, info.path.as_list(), error_type)


def register_exception(
    exception: Exception, info: Info, to_error_type: Callable[[Exception | None], ErrorType] = default_to_error_type
) -> None:
    """Register an exception encountered during the query execution.

    Use this to collect exceptions from multiple resolvers and return them in the response.
    """
    _register(str(exception), info.path.as_list(), to_error_type(exception))
