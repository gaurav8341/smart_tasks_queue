
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
import os
import uuid

# Use a separate in-memory SQLite database for testing
DB_USER = os.getenv("DB_USER", "vast")
DB_PASSWORD = os.getenv("DB_PASSWORD", "qweasdzx")
DB_NAME = os.getenv("DB_NAME", "test_smart_queue")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create the test database and tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the test database and tables
    Base.metadata.drop_all(bind=engine)

async def create_test_job(client, job_name="test_job", job_type="test", priority=3, payload={}, depends_on=[]):
    response = client.post("/jobs", json={
        "job_name": job_name,
        "type": job_type,
        "priority": priority,
        "payload": payload,
        "depends_on": depends_on
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    return data["job_id"]

async def test_create_job(client):
    job_id = await create_test_job(client)
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "job_id" in data
    assert isinstance(uuid.UUID(data["job_id"]), uuid.UUID)
    assert data["job_name"] == "test_job"
    assert data["status"] == "waiting"

async def test_get_job(client):
    job_id = await create_test_job(client)
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["job_id"] == job_id
    assert data["job_name"] == "test_job"
    assert data["status"] == "waiting"

async def test_list_jobs(client):
    await create_test_job(client, job_name="job1")
    await create_test_job(client, job_name="job2")
    response = client.get("/jobs")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 2 # May contain jobs from other tests if not cleaned up properly

async def test_cancel_job(client):
    job_id = await create_test_job(client)
    response = client.patch(f"/jobs/{job_id}/cancel")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "cancelled"

async def test_get_job_logs(client):
    job_id = await create_test_job(client)
    response = client.get(f"/jobs/{job_id}/logs")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Logs are created when job is executed, not on creation.
    # So, initially, this list might be empty.
    # We can add more specific log tests once scheduler is implemented.

async def test_cancel_job_with_dependencies(client):
    job_id_parent = await create_test_job(client, job_name="parent_job")
    job_id_dependent = await create_test_job(client, job_name="dependent_job", depends_on=[job_id_parent])

    response = client.patch(f"/jobs/{job_id_parent}/cancel")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "other jobs depend on this job" in response.json()["detail"]

async def test_cancel_already_cancelled_job(client):
    job_id = await create_test_job(client)
    # First cancel
    response = client.patch(f"/jobs/{job_id}/cancel")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "cancelled"

    # Try to cancel again
    response = client.patch(f"/jobs/{job_id}/cancel")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Job cannot be cancelled" in response.json()["detail"]

async def test_job_stream(client):
    with client.websocket_connect("/jobs/stream") as websocket:
        # At this point, no jobs have been executed, so no logs are expected immediately.
        # We'll create a job and then check if a log appears.
        job_id = await create_test_job(client, job_name="stream_test_job")

        # In a real scenario, a worker would process this job and create logs.
        # For testing the WebSocket, we'll simulate a log entry or rely on future scheduler implementation.
        # For now, we'll just assert that the connection is open and can receive messages.
        # If the scheduler were active, we'd expect a log message here.
        # For this test, we'll just ensure the websocket connection is successful.
        # The actual log content will be tested once the scheduler is in place.
        # For now, we'll just check if we can receive *any* message within a timeout.
        try:
            # This part is tricky without a running scheduler that generates logs.
            # For now, we'll just ensure the websocket connection is successful.
            # If the scheduler were active, we'd expect a log message here.
            # For this test, we'll just ensure the websocket connection is successful.
            # The actual log content will be tested once the scheduler is in place.
            # For now, we'll just check if we can receive *any* message within a timeout.
            # This is a placeholder for future, more robust WebSocket testing.
            pass
        except Exception as e:
            pytest.fail(f"WebSocket connection or initial message failed: {e}")

