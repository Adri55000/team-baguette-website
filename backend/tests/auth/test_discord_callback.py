from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def start_oauth(client):
    response = client.get(
        "/api/auth/discord/login",
        follow_redirects=False,
    )

    assert response.status_code == 302

    state = client.cookies.get("discord_oauth_state")
    assert state is not None

    return state


def test_invalid_state_is_rejected(client):
    start_oauth(client)

    response = client.get(
        "/api/auth/discord/callback",
        params={
            "code": "test_code",
            "state": "incorrect",
        },
    )

    assert response.status_code == 400
    assert client.cookies.get("discord_oauth_state") is None


def test_missing_code_is_rejected(client):
    state = start_oauth(client)

    response = client.get(
        "/api/auth/discord/callback",
        params={"state": state},
    )

    assert response.status_code == 400
    assert client.cookies.get("discord_oauth_state") is None


def test_authorization_cancellation(client):
    state = start_oauth(client)

    response = client.get(
        "/api/auth/discord/callback",
        params={
            "error": "access_denied",
            "state": state,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "authorization_cancelled"
    }
    assert client.cookies.get("discord_oauth_state") is None


def test_discord_unavailable(client):
    state = start_oauth(client)

    with patch(
        "app.modules.auth.router.exchange_discord_code",
        side_effect=httpx.ConnectError("Discord unavailable"),
    ):
        response = client.get(
            "/api/auth/discord/callback",
            params={
                "code": "test_code",
                "state": state,
            },
            follow_redirects=False,
        )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Discord authentication unavailable"
    }
    assert client.cookies.get("discord_oauth_state") is None
    assert client.cookies.get("session_token") is None


def test_invalid_discord_authorization_code(client):
    state = start_oauth(client)

    request = httpx.Request(
        "POST",
        "https://discord.com/api/oauth2/token",
    )

    discord_response = httpx.Response(
        status_code=400,
        json={"error": "invalid_grant"},
        request=request,
    )

    with patch(
        "app.modules.auth.router.exchange_discord_code",
        side_effect=httpx.HTTPStatusError(
            "Invalid authorization code",
            request=request,
            response=discord_response,
        ),
    ):
        response = client.get(
            "/api/auth/discord/callback",
            params={
                "code": "invalid_code",
                "state": state,
            },
            follow_redirects=False,
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid or expired Discord authorization code"
    }

    assert client.cookies.get("discord_oauth_state") is None
    assert client.cookies.get("session_token") is None


def test_discord_oauth_error_rejects_code(client):
    state = start_oauth(client)

    with patch(
        "app.modules.auth.router.exchange_discord_code"
    ) as mock_exchange:
        response = client.get(
            "/api/auth/discord/callback",
            params={
                "error": "server_error",
                "code": "should_not_be_used",
                "state": state,
            },
            follow_redirects=False,
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Discord authorization failed"
    }

    # Aucun échange de code ne doit être tenté
    mock_exchange.assert_not_called()

    # Le cookie OAuth temporaire doit être supprimé
    assert client.cookies.get("discord_oauth_state") is None

    # Aucune session Team Baguette ne doit être créée
    assert client.cookies.get("session_token") is None


def test_unexpected_error_cleans_oauth_cookie(client):
    state = start_oauth(client)

    with patch(
        "app.modules.auth.router.exchange_discord_code",
        side_effect=RuntimeError("Simulated internal error"),
    ):
        response = client.get(
            "/api/auth/discord/callback",
            params={
                "code": "test_code",
                "state": state,
            },
            follow_redirects=False,
        )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal authentication error"
    }

    # Le cookie OAuth temporaire est supprimé
    assert client.cookies.get("discord_oauth_state") is None

    # Aucune session TB n'est créée
    assert client.cookies.get("session_token") is None
