import pytest
from main import app
from api.auth import get_current_active_user
from models.auth_schemas import User

@pytest.fixture(autouse=True)
def override_auth():
    dummy_user = User(
        username="test_user",
        role="Admin",
        is_active=True
    )
    app.dependency_overrides[get_current_active_user] = lambda: dummy_user
    yield
    app.dependency_overrides.clear()
