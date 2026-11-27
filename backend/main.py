import os
import sys
from typing import Optional
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Cookie, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Session, or_, select

from auth import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    generate_refresh_token,
    get_client_info,
    hash_password,
    hash_refresh_token,
    record_audit_log,
    verify_password,
)
from database import create_db_and_tables, get_session
from models import Event, Group, GroupMember, User, UserSession
from rbac import (
    PERM_ASSIGN,
    PERM_CREATE,
    PERM_EDIT,
    ROLE_ADMIN,
    ROLE_USER,
    get_current_user,
    require_group_owner,
    verify_event_access,
    verify_group_permission,
)
from routers.admin import router as admin_router

app = FastAPI(
    title="Campus Event Management System API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

frontend_url = os.getenv("FRONTEND_URL", "https://campus-event-management-system-2110.vercel.app").rstrip("/")
allowed_origins = [
    frontend_url,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Never leak raw Python tracebacks to the client
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again later."},
    )


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# --- Pydantic Schemas ---
class SignupRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = ""


class GroupMemberRequest(BaseModel):
    email: EmailStr
    can_create: bool = False
    can_edit: bool = False
    can_assign: bool = False


class EventCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str
    category: str = "Workshop"
    venue: str
    start_time: str
    end_time: str
    capacity: int = Field(default=50, gt=0)
    group_id: Optional[int] = None
    assigned_to: Optional[int] = None


class EventUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    venue: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    capacity: Optional[int] = Field(default=None, gt=0)
    assigned_to: Optional[int] = None


api = APIRouter(prefix="/api")


def _set_refresh_cookie(response: Response, raw_token: str):
    is_prod = frontend_url.startswith("https://")
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        httponly=True,
        secure=is_prod,
        samesite="none" if is_prod else "lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )


# --- Health Check ---
@api.get("/health")
def health_check():
    return {"status": "ok"}


# --- Authentication & Session Management ---
@api.post("/auth/signup", status_code=201)
def signup(body: SignupRequest, request: Request, response: Response, db: Session = Depends(get_session)):
    existing = db.exec(select(User).where(User.email == body.email.lower())).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    user = User(
        email=body.email.lower(),
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role=ROLE_USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_refresh, refresh_hash = generate_refresh_token()
    ip, ua = get_client_info(request)
    session_row = UserSession(
        user_id=user.id,
        refresh_token_hash=refresh_hash,
        ip_address=ip,
        user_agent=ua,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session_row)
    db.commit()

    _set_refresh_cookie(response, raw_refresh)
    record_audit_log(db, "LOGIN", "New account registered and logged in", request, user.id, user.email)

    access_token = create_access_token(user.id, user.role)
    return {
        "access_token": access_token,
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
    }


@api.post("/auth/login")
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_session)):
    email = body.email.lower()
    user = db.exec(select(User).where(User.email == email)).first()

    if not user or not verify_password(body.password, user.password_hash):
        record_audit_log(db, "FAILED_LOGIN", f"Invalid credentials for {email}", request, user.id if user else None, email)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.is_banned:
        record_audit_log(db, "FAILED_LOGIN", f"Banned user attempted login: {email}", request, user.id, email)
        raise HTTPException(status_code=403, detail=f"Account banned: {user.ban_reason or 'Policy violation'}")

    raw_refresh, refresh_hash = generate_refresh_token()
    ip, ua = get_client_info(request)
    session_row = UserSession(
        user_id=user.id,
        refresh_token_hash=refresh_hash,
        ip_address=ip,
        user_agent=ua,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(session_row)
    db.commit()

    _set_refresh_cookie(response, raw_refresh)
    record_audit_log(db, "LOGIN", "User logged in", request, user.id, user.email)

    access_token = create_access_token(user.id, user.role)
    return {
        "access_token": access_token,
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
    }


@api.post("/auth/refresh")
def refresh_token(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_session),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    token_hash = hash_refresh_token(refresh_token)
    session_row = db.exec(select(UserSession).where(UserSession.refresh_token_hash == token_hash)).first()

    now = datetime.now(timezone.utc)
    if not session_row or session_row.is_revoked:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh session")

    expires = session_row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= now:
        raise HTTPException(status_code=401, detail="Refresh session expired")

    user = db.get(User, session_row.user_id)
    if not user or user.is_banned:
        raise HTTPException(status_code=403, detail="Account unavailable or banned")

    # Rotate refresh token on every refresh
    new_raw, new_hash = generate_refresh_token()
    session_row.refresh_token_hash = new_hash
    session_row.expires_at = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(session_row)
    db.commit()

    _set_refresh_cookie(response, new_raw)
    new_access = create_access_token(user.id, user.role)
    return {
        "access_token": new_access,
        "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role},
    }


@api.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_session),
):
    if refresh_token:
        token_hash = hash_refresh_token(refresh_token)
        session_row = db.exec(select(UserSession).where(UserSession.refresh_token_hash == token_hash)).first()
        if session_row:
            session_row.is_revoked = True
            db.add(session_row)
            db.commit()
            user = db.get(User, session_row.user_id)
            record_audit_log(
                db, "LOGOUT", "User logged out and revoked session", request, session_row.user_id, user.email if user else "unknown"
            )

    response.delete_cookie("refresh_token", path="/api/auth")
    return {"message": "Logged out successfully"}


