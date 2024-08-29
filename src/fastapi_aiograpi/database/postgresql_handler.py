from ..utils.config_secrets import Secrets
from sqlmodel import SQLModel, create_engine, Session

# PostgreSQL database URL
DATABASE_URL = Secrets.POSTGRES.POSTGRES_URL

# Create a database engine
engine = create_engine(DATABASE_URL)


# Create a session maker
def get_session():
    with Session(engine) as session:
        yield session


# Create all tables
SQLModel.metadata.create_all(engine)
