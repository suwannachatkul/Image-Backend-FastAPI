import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base_class import Base
from app.db import session


SQLALCHEMY_DATABASE_URL = "postgresql://postgres:10475@localhost:5432/myimage_fastapi_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="class")
def test_db_session():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    # Drop the database tables after the tests are done
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="class")
def test_client(test_db_session):
    # Override the get_db function
    def override_get_db():
        yield test_db_session

    app.dependency_overrides[session.get_db] = override_get_db

    return TestClient(app)
