from urllib.parse import urlencode
import httpx

from app.core.config import settings


DISCORD_AUTHORIZE_URL = "https://discord.com/oauth2/authorize"


def build_discord_authorization_url(state: str) -> str:
    parameters = {
        "client_id": settings.discord_client_id,
        "redirect_uri": settings.discord_redirect_uri,
        "response_type": "code",
        "scope": "identify",
        "state": state,
    }

    return f"{DISCORD_AUTHORIZE_URL}?{urlencode(parameters)}"


DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"


def exchange_discord_code(code: str) -> str:
    response = httpx.post(
        DISCORD_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.discord_redirect_uri,
        },
        auth=(
            settings.discord_client_id,
            settings.discord_client_secret,
        ),
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()["access_token"]



DISCORD_USER_URL = "https://discord.com/api/users/@me"


def get_discord_user(access_token: str) -> dict:
    response = httpx.get(
        DISCORD_USER_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        timeout=10.0,
    )

    response.raise_for_status()

    user = response.json()

    return {
        "id": user["id"],
        "username": user["username"],
        "avatar": user.get("avatar"),
    }
