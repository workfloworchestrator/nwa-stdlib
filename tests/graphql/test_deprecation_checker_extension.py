import strawberry

from nwastdlib.graphql.extensions.deprecation_checker_extension import make_deprecation_checker_extension


class CustomSchema(strawberry.federation.Schema):
    pass


async def test_deprecation_checker_extension_no_deprecations():
    # given

    def resolve_latest_query():
        return ["the", "quick", "brown", "fox"]

    @strawberry.type(description="No deprecated queries")
    class Query:
        latest_query: list[str] = strawberry.field(
            resolver=resolve_latest_query,
            description="Returns some info",
        )

    extensions = [make_deprecation_checker_extension(query=Query)]

    schema = CustomSchema(
        query=Query,
        extensions=extensions,
    )

    # when

    query = """
    query TestQuery {
        latestQuery
    }
    """

    await schema.execute(query=query)

    # then

    deprecation_extension = extensions[0]
    assert not deprecation_extension.deprecated_queries
    assert not deprecation_extension.deprecated_mutations


async def test_deprecation_checker_extension_with_deprecated_query():
    # given

    def resolve_deprecated_query():
        return ["the", "quick", "brown", "fox"]

    @strawberry.type(description="No deprecated queries")
    class Query:
        deprecated_query: list[str] = strawberry.field(
            resolver=resolve_deprecated_query,
            description="Returns some info",
            deprecation_reason="This query has been replaced!",
        )

    extensions = [make_deprecation_checker_extension(query=Query)]

    schema = CustomSchema(
        query=Query,
        extensions=extensions,
    )

    # when

    query = """
    query TestQuery {
        deprecatedQuery
    }
    """

    await schema.execute(query=query)

    # then

    deprecation_extension = extensions[0]
    assert deprecation_extension.deprecated_queries == {"deprecatedQuery": "This query has been replaced!"}
    assert not deprecation_extension.deprecated_mutations


async def test_deprecation_checker_extension_with_deprecated_fields():
    # given

    @strawberry.type
    class TypeWithDeprecatedFields:
        outdated: str = strawberry.field(deprecation_reason="Please use 'replacement'", default="outdated")
        replacement: str = strawberry.field(default="replacement")

    def resolve_deprecated_query() -> TypeWithDeprecatedFields:
        return TypeWithDeprecatedFields()

    @strawberry.type(description="No deprecated queries")
    class Query:
        latest_query: TypeWithDeprecatedFields = strawberry.field(
            resolver=resolve_deprecated_query, description="Returns some info"
        )

    extensions = [make_deprecation_checker_extension(query=Query)]

    schema = CustomSchema(
        query=Query,
        extensions=extensions,
    )

    # when

    query = """
    query TestQuery {
        latestQuery {
            outdated
        }
    }
    """

    await schema.execute(query=query)

    # then

    deprecation_extension = extensions[0]
    assert deprecation_extension.deprecated_queries == {"latestQuery/outdated": "Please use 'replacement'"}
    assert not deprecation_extension.deprecated_mutations
