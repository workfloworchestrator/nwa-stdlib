import strawberry
from strawberry.types import Info

from nwastdlib.graphql.extensions.error_handler_extension import ErrorHandlerExtension, register_error


class CustomSchema(strawberry.federation.Schema):
    pass


async def test_error_handler_extension_with_error():
    # given

    def resolve_some_query(info: Info):
        register_error("Some disaster happened!", info)
        return ["the", "quick", "brown", "fox"]

    @strawberry.type(description="No deprecated queries")
    class Query:
        some_query: list[str] = strawberry.field(
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

    assert error.message == "Some disaster happened!"
