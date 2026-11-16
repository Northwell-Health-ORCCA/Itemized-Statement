import os  
from contextlib import contextmanager

from sqlalchemy import create_engine  
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):  
    pass

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///itemized_statements.db")

engine = create_engine(  
    DATABASE_URL,  
    echo=False,        # flip to True while developing to see the SQL  
    pool_pre_ping=True # reconnects dead pooled connections (important for long RPA runs)  
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

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