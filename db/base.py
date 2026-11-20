import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# for alembic
NAMING_CONVENTION = {  
    "ix": "ix_%(column_0_label)s",  
    "uq": "uq_%(table_name)s_%(column_0_name)s",  
    "ck": "ck_%(table_name)s_%(constraint_name)s",  
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  
    "pk": "pk_%(table_name)s",  
}

class Base(DeclarativeBase):  
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///itemized_statements.db")

engine = create_engine(  
    DATABASE_URL,  
    echo=False,        # flip to True while developing to see the SQL  
    pool_pre_ping=True # reconnects dead pooled connections (important for long RPA runs)  
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def configure_database(database_url: str) -> None:
    """Rebind engine/session factory at runtime.

    Useful for routing dry-run executions to a staging database while keeping
    the normal default from DATABASE_URL.
    """
    global DATABASE_URL, engine, SessionLocal

    if not database_url:
        raise ValueError("database_url must be a non-empty string")

    previous_engine = engine

    DATABASE_URL = database_url
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    try:
        previous_engine.dispose()
    except Exception:
        # Best effort cleanup; do not block reconfiguration.
        pass

@contextmanager  
def session_scope():  
    """Transactional scope. Commits on success, rolls back on exception."""  
    session = SessionLocal()  
    try:  
        yield session  
        session.commit()  
    except Exception:  
        session.rollback()  
        raise  
    finally:  
        session.close()  