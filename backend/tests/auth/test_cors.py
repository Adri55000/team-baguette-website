from fastapi.testclient import TestClient

from app.main import app


def test_external_origin_cannot_use_custom_auth_header():
    with TestClient(app) as client:
        response = client.options(
            "/api/auth/logout",
            headers={
                "Origin": "https://site-exterieur.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-TB-Request",
            },
        )

    assert (
        response.headers.get("access-control-allow-origin")
        != "https://site-exterieur.example"
    )

    assert response.headers.get(
        "access-control-allow-credentials"
    ) != "true"

