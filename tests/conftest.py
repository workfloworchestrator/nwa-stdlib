import pytest


@pytest.fixture
def fastapi_test_client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    yield TestClient(FastAPI())
