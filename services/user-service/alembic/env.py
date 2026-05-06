from logging.config import fileConfig
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, pool, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.engine import Connection
from alembic import context

config = context.config

sqlite_url = os.getenv("USER_DATABASE_URL", "sqlite:///./users.db")
sqlite_url = sqlite_url.replace("sqlite+aiosqlite://", "sqlite:///")

config.set_main_option("sqlalchemy.url", sqlite_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

metadata = MetaData()


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
