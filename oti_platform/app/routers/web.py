from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app import models
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@router.get("/history")
def history(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    histories = (
        db.query(models.QueryHistory)
        .filter(models.QueryHistory.user_id == user.id)
        .order_by(models.QueryHistory.queried_at.desc())
        .limit(50)
        .all()
    )
    return templates.TemplateResponse("history.html", {"request": request, "user": user, "histories": histories})