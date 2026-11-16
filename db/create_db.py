from db.base import Base, engine  
from db import models  # noqa: F401 — imports register the models on Base

if __name__ == "__main__":  
    Base.metadata.create_all(engine)  
    print("Tables created:", list(Base.metadata.tables))  