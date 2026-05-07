from . import models


def add_audit_log(db, user_id, action, detail=""):
    log = models.AuditLog(user_id=user_id, action=action, detail=detail)
    db.add(log)
    db.commit()