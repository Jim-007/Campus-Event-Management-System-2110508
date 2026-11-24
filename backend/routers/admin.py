import csv
import io
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, or_, select

from auth import record_audit_log
from database import get_session
from models import AuditLog, Event, Group, GroupMember, User, UserSession
from rbac import ROLE_ADMIN, ROLE_USER, require_admin

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(require_admin)],
)


class BanRequest(BaseModel):
    reason: str = "Violation of campus policy"


class BulkUserIdsRequest(BaseModel):
    user_ids: List[int]
    reason: Optional[str] = "Bulk administrative action"


class BulkDeleteIdsRequest(BaseModel):
    ids: List[int]


class RoleUpdateRequest(BaseModel):
    role: str


@router.get("/stats")
def get_admin_stats(db: Session = Depends(get_session)):
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    total_users = db.exec(select(func.count(User.id))).one()
    banned_users = db.exec(select(func.count(User.id)).where(User.is_banned == True)).one()
    total_events = db.exec(select(func.count(Event.id))).one()
    total_groups = db.exec(select(func.count(Group.id))).one()

    new_users_7d = db.exec(select(func.count(User.id)).where(User.created_at >= seven_days_ago)).one()
    new_events_7d = db.exec(select(func.count(Event.id)).where(Event.created_at >= seven_days_ago)).one()
    new_groups_7d = db.exec(select(func.count(Group.id)).where(Group.created_at >= seven_days_ago)).one()

    return {
        "total_users": total_users,
        "banned_users": banned_users,
        "total_events": total_events,
        "total_groups": total_groups,
        "new_last_7_days": {
            "users": new_users_7d,
            "events": new_events_7d,
            "groups": new_groups_7d,
        },
    }


@router.get("/users")
def list_users(
    search: Optional[str] = None,
    role: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_session),
):
    stmt = select(User)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
    if role in (ROLE_USER, ROLE_ADMIN):
        stmt = stmt.where(User.role == role)
    if status_filter == "banned":
        stmt = stmt.where(User.is_banned == True)
    elif status_filter == "active":
        stmt = stmt.where(User.is_banned == False)

    all_matching = db.exec(stmt.order_by(User.created_at.desc())).all()
    total = len(all_matching)
    start = (page - 1) * limit
    items = all_matching[start : start + limit]

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_banned": u.is_banned,
                "ban_reason": u.ban_reason,
                "created_at": u.created_at,
            }
            for u in items
        ],
    }


@router.get("/users/{user_id}")
def get_user_detail(user_id: int, db: Session = Depends(get_session)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    events = db.exec(select(Event).where(Event.owner_id == user_id)).all()
    memberships = db.exec(select(GroupMember).where(GroupMember.user_id == user_id)).all()
    owned_groups = db.exec(select(Group).where(Group.owner_id == user_id)).all()
    sessions = db.exec(
        select(UserSession).where(UserSession.user_id == user_id).order_by(UserSession.created_at.desc())
    ).all()
    logs = db.exec(
        select(AuditLog)
        .where(or_(AuditLog.user_id == user_id, AuditLog.actor_email == user.email))
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    ).all()

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_banned": user.is_banned,
            "ban_reason": user.ban_reason,
            "created_at": user.created_at,
        },
        "events": events,
        "owned_groups": owned_groups,
        "memberships": memberships,
        "sessions": [
            {
                "id": s.id,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "is_revoked": s.is_revoked,
                "expires_at": s.expires_at,
                "created_at": s.created_at,
            }
            for s in sessions
        ],
        "recent_activity": logs,
    }