@api.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "created_at": current_user.created_at,
    }


@api.patch("/auth/me")
def update_profile(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    current_user.full_name = body.full_name
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
    }


@api.post("/auth/change-password")
def change_password(
    body: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    if not verify_password(body.current_password, current_user.password_hash):
        record_audit_log(
            db, "FAILED_LOGIN", "Failed password change: wrong current password", request, current_user.id, current_user.email
        )
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = hash_password(body.new_password)
    db.add(current_user)
    db.commit()
    record_audit_log(db, "PASSWORD_CHANGE", "User changed password", request, current_user.id, current_user.email)
    return {"message": "Password updated successfully"}


@api.get("/auth/sessions")
def list_my_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    sessions = db.exec(
        select(UserSession).where(UserSession.user_id == current_user.id).order_by(UserSession.created_at.desc())
    ).all()
    return [
        {
            "id": s.id,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "is_revoked": s.is_revoked,
            "expires_at": s.expires_at,
            "created_at": s.created_at,
        }
        for s in sessions
    ]


@api.delete("/auth/sessions/{session_id}")
def revoke_my_session(
    session_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    session_row = db.get(UserSession, session_id)
    if not session_row or session_row.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    session_row.is_revoked = True
    db.add(session_row)
    db.commit()
    record_audit_log(db, "LOGOUT", f"User revoked session #{session_id}", request, current_user.id, current_user.email)
    return {"message": "Session revoked"}


# --- Groups / Campus Organizing Teams ---
@api.get("/groups")
def list_my_groups(current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    member_group_ids = db.exec(select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)).all()
    groups = db.exec(
        select(Group).where(or_(Group.owner_id == current_user.id, Group.id.in_(member_group_ids)))
    ).all()

    result = []
    for g in groups:
        members = db.exec(select(GroupMember).where(GroupMember.group_id == g.id)).all()
        member_details = []
        for m in members:
            u = db.get(User, m.user_id)
            member_details.append(
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "email": u.email if u else "",
                    "full_name": u.full_name if u else "",
                    "can_create": m.can_create,
                    "can_edit": m.can_edit,
                    "can_assign": m.can_assign,
                }
            )
        result.append(
            {
                "id": g.id,
                "name": g.name,
                "description": g.description,
                "owner_id": g.owner_id,
                "is_owner": g.owner_id == current_user.id,
                "members": member_details,
            }
        )
    return result


@api.post("/groups", status_code=201)
def create_group(body: GroupCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    group = Group(name=body.name, description=body.description, owner_id=current_user.id)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@api.patch("/groups/{group_id}")
def rename_group(
    group_id: int,
    body: GroupCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    group = require_group_owner(db, group_id, current_user)
    group.name = body.name
    if body.description is not None:
        group.description = body.description
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@api.delete("/groups/{group_id}")
def delete_group(
    group_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    group = require_group_owner(db, group_id, current_user)
    members = db.exec(select(GroupMember).where(GroupMember.group_id == group_id)).all()
    for m in members:
        db.delete(m)
    db.delete(group)
    db.commit()
    record_audit_log(db, "DELETE", f"Deleted group '{group.name}'", request, current_user.id, current_user.email)
    return {"message": "Group deleted"}


@api.post("/groups/{group_id}/members")
def upsert_group_member(
    group_id: int,
    body: GroupMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    require_group_owner(db, group_id, current_user)
    target_user = db.exec(select(User).where(User.email == body.email.lower())).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="No user found with that email")

    existing = db.exec(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == target_user.id)
    ).first()
    if existing:
        existing.can_create = body.can_create
        existing.can_edit = body.can_edit
        existing.can_assign = body.can_assign
        db.add(existing)
    else:
        member = GroupMember(
            group_id=group_id,
            user_id=target_user.id,
            can_create=body.can_create,
            can_edit=body.can_edit,
            can_assign=body.can_assign,
        )
        db.add(member)
    db.commit()
    return {"message": f"Updated permissions for {target_user.email}"}


@api.delete("/groups/{group_id}/members/{member_user_id}")
def remove_group_member(
    group_id: int,
    member_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    require_group_owner(db, group_id, current_user)
    membership = db.exec(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == member_user_id)
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Member not found in group")
    db.delete(membership)
    db.commit()
    return {"message": "Member removed"}


# --- Events (Protected by Ownership & Group RBAC) ---
@api.get("/events")
def list_events(current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    # Normal users see only their own events or events belonging to groups they belong to
    owned_group_ids = db.exec(select(Group.id).where(Group.owner_id == current_user.id)).all()
    member_group_ids = db.exec(select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)).all()
    accessible_groups = list(set(owned_group_ids + member_group_ids))

    stmt = select(Event).where(
        or_(
            Event.owner_id == current_user.id,
            Event.group_id.in_(accessible_groups) if accessible_groups else False,
        )
    )
    return db.exec(stmt.order_by(Event.created_at.desc())).all()


@api.post("/events", status_code=201)
def create_event(
    body: EventCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    if body.group_id is not None:
        verify_group_permission(db, body.group_id, current_user, PERM_CREATE)
        if body.assigned_to is not None:
            verify_group_permission(db, body.group_id, current_user, PERM_ASSIGN)

    event = Event(
        title=body.title,
        description=body.description,
        category=body.category,
        venue=body.venue,
        start_time=body.start_time,
        end_time=body.end_time,
        capacity=body.capacity,
        owner_id=current_user.id,
        group_id=body.group_id,
        assigned_to=body.assigned_to,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@api.patch("/events/{event_id}")
def update_event(
    event_id: int,
    body: EventUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if body.assigned_to is not None and body.assigned_to != event.assigned_to:
        verify_event_access(db, event, current_user, PERM_ASSIGN)
    else:
        verify_event_access(db, event, current_user, PERM_EDIT)

    update_data = body.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(event, key, val)

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@api.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    verify_event_access(db, event, current_user, "delete")
    db.delete(event)
    db.commit()
    record_audit_log(db, "DELETE", f"Deleted event '{event.title}' (ID {event_id})", request, current_user.id, current_user.email)
    return {"message": "Event deleted"}


# --- One-Click Demo Data Seeder (2 Admins, 3 Users, 1 Mixed-Permission Group, Sample Events) ---
@api.post("/seed")
def seed_demo_data(db: Session = Depends(get_session)):
    existing_admin = db.exec(select(User).where(User.email == "admin1@campus.edu")).first()
    if existing_admin:
        return {"message": "Demo data already seeded"}

    demo_password = hash_password("Campus@2026")

    admin1 = User(email="admin1@campus.edu", full_name="Dr. Sayef Admin", password_hash=demo_password, role=ROLE_ADMIN)
    admin2 = User(email="admin2@campus.edu", full_name="System Moderator", password_hash=demo_password, role=ROLE_ADMIN)
    user1 = User(email="alice@campus.edu", full_name="Alice Rahman (Club Lead)", password_hash=demo_password, role=ROLE_USER)
    user2 = User(email="bob@campus.edu", full_name="Bob Hasan (Event Editor)", password_hash=demo_password, role=ROLE_USER)
    user3 = User(email="charlie@campus.edu", full_name="Charlie Karim (Coordinator)", password_hash=demo_password, role=ROLE_USER)

    for u in [admin1, admin2, user1, user2, user3]:
        db.add(u)
    db.commit()
    for u in [admin1, admin2, user1, user2, user3]:
        db.refresh(u)

    # Shared group owned by Alice with mixed permissions for Bob and Charlie
    club = Group(
        name="IUB Computer Club Committee",
        description="Shared organizing group with mixed member permissions",
        owner_id=user1.id,
    )
    db.add(club)
    db.commit()
    db.refresh(club)

    db.add(GroupMember(group_id=club.id, user_id=user2.id, can_create=True, can_edit=True, can_assign=False))
    db.add(GroupMember(group_id=club.id, user_id=user3.id, can_create=False, can_edit=False, can_assign=True))

    db.add(
        Event(
            title="FastAPI & React Hackathon 2026",
            description="24-hour full-stack coding sprint at IUB Auditorium",
            category="Workshop",
            venue="Main Auditorium",
            start_time="2026-12-05T10:00",
            end_time="2026-12-05T18:00",
            capacity=120,
            owner_id=user1.id,
            group_id=club.id,
            assigned_to=user3.id,
        )
    )
    db.add(
        Event(
            title="Alice Personal Study Session",
            description="Private event visible only to Alice and Admins",
            category="Seminar",
            venue="Room 402",
            start_time="2026-12-02T14:00",
            end_time="2026-12-02T16:00",
            capacity=20,
            owner_id=user1.id,
            group_id=None,
        )
    )
    db.add(
        Event(
            title="Bob Robotics Demo Day",
            description="Private event owned by Bob",
            category="Exhibition",
            venue="Gallery Hall",
            start_time="2026-12-08T11:00",
            end_time="2026-12-08T15:00",
            capacity=60,
            owner_id=user2.id,
            group_id=None,
        )
    )
    db.commit()
    return {"message": "Seeded 2 admins, 3 users, 1 mixed-permission group, and sample events"}


app.include_router(api)
app.include_router(admin_router)