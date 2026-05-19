import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
import app.models as models

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def auth_headers():
    client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "secretpassword",
        "skill_level": 3
    })

    login_res = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "secretpassword"
    })

    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_and_login():
    reg_res = client.post("/auth/register", json={
        "email": "unique@example.com",
        "password": "secretpassword",
        "skill_level": 3
    })
    assert reg_res.status_code == 201
    assert reg_res.json()["email"] == "unique@example.com"

    login_res = client.post("/auth/login", data={
        "username": "unique@example.com",
        "password": "secretpassword"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_business_logic_flow(auth_headers):
    proj_res = client.post("/projects/", json={"name": "AI Dev", "description": "FastAPI Project"},
                           headers=auth_headers)
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    task_res = client.post(f"/projects/{proj_id}/tasks/", json={
        "title": "Write Code",
        "priority": 2,
        "estimated_hours": 5.0
    }, headers=auth_headers)
    assert task_res.status_code == 201

    opt_res = client.post(f"/projects/{proj_id}/optimize-assignments", headers=auth_headers)
    assert opt_res.status_code == 200
    assert "Успешно оптимизировано" in opt_res.json()["message"]