import os
import sys
from datetime import timedelta

# Set required env vars before importing backend modules
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_suite.db")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-for-pytest-only-123456")
os.environ.setdefault("PASSWORD_PEPPER", "test-pepper-key-for-pytest-only-123456")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from auth import create_access_token, hash_password
from database import get_session
from main import app
from models import User
from rbac import ROLE_ADMIN, ROLE_USER


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _create_user(session: Session, email: str, password: str, role: str = ROLE_USER, is_banned: bool = False) -> User:
    user = User(
        full_name=email.split("@")[0].title(),
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_banned=is_banned,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _auth_header(user: User) -> dict:
    token = create_access_token(user_id=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


def test_health_check(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200


def test_signup_and_login_flow(client: TestClient):
    signup = client.post("/api/auth/signup", json={
        "full_name": "Test Student",
        "email": "student@campus.edu",
        "password": "Password@2026"
    })
    assert signup.status_code in (200, 201)

    login = client.post("/api/auth/login", json={
        "email": "student@campus.edu",
        "password": "Password@2026"
    })
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_expired_and_tampered_token_rejected(client: TestClient, session: Session):
    user = _create_user(session, "alice@campus.edu", "Campus@2026")
    expired_token = create_access_token(
        user_id=user.id,
        role=user.role,
        expires_delta=timedelta(seconds=-10),
    )
    res_expired = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401

    res_tampered = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}tampered"})
    assert res_tampered.status_code == 401


def test_banned_user_rejected_immediately(client: TestClient, session: Session):
    user = _create_user(session, "banned@campus.edu", "Campus@2026", is_banned=False)
    headers = _auth_header(user)
    assert client.get("/api/auth/me", headers=headers).status_code == 200

    user.is_banned = True
    session.add(user)
    session.commit()

    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 403


def test_event_ownership_isolation(client: TestClient, session: Session):
    alice = _create_user(session, "alice@campus.edu", "Campus@2026")
    bob = _create_user(session, "bob@campus.edu", "Campus@2026")

    create_res = client.post("/api/events", headers=_auth_header(alice), json={
        "title": "Alice Private Workshop",
        "description": "Private event",
        "category": "Workshop",
        "venue": "BC5002",
        "start_time": "2026-12-10T10:00:00",
        "end_time": "2026-12-10T12:00:00",
        "capacity": 40
    })
    assert create_res.status_code in (200, 201)
    event_id = create_res.json()["id"]

    # Bob cannot update or delete Alice's private event
    patch_res = client.patch(f"/api/events/{event_id}", headers=_auth_header(bob), json={"title": "Hacked"})
    assert patch_res.status_code in (403, 404)


def test_group_permission_matrix(client: TestClient, session: Session):
    alice = _create_user(session, "alice@campus.edu", "Campus@2026")
    charlie = _create_user(session, "charlie@campus.edu", "Campus@2026")

    # Alice creates group
    grp = client.post("/api/groups", headers=_auth_header(alice), json={
        "name": "IUB Computer Club",
        "description": "Club committee"
    })
    assert grp.status_code in (200, 201)
    group_id = grp.json()["id"]

    # Add Charlie with assign-only permission (can_edit=False, can_create=False)
    add_member = client.post(f"/api/groups/{group_id}/members", headers=_auth_header(alice), json={
        "email": "charlie@campus.edu",
        "can_create": False,
        "can_edit": False,
        "can_assign": True
    })
    assert add_member.status_code in (200, 201)

    # Charlie tries to create a group event -> must get 403
    denied = client.post("/api/events", headers=_auth_header(charlie), json={
        "title": "Unauthorized Event",
        "description": "Should fail",
        "category": "Seminar",
        "venue": "Auditorium",
        "start_time": "2026-12-12T10:00:00",
        "end_time": "2026-12-12T12:00:00",
        "capacity": 100,
        "group_id": group_id
    })
    assert denied.status_code == 403


def test_admin_self_protection_and_admin_ban_rule(client: TestClient, session: Session):
    admin1 = _create_user(session, "admin1@campus.edu", "Campus@2026", role=ROLE_ADMIN)
    admin2 = _create_user(session, "admin2@campus.edu", "Campus@2026", role=ROLE_ADMIN)
    normal = _create_user(session, "user@campus.edu", "Campus@2026", role=ROLE_USER)

    # Admin cannot ban another admin
    ban_admin = client.post(f"/api/admin/users/{admin2.id}/ban", headers=_auth_header(admin1), json={"reason": "Test"})
    assert ban_admin.status_code in (400, 403)

    # Admin cannot demote themselves
    demote_self = client.patch(f"/api/admin/users/{admin1.id}/role", headers=_auth_header(admin1), json={"role": ROLE_USER})
    assert demote_self.status_code in (400, 403)

    # Normal user cannot access admin endpoints
    user_admin_call = client.get("/api/admin/users", headers=_auth_header(normal))
    assert user_admin_call.status_code == 403