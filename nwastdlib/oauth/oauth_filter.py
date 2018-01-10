"""
OAuthFilter checks the bearer access_token in the Authorization header using the check_token endpoint exposed by
the AuthorizationServer. The check_token dictionary payload contains the granted scopes for the user and the allowed
resource servers (e.g. an array of string in the aud key). The aud key must contain the unique name of the resource
server protected by the OAuthFilter. The granted scopes must contain the scope configured - if any - for the intended
endpoint and - if configured in the swagger API yml file - either the read or write scope for respectively GET and
update methods - PUT, PATCH, POST and DELETE - http methods. See the integration tests in test_oauth_filter.py for
examples. The check_token payload is saved in the thread-local flask.g for subsequent use in the API endpoints.
"""
import flask
import requests
from werkzeug.exceptions import Unauthorized, Forbidden, RequestTimeout

from .scopes import Scopes
from ..ex import show_ex


class OAuthFilter(object):
    def __init__(self, security_definitions, token_check_url, resource_server_id, resource_server_secret,
                 white_listed_urls=[]):
        self.scope_config = Scopes(list(security_definitions.values()))
        self.token_check_url = token_check_url
        self.resource_server_id = resource_server_id
        self.white_listed_urls = white_listed_urls
        self.auth = (resource_server_id, resource_server_secret)

    def filter(self):
        current_request = flask.request
        endpoint = current_request.endpoint if current_request.endpoint else current_request.base_url

        is_white_listed = next(filter(lambda url: endpoint.endswith(url), self.white_listed_urls), None)
        if is_white_listed:
            return

        authorization = current_request.headers.get("Authorization")
        if not authorization:
            raise Unauthorized(description="No Authorization token provided")
        else:
            try:
                _, token = authorization.split()
            except ValueError:
                raise Unauthorized(description="Invalid authorization header: {}".format(authorization))

            try:
                with requests.Session() as s:
                    s.auth = self.auth
                    token_request = s.get(self.token_check_url, params={"token": token}, timeout=5)
            except requests.exceptions.Timeout as e:
                print(show_ex(e))
                raise RequestTimeout(description='RequestTimeout from authorization server')

            if not token_request.ok:
                raise Unauthorized(description="Provided oauth token {} is not valid".format(token))
            token_info = token_request.json()

            if "aud" not in token_info or self.resource_server_id not in token_info["aud"]:
                raise Forbidden(description="Provided token has access to {}, but not {}".format(
                    token_info.get("aud", []), self.resource_server_id))

            user_scopes = set(token_info.get("scope", []))

            self.scope_config.is_allowed(user_scopes, current_request.method, endpoint)

            flask.g.current_user = token_info

    @classmethod
    def current_user(cls):
        return flask.g.get("current_user", None) if flask.has_app_context() else None
