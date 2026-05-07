from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.auth import SESSION_KEY, authenticate_user
from app.database import get_db
from app.utils import add_audit_log

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "用户名或密码错误"})
    request.session[SESSION_KEY] = user.id
    add_audit_log(db, user.id, "login", f"用户 {user.username} 登录")
    return RedirectResponse(url="/", status_code=302)


@router.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get(SESSION_KEY)
    if user_id:
        add_audit_log(db, user_id, "logout", "用户退出登录")
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)