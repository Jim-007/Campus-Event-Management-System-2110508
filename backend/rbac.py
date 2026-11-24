from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from auth import decode_access_token
from database import get_session
from models import Event, Group, GroupMember, User

# Permission Constants
ROLE_USER = "user"
ROLE_ADMIN = "admin"

PERM_CREATE = "create"
PERM_EDIT = "edit"
PERM_ASSIGN = "assign"

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_session),
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization token",
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired",
        )

    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found",
        )

    # Safety Rule: Banned users are rejected immediately on their very next request
    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account banned: {user.ban_reason or 'Policy violation'}",
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def verify_group_permission(db: Session, group_id: int, user: User, permission: str) -> Group:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Group owner and system admins have full access
    if user.role == ROLE_ADMIN or group.owner_id == user.id:
        return group

    membership = db.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user.id,
        )
    ).first()

    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")

    allowed = (
        (permission == PERM_CREATE and membership.can_create)
        or (permission == PERM_EDIT and membership.can_edit)
        or (permission == PERM_ASSIGN and membership.can_assign)
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing '{permission}' permission in this group",
        )
    return group


def verify_event_access(db: Session, event: Event, user: User, action: str) -> None:
    """Enforces ownership and shared-group permissions on an Event."""
    if user.role == ROLE_ADMIN or event.owner_id == user.id:
        return

    if event.group_id is not None:
        # Only the event owner or group owner can delete an event; members can edit/assign if permitted
        if action == "delete":
            group = db.get(Group, event.group_id)
            if group and group.owner_id == user.id:
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the event creator or group owner can delete this event",
            )
        verify_group_permission(db, event.group_id, user, action)
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access or modify this event",
    )


def require_group_owner(db: Session, group_id: int, user: User) -> Group:
    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if group.owner_id != user.id and user.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can rename, delete, or manage members",
        )
    return group