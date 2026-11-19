import secrets
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.main import app
from app.core.config import settings
from app.infrastructure.database.database import SessionLocal
from app.modules.auth.models import UserSession
from app.modules.players.models import Player
from app.modules.users.models import User


def test_successful_discord_login():
    discord_id = "test_" + secrets.token_hex(12)

    try:
        with (
            patch(
                "app.modules.auth.router.exchange_discord_code",
                return_value="fake_access_token",
            ),
            patch(
                "app.modules.auth.router.get_discord_user",
                return_value={
                    "id": discord_id,
                    "username": "BaguettePytest",
                    "avatar": None,
                },
            ),
            TestClient(app) as client,
        ):
            # Démarrer OAuth2
            response = client.get(
                "/api/auth/discord/login",
                follow_redirects=False,
            )

            assert response.status_code == 302

            # Vérifier le cookie temporaire OAuth2
            oauth_cookie = response.headers["set-cookie"].lower()

            assert "discord_oauth_state=" in oauth_cookie
            assert "httponly" in oauth_cookie
            assert "samesite=lax" in oauth_cookie
            assert "path=/api/auth/discord" in oauth_cookie
            assert "max-age=600" in oauth_cookie
            assert ("secure" in oauth_cookie) == settings.cookie_secure

            state = client.cookies.get("discord_oauth_state")
            assert state is not None

            # Simuler le retour réussi de Discord
            response = client.get(
                "/api/auth/discord/callback",
                params={
                    "code": "fake_code",
                    "state": state,
                },
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert response.headers["location"] == "/"


            # Vérifier les attributs du cookie de session
            cookies = response.headers.get_list("set-cookie")

            session_cookie = next(
                cookie.lower()
                for cookie in cookies
                if cookie.startswith("session_token=")
            )

            assert "httponly" in session_cookie
            assert "samesite=lax" in session_cookie
            assert "path=/" in session_cookie

            expected_age = settings.session_duration_days * 86400
            assert f"max-age={expected_age}" in session_cookie

            assert (
                "secure" in session_cookie
            ) == settings.cookie_secure


            # Vérifier les cookies
            assert client.cookies.get("discord_oauth_state") is None
            assert client.cookies.get("session_token") is not None

            # Vérifier que l'API reconnaît l'utilisateur
            response = client.get("/api/auth/me")

            assert response.status_code == 200

            data = response.json()

            assert data["authenticated"] is True
            assert data["display_name"] == "BaguettePytest"
            assert data["discord_username"] == "BaguettePytest"

            # Vérifier le compte PostgreSQL
            with SessionLocal() as db:
                user = db.scalar(
                    select(User).where(User.discord_id == discord_id)
                )

                assert user is not None
                assert data["user_id"] == user.id
                assert db.get(Player, user.player_id) is not None
            
            # Refuser une déconnexion sans protection CSRF
            response = client.post("/api/auth/logout")

            assert response.status_code == 403

            # L'utilisateur doit toujours être connecté
            response = client.get("/api/auth/me")
            assert response.json()["authenticated"] is True

            # Déconnexion autorisée
            response = client.post(
                "/api/auth/logout",
                headers={"X-TB-Request": "1"},
            )

            assert response.status_code == 200
            assert response.json() == {"authenticated": False}
            assert client.cookies.get("session_token") is None

            # Le cookie ne permet plus de s'authentifier
            response = client.get("/api/auth/me")
            assert response.json() == {"authenticated": False}

            # Le compte existe toujours, mais plus sa session
            with SessionLocal() as db:
                user = db.scalar(
                    select(User).where(User.discord_id == discord_id)
                )

                assert user is not None

                sessions = db.scalars(
                    select(UserSession).where(
                        UserSession.user_id == user.id
                    )
                ).all()

                assert sessions == []


    finally:
        # Nettoyer les données créées et validées
        with SessionLocal() as db:
            try:
                user = db.scalar(
                    select(User).where(User.discord_id == discord_id)
                )

                if user is not None:
                    player_id = user.player_id

                    db.execute(
                        delete(UserSession).where(
                            UserSession.user_id == user.id
                        )
                    )

                    db.delete(user)
                    db.flush()

                    player = db.get(Player, player_id)
                    if player is not None:
                        db.delete(player)

                    db.commit()

            except Exception:
                db.rollback()
                raise