@router.post("/users/{user_id}/ban")
def ban_user(
    user_id: int,
    body: BanRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Admins cannot ban themselves")
    if target.role == ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Admins cannot ban another admin")

    target.is_banned = True
    target.ban_reason = body.reason
    db.add(target)
    db.commit()

    record_audit_log(
        db, "BAN", f"Banned user {target.email} (ID {target.id}): {body.reason}", request, admin.id, admin.email
    )
    return {"message": f"User {target.email} has been banned"}


@router.post("/users/{user_id}/unban")
def unban_user(
    user_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target.is_banned = False
    target.ban_reason = None
    db.add(target)
    db.commit()

    record_audit_log(db, "UNBAN", f"Unbanned user {target.email} (ID {target.id})", request, admin.id, admin.email)
    return {"message": f"User {target.email} has been unbanned"}


@router.post("/users/bulk-ban")
def bulk_ban_users(
    body: BulkUserIdsRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    banned_count = 0
    for uid in body.user_ids:
        target = db.get(User, uid)
        if target and target.id != admin.id and target.role != ROLE_ADMIN:
            target.is_banned = True
            target.ban_reason = body.reason or "Bulk ban"
            db.add(target)
            banned_count += 1
    db.commit()
    record_audit_log(db, "BAN", f"Bulk banned {banned_count} users: {body.reason}", request, admin.id, admin.email)
    return {"message": f"Banned {banned_count} users"}


@router.post("/users/bulk-unban")
def bulk_unban_users(
    body: BulkUserIdsRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    unbanned_count = 0
    for uid in body.user_ids:
        target = db.get(User, uid)
        if target:
            target.is_banned = False
            target.ban_reason = None
            db.add(target)
            unbanned_count += 1
    db.commit()
    record_audit_log(db, "UNBAN", f"Bulk unbanned {unbanned_count} users", request, admin.id, admin.email)
    return {"message": f"Unbanned {unbanned_count} users"}


@router.patch("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    body: RoleUpdateRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    if body.role not in (ROLE_USER, ROLE_ADMIN):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="Admins cannot change their own role")

    old_role = target.role
    target.role = body.role
    db.add(target)
    db.commit()

    record_audit_log(
        db,
        "ROLE_CHANGE",
        f"Changed {target.email} role from {old_role} to {body.role}",
        request,
        admin.id,
        admin.email,
    )
    return {"message": f"Updated {target.email} role to {body.role}"}


@router.post("/users/{user_id}/revoke-sessions")
def revoke_user_sessions(
    user_id: int,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    sessions = db.exec(select(UserSession).where(UserSession.user_id == user_id, UserSession.is_revoked == False)).all()
    for s in sessions:
        s.is_revoked = True
        db.add(s)
    db.commit()

    record_audit_log(
        db, "LOGOUT", f"Admin revoked {len(sessions)} active sessions for {target.email}", request, admin.id, admin.email
    )
    return {"message": f"Revoked {len(sessions)} sessions for {target.email}"}


@router.get("/events")
def admin_list_events(search: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_session)):
    stmt = select(Event)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Event.title.ilike(pattern), Event.venue.ilike(pattern)))
    if category:
        stmt = stmt.where(Event.category == category)
    return db.exec(stmt.order_by(Event.created_at.desc())).all()


@router.post("/events/bulk-delete")
def admin_bulk_delete_events(
    body: BulkDeleteIdsRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    deleted = 0
    for eid in body.ids:
        ev = db.get(Event, eid)
        if ev:
            db.delete(ev)
            deleted += 1
    db.commit()
    record_audit_log(db, "DELETE", f"Admin deleted {deleted} events (IDs: {body.ids})", request, admin.id, admin.email)
    return {"message": f"Deleted {deleted} events"}


@router.get("/groups")
def admin_list_groups(search: Optional[str] = None, db: Session = Depends(get_session)):
    stmt = select(Group)
    if search:
        stmt = stmt.where(Group.name.ilike(f"%{search}%"))
    return db.exec(stmt.order_by(Group.created_at.desc())).all()


@router.post("/groups/bulk-delete")
def admin_bulk_delete_groups(
    body: BulkDeleteIdsRequest,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    deleted = 0
    for gid in body.ids:
        grp = db.get(Group, gid)
        if grp:
            members = db.exec(select(GroupMember).where(GroupMember.group_id == gid)).all()
            for m in members:
                db.delete(m)
            db.delete(grp)
            deleted += 1
    db.commit()
    record_audit_log(db, "DELETE", f"Admin deleted {deleted} groups (IDs: {body.ids})", request, admin.id, admin.email)
    return {"message": f"Deleted {deleted} groups"}


@router.get("/logs")
def admin_audit_logs(
    action: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_session),
):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                AuditLog.actor_email.ilike(pattern),
                AuditLog.details.ilike(pattern),
                AuditLog.ip_address.ilike(pattern),
            )
        )
    return db.exec(stmt.order_by(AuditLog.created_at.desc()).limit(200)).all()


@router.get("/security")
def admin_security_view(db: Session = Depends(get_session)):
    failed_logs = db.exec(
        select(AuditLog).where(AuditLog.action == "FAILED_LOGIN").order_by(AuditLog.created_at.desc())
    ).all()

    by_ip: dict[str, int] = {}
    by_account: dict[str, int] = {}
    for log in failed_logs:
        by_ip[log.ip_address] = by_ip.get(log.ip_address, 0) + 1
        by_account[log.actor_email] = by_account.get(log.actor_email, 0) + 1

    return {
        "total_failed_logins": len(failed_logs),
        "by_ip": [{"ip_address": k, "count": v} for k, v in sorted(by_ip.items(), key=lambda x: -x[1])],
        "by_account": [{"email": k, "count": v} for k, v in sorted(by_account.items(), key=lambda x: -x[1])],
        "recent_failures": failed_logs[:25],
    }


@router.get("/export/{resource}")
def export_csv(
    resource: str,
    request: Request,
    search: Optional[str] = None,
    role: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    action: Optional[str] = None,
    category: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_session),
):
    output = io.StringIO()
    writer = csv.writer(output)

    if resource == "users":
        stmt = select(User)
        if search:
            stmt = stmt.where(or_(User.email.ilike(f"%{search}%"), User.full_name.ilike(f"%{search}%")))
        if role in (ROLE_USER, ROLE_ADMIN):
            stmt = stmt.where(User.role == role)
        if status_filter == "banned":
            stmt = stmt.where(User.is_banned == True)
        elif status_filter == "active":
            stmt = stmt.where(User.is_banned == False)
        rows = db.exec(stmt).all()
        writer.writerow(["ID", "Email", "Full Name", "Role", "Is Banned", "Ban Reason", "Created At"])
        for u in rows:
            writer.writerow([u.id, u.email, u.full_name, u.role, u.is_banned, u.ban_reason or "", u.created_at])

    elif resource == "events":
        stmt = select(Event)
        if search:
            stmt = stmt.where(or_(Event.title.ilike(f"%{search}%"), Event.venue.ilike(f"%{search}%")))
        if category:
            stmt = stmt.where(Event.category == category)
        rows = db.exec(stmt).all()
        writer.writerow(["ID", "Title", "Category", "Venue", "Start Time", "End Time", "Capacity", "Owner ID", "Group ID"])
        for e in rows:
            writer.writerow([e.id, e.title, e.category, e.venue, e.start_time, e.end_time, e.capacity, e.owner_id, e.group_id])

    elif resource == "logs":
        stmt = select(AuditLog)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if search:
            stmt = stmt.where(or_(AuditLog.actor_email.ilike(f"%{search}%"), AuditLog.details.ilike(f"%{search}%")))
        rows = db.exec(stmt.order_by(AuditLog.created_at.desc())).all()
        writer.writerow(["ID", "Timestamp", "Actor Email", "Action", "Details", "IP Address", "User Agent"])
        for l in rows:
            writer.writerow([l.id, l.created_at, l.actor_email, l.action, l.details, l.ip_address, l.user_agent])
    else:
        raise HTTPException(status_code=400, detail="Invalid export type. Use users, events, or logs.")

    record_audit_log(db, "EXPORT", f"Exported {resource} CSV", request, admin.id, admin.email)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={resource}_export.csv"},
    )