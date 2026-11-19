
from logging.config import fileConfig

from alembic import context

from app.infrastructure.database.database import Base, database_url, engine

# Charger les modèles pour les enregistrer dans Base.metadata
from app.modules.players.models import Player, PlayerAlias
from app.modules.users.models import User
from app.modules.auth.models import UserSession
from app.modules.uploads.models import Upload


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=database_url.render_as_string(
            hide_password=False
        ),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
