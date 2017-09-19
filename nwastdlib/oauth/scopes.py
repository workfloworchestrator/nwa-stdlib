from functools import reduce

from werkzeug.exceptions import Forbidden

HTTP_READ_METHODS = {'get', 'head', 'options'}


class Scopes(object):
    def __init__(self, security_definitions):
        all_scopes = map(lambda sec_def: list(sec_def.get('scopes', [])), security_definitions)
        unique_scopes = {scopes for sub_scopes in all_scopes for scopes in sub_scopes}

        self.requires_read = 'read' in unique_scopes
        self.requires_write = 'write' in unique_scopes

        scopes_and_operations_list = list(
            map(lambda definition: definition.get('x-scopes-operation-ids', []), security_definitions))

        def map_all_endpoints(accumulator, scope_and_operation):
            scope = next(iter(scope_and_operation.keys()))
            endpoints = next(iter(scope_and_operation.values()))
            for endpoint in endpoints:
                accumulator[endpoint] = scope
            return accumulator

        self.operation_and_scope = reduce(map_all_endpoints, scopes_and_operations_list, {})

    def is_allowed(self, user_scopes, request_method, request_endpoint):
        required_scopes = set()
        method = request_method.lower()
        read_access_request = method in HTTP_READ_METHODS
        not_allowed = False

        if read_access_request and self.requires_read and 'read' not in user_scopes:
            not_allowed = True
            required_scopes.add('read')

        if not read_access_request and self.requires_write and 'write' not in user_scopes:
            not_allowed = True
            required_scopes.add('write')

        if not not_allowed:
            operation_scope = next(
                filter(lambda item: request_endpoint.endswith(item[0]), self.operation_and_scope.items()), None)
            if operation_scope and operation_scope[1] not in user_scopes:
                not_allowed = True
                required_scopes.add(operation_scope[1])

        if not_allowed:
            raise Forbidden(
                description="Provided token does not have the required scope(s): {}".format(
                    required_scopes - user_scopes))
