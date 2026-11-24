from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: str
    password_hash: str
    role: str = Field(default="user")  # "user" or "admin"
    is_banned: bool = Field(default=False)
    ban_reason: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)


class UserSession(SQLModel, table=True):
    __tablename__ = "user_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    refresh_token_hash: str = Field(index=True)
    ip_address: str = Field(default="unknown")
    user_agent: str = Field(default="unknown")
    is_revoked: bool = Field(default=False)
    expires_at: datetime
    created_at: datetime = Field(default_factory=utc_now)


class Group(SQLModel, table=True):
    __tablename__ = "groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = Field(default="")
    owner_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=utc_now)


class GroupMember(SQLModel, table=True):
    __tablename__ = "group_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="groups.id", index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    can_create: bool = Field(default=False)
    can_edit: bool = Field(default=False)
    can_assign: bool = Field(default=False)


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    category: str = Field(default="Workshop")
    venue: str
    start_time: str
    end_time: str
    capacity: int = Field(default=50)
    owner_id: int = Field(foreign_key="users.id", index=True)
    group_id: Optional[int] = Field(default=None, foreign_key="groups.id", index=True)
    assigned_to: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=utc_now)


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    actor_email: str = Field(default="anonymous")
    action: str = Field(index=True)  # LOGIN, FAILED_LOGIN, LOGOUT, PASSWORD_CHANGE, ROLE_CHANGE, BAN, UNBAN, DELETE, EXPORT
    details: str = Field(default="")
    ip_address: str = Field(default="unknown")
    user_agent: str = Field(default="unknown")
    created_at: datetime = Field(default_factory=utc_now)