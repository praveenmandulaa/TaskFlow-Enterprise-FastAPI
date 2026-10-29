
from pathlib import Path

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

import app.models  # Register SQLAlchemy models
from app.db.base import Base
from app.db.session import get_db
from app.main import app


config = dotenv_values(
    Path(__file__).resolve().parents[1] / ".env.test"
)

TEST_DATABASE_URL = config.get("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL is missing from .env.test"
    )

if not TEST_DATABASE_URL.rsplit("/", 1)[-1] == "taskflow_test_db":
    raise RuntimeError(
        "Tests must use the taskflow_test_db database"
    )

engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    # Only run against the dedicated test database.
    Base.metadata.create_all(bind=engine)

    yield

    # Do not drop the entire schema automatically.
    # We will use transaction-based isolation later.


@pytest.fixture
def client():
    def override_get_db():
        with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
