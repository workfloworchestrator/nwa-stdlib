from http import HTTPStatus
from types import SimpleNamespace

import pytest
import strawberry
from httpx import ConnectError, HTTPStatusError, Request, Response
from strawberry.types import Info

from nwastdlib.graphql.extensions.error_handler_extension import ErrorHandlerExtension, ErrorType


class CustomSchema(strawberry.federation.Schema):
    pass


async def test_error_handler_extension_no_errors():
    # given

    def resolve_some_query(info: Info):
        return ["the", "quick", "brown", "fox"]

    @strawberry.type(description="No deprecated queries")
    class Query:
        some_query: list[str] | None = strawberry.field(
            resolver=resolve_some_query,
            description="Returns some info",
        )

    extensions = [ErrorHandlerExtension]

    schema = CustomSchema(
        query=Query,
        extensions=extensions,
    )

    # when

    query = """
    query TestQuery {
        someQuery
    }
    """

    result = await schema.execute(query=query)

    # then

    assert result.errors == []
    assert result.data == {"someQuery": ["the", "quick", "brown", "fox"]}


@pytest.mark.parametrize(
    "exception_class, message, error_type",
    [
        (ValueError, "Internal Server Error", ErrorType.INTERNAL_ERROR),
        (PermissionError, "There was a permission error", ErrorType.NOT_AUTHORIZED),
    ],
)
async def test_error_handler_extension_with_error(exception_class, message, error_type):
    # given

    def resolve_some_query(info: Info):
        if exception_class:
            raise exception_class(message)
        return

    @strawberry.type(description="No deprecated queries")
    class Query:
        some_query: list[str] | None = strawberry.field(
            resolver=resolve_some_query,
            description="Returns some info",
        )

    extensions = [ErrorHandlerExtension]

    schema = CustomSchema(
        query=Query,
        extensions=extensions,
    )

    # when

    query = """
    query TestQuery {
        someQuery
    }
    """

    result = await schema.execute(query=query)

    # then

    assert result.errors
    error = result.errors[0]

    assert error.message == message
    assert error.path == ["someQuery"]
    assert error.extensions == {"error_type": error_type}

    assert result.data == {"someQuery": None}


def httpx_error(message: str, status_code: HTTPStatus) -> Exception:
    return HTTPStatusError(
        message=message,
        request=Request(method="GET", url="surf.nl"),
        response=Response(status_code=status_code),
    )


def foreign_client_error(message: str, status_code: HTTPStatus) -> Exception:
    """Any other client — httpx2, requests, whatever a resolver reaches for."""
    error = Exception(message)
    error.request = SimpleNamespace(url="surf.nl")
    error.response = SimpleNamespace(status_code=status_code)
    return error


@pytest.mark.parametrize("make_error", [httpx_error, foreign_client_error], ids=["httpx", "foreign-client"])
@pytest.mark.parametrize(
    "status_code, message, error_type",
    [
        (HTTPStatus.NOT_FOUND, "Resource does not exists", ErrorType.NOT_FOUND),
        (HTTPStatus.FORBIDDEN, "Not authorized", ErrorType.NOT_AUTHORIZED),
        (HTTPStatus.UNAUTHORIZED, "Not authenticated", ErrorType.NOT_AUTHENTICATED),
    ],
)
async def test_error_handler_extension_with_http_error(make_error, status_code, message, error_type):
    # given

    def resolve_some_query(info: Info):
        raise make_error(message, status_code)

    @strawberry.type(description="No deprecated queries")
    class Query:
        some_query: list[str] | None = strawberry.field(
            resolver=resolve_some_query,
            description="Returns some info",
        )

    extensions = [ErrorHandlerExtension]

    schema = CustomSchema(
        query=Query,
        extensions=extensions,
    )

    # when

    query = """
    query TestQuery {
        someQuery
    }
    """

    result = await schema.execute(query=query)

    # then

    assert result.errors
    error = result.errors[0]

    assert error.message == message
    assert error.path == ["someQuery"]
    assert error.extensions == {"error_type": error_type, "http_status_code": {"surf.nl": status_code}}

    assert result.data == {"someQuery": None}


async def test_error_handler_extension_with_transport_error():
    """A connection failure must not crash the handler.

    httpx's `.request` is a property that raises RuntimeError until it is set, so probing it on a
    bare transport error has to tolerate that.
    """

    # given

    def resolve_some_query(info: Info):
        raise ConnectError("backend unreachable")

    @strawberry.type(description="No deprecated queries")
    class Query:
        some_query: list[str] | None = strawberry.field(
            resolver=resolve_some_query,
            description="Returns some info",
        )

    schema = CustomSchema(query=Query, extensions=[ErrorHandlerExtension])

    # when

    result = await schema.execute(
        query="""
    query TestQuery {
        someQuery
    }
    """
    )

    # then

    assert result.errors
    error = result.errors[0]

    assert error.message == "Internal Server Error"
    assert error.extensions == {"error_type": ErrorType.INTERNAL_ERROR}


async def test_error_handler_extension_when_request_is_unreadable():
    """A client whose `.request` raises is still classified, minus the status code extension.

    httpx's `.request` is a property that raises RuntimeError until set, so probing it must tolerate
    more than AttributeError.
    """

    # given

    class UnreadableRequestError(Exception):
        response = SimpleNamespace(status_code=HTTPStatus.NOT_FOUND)

        @property
        def request(self):
            raise RuntimeError("The .request property has not been set.")

    def resolve_some_query(info: Info):
        raise UnreadableRequestError("Resource does not exists")

    @strawberry.type(description="No deprecated queries")
    class Query:
        some_query: list[str] | None = strawberry.field(
            resolver=resolve_some_query,
            description="Returns some info",
        )

    schema = CustomSchema(query=Query, extensions=[ErrorHandlerExtension])

    # when

    result = await schema.execute(
        query="""
    query TestQuery {
        someQuery
    }
    """
    )

    # then

    assert result.errors
    error = result.errors[0]

    assert error.extensions == {"error_type": ErrorType.NOT_FOUND}
