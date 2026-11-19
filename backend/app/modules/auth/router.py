from typing import Annotated
import secrets
from datetime import timedelta
import httpx
import logging


from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, Header
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse

from app.modules.auth.discord import build_discord_authorization_url,exchange_discord_code,get_discord_user
from app.modules.auth.dependencies import get_current_session, get_db
from app.modules.auth.models import UserSession
from app.modules.auth.service import create_session, revoke_session
from app.modules.users.service import get_or_create_discord_user
from app.core.config import settings
from app.modules.users.models import User
from app.modules.players.models import Player

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_discord_avatar_url(
    discord_id: str,
    avatar_hash: str | None,
) -> str | None:
    if not avatar_hash:
        return None

    extension = "gif" if avatar_hash.startswith("a_") else "png"

    return (
        f"https://cdn.discordapp.com/avatars/"
        f"{discord_id}/{avatar_hash}.{extension}?size=128"
    )


@router.get("/me")
def get_me(
    current_session: Annotated[
        UserSession | None,
        Depends(get_current_session),
    ],
    db: Annotated[Session, Depends(get_db)],
):
    if current_session is None:
        return {"authenticated": False}

    user = db.get(User, current_session.user_id)

    if user is None:
        return {"authenticated": False}

    player = db.get(Player, user.player_id)

    if player is None:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "user_id": user.id,
        "display_name": player.primary_name,
        "discord_username": user.discord_username,
        "avatar_url": get_discord_avatar_url(
            user.discord_id,
            user.discord_avatar,
        ),
    }


@router.get("/discord/login")
def discord_login():
    state = secrets.token_urlsafe(32)

    authorization_url = build_discord_authorization_url(state)

    response = RedirectResponse(
        url=authorization_url,
        status_code=302,
    )

    response.set_cookie(
        key="discord_oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/api/auth/discord",
    )

    return response




@router.get("/discord/callback")
def discord_callback(
    db: Annotated[Session, Depends(get_db)],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    discord_oauth_state: Annotated[
        str | None,
        Cookie(),
    ] = None,
    
):

    
    
    if error is not None:
        valid_state = (
            bool(state)
            and bool(discord_oauth_state)
            and secrets.compare_digest(
                state,
                discord_oauth_state,
            )
        )

        
        if valid_state and error == "access_denied":
            response = JSONResponse(
                status_code=200,
                content={"status": "authorization_cancelled"},
            )
        elif valid_state:
            response = JSONResponse(
                status_code=400,
                content={"detail": "Discord authorization failed"},
            )
        else:
            response = JSONResponse(
                status_code=400,
                content={"detail": "Invalid Discord OAuth callback"},
            )

        response.delete_cookie(
            key="discord_oauth_state",
            path="/api/auth/discord",
        )

        return response


    valid_state = (
        bool(code)
        and bool(state)
        and bool(discord_oauth_state)
        and secrets.compare_digest(state, discord_oauth_state)
    )

    if not valid_state:
        response = JSONResponse(
            status_code=400,
            content={"detail": "Invalid Discord OAuth callback"},
        )
    else:
        try:
            # Récupérer l'identité Discord
            access_token = exchange_discord_code(code)
            discord_user = get_discord_user(access_token)

            # Retrouver ou créer l'utilisateur TB
            user = get_or_create_discord_user(
                db,
                discord_id=discord_user["id"],
                username=discord_user["username"],
                avatar=discord_user["avatar"],
            )

            # Créer notre propre session
            session_duration = timedelta(days=settings.session_duration_days)

            session_token = create_session(
                db,
                user_id=user.id,
                duration=session_duration,
            )

            # Valider ensemble le User, le Player et la session
            db.commit()

        
        
        except httpx.HTTPStatusError as exc:
            db.rollback()

            if exc.response.status_code == 400:
                status_code = 400
                detail = "Invalid or expired Discord authorization code"
            else:
                status_code = 502
                detail = "Discord authentication unavailable"

            response = JSONResponse(
                status_code=status_code,
                content={"detail": detail},
            )

            response.delete_cookie(
                key="discord_oauth_state",
                path="/api/auth/discord",
            )

            return response

        except httpx.RequestError:
            db.rollback()

            response = JSONResponse(
                status_code=502,
                content={"detail": "Discord authentication unavailable"},
            )

            response.delete_cookie(
                key="discord_oauth_state",
                path="/api/auth/discord",
            )

            return response


        except Exception:
            db.rollback()
            logger.exception(
                "Unexpected error during Discord OAuth callback"
            )

            response = JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal authentication error"
                },
            )

            response.delete_cookie(
                key="discord_oauth_state",
                path="/api/auth/discord",
            )

            return response



        # Revenir à l'accueil du site
        response = RedirectResponse(
            url="/",
            status_code=302,
        )

        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=int(session_duration.total_seconds()),
            httponly=True,
            secure=settings.cookie_secure,
            samesite="lax",
            path="/",
        )

    # Le state temporaire ne doit pas rester dans le navigateur
    response.delete_cookie(
        key="discord_oauth_state",
        path="/api/auth/discord",
    )

    return response



@router.post("/logout")
def logout(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    tb_request: Annotated[str | None, Header(alias="X-TB-Request")] = None,
    session_token: Annotated[
        str | None,
        Cookie(),
    ] = None,
):

    if tb_request != "1":
        raise HTTPException(
            status_code=403,
            detail="Invalid request",
        )

    if session_token:
        revoke_session(db, session_token)
        db.commit()

    response.delete_cookie(
        key="session_token",
        path="/",
    )

    return {"authenticated": False}
