import os

from dotenv import load_dotenv

from db import models  # noqa: F401 — imports register the models on Base
from db import base as db_base


def _create_tables_for_url(database_url: str, label: str) -> None:
    db_base.configure_database(database_url)
    db_base.Base.metadata.create_all(db_base.engine)
    print(f"[{label}] Tables created on: {database_url}")


if __name__ == "__main__":
    load_dotenv()

    default_database_url = os.getenv("DATABASE_URL", "sqlite:///itemized_statements.db")
    staging_database_url = os.getenv("STAGING_DATABASE_URL")

    _create_tables_for_url(default_database_url, "default")

    if staging_database_url:
        _create_tables_for_url(staging_database_url, "staging")
    else:
        print("[staging] STAGING_DATABASE_URL not set; skipping staging table creation")

    print("Known tables:", list(db_base.Base.metadata.tables))