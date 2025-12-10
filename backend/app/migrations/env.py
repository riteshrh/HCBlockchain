from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Load environment variables from .env file before importing settings
from dotenv import load_dotenv
# Load .env from project root
# migrations/env.py -> app/migrations/env.py -> backend/app/migrations/env.py
# So we need to go up 3 levels to get to project root
project_root = Path(__file__).resolve().parents[3]
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✅ Loaded .env from: {env_path}")
else:
    # Try alternative paths just in case
    alt_paths = [
        Path(__file__).resolve().parents[2] / ".env",  # backend/.env
        Path(__file__).resolve().parents[1] / ".env",  # app/.env
    ]
    found = False
    for alt_path in alt_paths:
        if alt_path.exists():
            load_dotenv(alt_path, override=True)
            print(f"✅ Loaded .env from: {alt_path}")
            found = True
            break
    if not found:
        print(f"⚠️  Warning: .env file not found at {env_path}")
        print(f"   Also checked: {[str(p) for p in alt_paths]}")
        print("   Using environment variables or defaults")

# Add the backend directory to the path so we can import our app
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Import our models and config
from app.database.models import Base
from app.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the metadata for autogenerate support
target_metadata = Base.metadata

# Override sqlalchemy.url with our database URL (sync version for Alembic)
# Alembic needs a sync connection, so we convert asyncpg to psycopg2
# Also ensure we're using the correct database from settings
sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
# Debug output
print(f"\n🔧 Alembic Configuration:")
print(f"   DB_HOST from env: {os.getenv('DB_HOST', 'NOT SET')}")
print(f"   DB_NAME from env: {os.getenv('DB_NAME', 'NOT SET')}")
print(f"   Settings DB_HOST: {settings.db_host}")
print(f"   Settings DB_NAME: {settings.db_name}")
print(f"   Using database URL: {sync_url.replace(settings.db_password, '***') if settings.db_password else sync_url}\n")
config.set_main_option("sqlalchemy.url", sync_url)

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
