"""
Database connection setup using SQLAlchemy + SQLite.
SQLite is fine for this project — zero setup, file-based, good enough for the assessment.
"""


import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a DB session per-request and closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
