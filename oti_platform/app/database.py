from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

MYSQL_USER = "root"
MYSQL_PASSWORD = "123456qwer"
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = "3306"
MYSQL_DB = "threat_intel_platform"

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()