import os
from dataclasses import dataclass, field
from pathlib import Path

def parse_bool_env(name: str, default: str = "true") -> bool:
    value = os.environ.get(name, default).strip().lower()

    if value == "true":
        return True

    if value == "false":
        return False

    raise ValueError(
        f"{name} must be 'true' or 'false'"
    )


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str

    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str = field(repr=False)
    storage_root: Path
    resources_root: Path
    discord_client_id: str
    discord_client_secret: str = field(repr=False)
    discord_redirect_uri: str
    cookie_secure: bool
    session_duration_days: int


    def __post_init__(self) -> None:
        if self.session_duration_days <= 0:
            raise ValueError(
                "SESSION_DURATION_DAYS must be greater than zero"
            )



settings = Settings(
    app_name="Team Baguette API",
    app_version="0.1.0",

    postgres_host=os.environ["POSTGRES_HOST"],
    postgres_port=5432,
    postgres_db=os.environ["POSTGRES_DB"],
    postgres_user=os.environ["POSTGRES_USER"],
    postgres_password=os.environ["POSTGRES_PASSWORD"],

    storage_root=Path(os.environ["STORAGE_ROOT"]),
    resources_root=Path(__file__).resolve().parents[2] / "resources",

    discord_client_id=os.environ["DISCORD_CLIENT_ID"],
    discord_client_secret=os.environ["DISCORD_CLIENT_SECRET"],
    discord_redirect_uri=os.environ["DISCORD_REDIRECT_URI"],
    cookie_secure=parse_bool_env("COOKIE_SECURE"),
    session_duration_days=int(os.environ.get("SESSION_DURATION_DAYS", "30")),
)
