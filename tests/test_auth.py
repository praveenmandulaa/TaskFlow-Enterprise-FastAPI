
from uuid import uuid4


def test_health_check(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_login_and_profile(client):
    email = f"test-{uuid4().hex}@example.com"
    password = "TestPassword123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test Employee",
            "email": email,
            "password": password,
        },
    )

    assert register_response.status_code == 201

    user = register_response.json()

    assert user["email"] == email
    assert user["role"] == "employee"
    assert "hashed_password" not in user

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    tokens = login_response.json()

    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    profile_response = client.get(
        "/api/v1/users/me",
        headers={
            "Authorization": (
                f"Bearer {tokens['access_token']}"
            )
        },
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == email


def test_protected_endpoint_without_token(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401



def test_refresh_token_rotation(client):
    from uuid import uuid4

    email = f"refresh-{uuid4().hex}@example.com"
    password = "TestPassword123!"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Refresh Test User",
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200

    original_tokens = login_response.json()
    old_refresh_token = original_tokens["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert refresh_response.status_code == 200

    new_tokens = refresh_response.json()
    new_refresh_token = new_tokens["refresh_token"]

    assert new_tokens["access_token"]
    assert new_refresh_token != old_refresh_token

    # A rotated refresh token cannot be reused.
    reuse_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert reuse_response.status_code == 401
