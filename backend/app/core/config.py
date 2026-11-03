import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str

    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str = field(repr=False)


settings = Settings(
    app_name="Team Baguette API",
    app_version="0.1.0",

    postgres_host=os.environ["POSTGRES_HOST"],
    postgres_port=5432,
    postgres_db=os.environ["POSTGRES_DB"],
    postgres_user=os.environ["POSTGRES_USER"],
    postgres_password=os.environ["POSTGRES_PASSWORD"],
)
