import requests
from flask import current_app
from werkzeug.exceptions import Unauthorized

from nwastdlib.api_client import ApiClientProxy

AUTH_RESOURCE_SERVER = 'auth_resource_server'
SCOPES = ["read", "write", "admin"]

req_session = requests.Session()


def obtain_client_credentials_token(app, oauth2_token_url, oauth2_client_id, oauth2_secret):
    app.config[AUTH_RESOURCE_SERVER] = dict(
        oauth2_token_url=oauth2_token_url,
        oauth2_client_id=oauth2_client_id,
        oauth2_secret=oauth2_secret
    )
    response = req_session.post(url=oauth2_token_url,
                                data={'grant_type': 'client_credentials'},
                                auth=(oauth2_client_id, oauth2_secret),
                                timeout=5)
    if not response.ok:
        raise Unauthorized(description=f"Response for obtaining access_token {response.json()}")

    json = response.json()
    # Spec dictates that client credentials should not be allowed to get a refresh token
    app.config[AUTH_RESOURCE_SERVER]['access_token'] = json['access_token']


def add_client_credentials_token_header(client):
    config = current_app.config[AUTH_RESOURCE_SERVER]
    if 'access_token' in config:
        access_token = config['access_token']
        return ApiClientProxy(client, {'Authorization': f"bearer {access_token}"})
    return client


def refresh_client_credentials_token():
    config = current_app.config[AUTH_RESOURCE_SERVER]
    return obtain_client_credentials_token(current_app,
                                           config['oauth2_token_url'],
                                           config['oauth2_client_id'],
                                           config['oauth2_secret'])
