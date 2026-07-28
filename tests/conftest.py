import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities as activities_store


@pytest.fixture(autouse=True)
def _reset_activities_state():
    """Reset the in-memory activities store between tests to avoid order dependence."""
    original = deepcopy(activities_store)
    yield
    activities_store.clear()
    activities_store.update(deepcopy(original))


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)
