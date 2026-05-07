from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_user, hash_password, require_admin
from app.database import get_db
from app.utils import add_audit_log

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


def get_admin_user(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user:
        return None
    if not require_admin(user):
        return None
    return user


@router.get("/sources")
def source_page(request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    sources = db.query(models.SourceConfig).order_by(models.SourceConfig.id.asc()).all()
    return templates.TemplateResponse(
        "admin_sources.html",
        {"request": request, "sources": sources, "user": user},
    )


@router.post("/sources/add")
def add_source(
    request: Request,
    name: str = Form(...),
    source_type: str = Form(...),
    base_url: str = Form(""),
    api_key: str = Form(""),
    enabled: str = Form("true"),
    db: Session = Depends(get_db),
):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    row = models.SourceConfig(
        name=name.strip(),
        source_type=source_type.strip(),
        base_url=base_url.strip() or None,
        api_key=api_key.strip() or None,
        enabled=enabled == "true",
    )
    db.add(row)

    try:
        db.commit()
        add_audit_log(db, user.id, "add_source", f"新增情报源 {row.name}")
    except IntegrityError:
        db.rollback()
        add_audit_log(db, user.id, "add_source_failed", f"新增情报源失败，名称重复：{name}")

    return RedirectResponse(url="/admin/sources", status_code=302)


@router.post("/sources/{source_id}/toggle")
def toggle_source(source_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    row = db.query(models.SourceConfig).filter(models.SourceConfig.id == source_id).first()
    if row:
        row.enabled = not row.enabled
        db.commit()
        add_audit_log(db, user.id, "toggle_source", f"切换情报源 {row.name} 状态为 {row.enabled}")

    return RedirectResponse(url="/admin/sources", status_code=302)


@router.post("/sources/{source_id}/update")
def update_source(
    source_id: int,
    request: Request,
    name: str = Form(...),
    source_type: str = Form(...),
    base_url: str = Form(""),
    api_key: str = Form(""),
    enabled: str = Form("true"),
    db: Session = Depends(get_db),
):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    row = db.query(models.SourceConfig).filter(models.SourceConfig.id == source_id).first()
    if row:
        old_name = row.name
        row.name = name.strip()
        row.source_type = source_type.strip()
        row.base_url = base_url.strip() or None
        row.api_key = api_key.strip() or None
        row.enabled = enabled == "true"

        try:
            db.commit()
            add_audit_log(db, user.id, "update_source", f"修改情报源 {old_name} -> {row.name}")
        except IntegrityError:
            db.rollback()
            add_audit_log(db, user.id, "update_source_failed", f"修改情报源失败，名称重复：{name}")

    return RedirectResponse(url="/admin/sources", status_code=302)


@router.post("/sources/{source_id}/delete")
def delete_source(source_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    row = db.query(models.SourceConfig).filter(models.SourceConfig.id == source_id).first()
    if row:
        source_name = row.name
        db.delete(row)
        db.commit()
        add_audit_log(db, user.id, "delete_source", f"删除情报源 {source_name}")

    return RedirectResponse(url="/admin/sources", status_code=302)


@router.get("/users")
def users_page(request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    users = db.query(models.User).order_by(models.User.id.asc()).all()
    return templates.TemplateResponse(
        "admin_users.html",
        {"request": request, "users": users, "user": user},
    )


@router.post("/users/add")
def add_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    row = models.User(
        username=username.strip(),
        password_hash=hash_password(password.strip()),
        role=role.strip(),
    )
    db.add(row)

    try:
        db.commit()
        add_audit_log(db, user.id, "add_user", f"新增用户 {row.username}")
    except IntegrityError:
        db.rollback()
        add_audit_log(db, user.id, "add_user_failed", f"新增用户失败，用户名重复：{username}")

    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{target_user_id}/update")
def update_user(
    target_user_id: int,
    request: Request,
    username: str = Form(...),
    role: str = Form(...),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    target = db.query(models.User).filter(models.User.id == target_user_id).first()
    if target:
        old_username = target.username
        target.username = username.strip()
        target.role = role.strip()
        if password.strip():
            target.password_hash = hash_password(password.strip())

        try:
            db.commit()
            add_audit_log(db, user.id, "update_user", f"修改用户 {old_username} -> {target.username}")
        except IntegrityError:
            db.rollback()
            add_audit_log(db, user.id, "update_user_failed", f"修改用户失败，用户名重复：{username}")

    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/users/{target_user_id}/delete")
def delete_user(target_user_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    target = db.query(models.User).filter(models.User.id == target_user_id).first()
    if target:
        if target.id == user.id:
            add_audit_log(db, user.id, "delete_user_blocked", "管理员尝试删除当前登录账号，被阻止")
            return RedirectResponse(url="/admin/users", status_code=302)

        username = target.username
        db.delete(target)
        db.commit()
        add_audit_log(db, user.id, "delete_user", f"删除用户 {username}")

    return RedirectResponse(url="/admin/users", status_code=302)


@router.get("/audit-logs")
def audit_logs_page(request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    logs = db.query(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100).all()

    user_map = {}
    user_ids = [log.user_id for log in logs if log.user_id]
    if user_ids:
        rows = db.query(models.User).filter(models.User.id.in_(user_ids)).all()
        user_map = {row.id: row.username for row in rows}

    return templates.TemplateResponse(
        "admin_audit_logs.html",
        {"request": request, "logs": logs, "user": user, "user_map": user_map},
    )