from app.auth import hash_password
from app.database import Base, engine, SessionLocal
from app import models


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    admin = db.query(models.User).filter(models.User.username == "admin").first()
    analyst = db.query(models.User).filter(models.User.username == "analyst").first()

    if not admin:
        db.add(models.User(username="admin", password_hash=hash_password("admin123"), role="admin"))
    if not analyst:
        db.add(models.User(username="analyst", password_hash=hash_password("analyst123"), role="analyst"))

    mock_source = db.query(models.SourceConfig).filter(models.SourceConfig.name == "Mock Feed").first()
    if not mock_source:
        db.add(models.SourceConfig(name="Mock Feed", source_type="mock_feed", enabled=True))

    otx_source = db.query(models.SourceConfig).filter(models.SourceConfig.name == "AlienVault OTX").first()
    if not otx_source:
        db.add(models.SourceConfig(name="AlienVault OTX", source_type="alienvault_otx", enabled=False))

    db.commit()
    db.close()
    print("数据库初始化完成")


if __name__ == "__main__":
    main()