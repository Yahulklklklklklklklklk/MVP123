from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.database import Base, engine
from app.routers import admin, auth, search, web

Base.metadata.create_all(bind=engine)

app = FastAPI(title="开源威胁情报智能分级搜索平台")
app.add_middleware(SessionMiddleware, secret_key="threat-intel-platform-secret-key")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(web.router)
app.include_router(search.router)
app.include_router(admin.router)