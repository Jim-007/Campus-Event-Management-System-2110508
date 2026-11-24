import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine

load_dotenv()

raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./local_dev.db")

if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql+pg8000://", 1)
elif raw_db_url.startswith("postgresql://"):
    raw_db_url = raw_db_url.replace("postgresql://", "postgresql+pg8000://", 1)

if "?pgbouncer=true" in raw_db_url:
    raw_db_url = raw_db_url.replace("?pgbouncer=true", "")

connect_args = {"check_same_thread": False} if raw_db_url.startswith("sqlite") else {}
engine = create_engine(raw_db_url, echo=False, connect_args=connect_args, pool_pre_ping=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session