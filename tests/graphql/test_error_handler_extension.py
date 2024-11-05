from http import HTTPStatus

import pytest
import strawberry
from httpx import HTTPStatusError, Request, Response
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


@pytest.mark.parametrize(
    "status_code, message, error_type",
    [
        (HTTPStatus.NOT_FOUND, "Resource does not exists", ErrorType.NOT_FOUND),
        (HTTPStatus.FORBIDDEN, "Not authorized", ErrorType.NOT_AUTHORIZED),
    ],
)
async def test_error_handler_extension_with_http_error(status_code, message, error_type):
    # given

    def resolve_some_query(info: Info):
        if status_code:
            raise HTTPStatusError(
                message=message,
                request=Request(method="GET", url="surf.nl"),
                response=Response(status_code=status_code),
            )
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
    assert error.extensions == {"error_type": error_type, "http_status_code": {"surf.nl": status_code}}

    assert result.data == {"someQuery": None}
