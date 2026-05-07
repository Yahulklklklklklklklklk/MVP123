import json
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import models
from app.auth import get_current_user
from app.database import get_db
from app.schemas import BatchSearchRequest, SearchRequest
from app.services.indicator import detect_indicator_type
from app.services.intel_service import aggregate_external, query_local_cache
from app.utils import add_audit_log

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search")
def api_search(
    payload: SearchRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return {"error": "unauthorized"}

    indicator = payload.indicator.strip()
    indicator_type = detect_indicator_type(indicator)

    rows = query_local_cache(db, indicator)
    cache_hit = len(rows) > 0

    if cache_hit:
        results = [
            {
                "source_name": r.source_name,
                "severity": r.severity,
                "summary": r.summary,
                "indicator": r.indicator,
                "indicator_type": r.indicator_type,
                "fetched_at": r.fetched_at.isoformat() if r.fetched_at else None,
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "raw_json": json.loads(r.raw_json or "{}"),
                "cache": True,
            }
            for r in rows
        ]
    else:
        external = aggregate_external(db, indicator, indicator_type)
        results = []
        for r in external:
            item = dict(r)
            item["cache"] = False
            if hasattr(item.get("fetched_at"), "isoformat"):
                item["fetched_at"] = item["fetched_at"].isoformat()
            if hasattr(item.get("expires_at"), "isoformat"):
                item["expires_at"] = item["expires_at"].isoformat()
            results.append(item)

    history = models.QueryHistory(
        user_id=user.id,
        query_text=indicator,
        query_type=indicator_type,
        result_count=len(results),
    )
    db.add(history)
    db.commit()

    add_audit_log(db, user.id, "search", f"查询 {indicator}，命中 {len(results)} 条")

    return {
        "indicator": indicator,
        "indicator_type": indicator_type,
        "cache_hit": cache_hit,
        "results": results,
    }


@router.post("/batch-search")
def api_batch_search(
    payload: BatchSearchRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return {"error": "unauthorized"}

    output = []
    for item in payload.indicators:
        item = item.strip()
        if not item:
            continue

        indicator_type = detect_indicator_type(item)
        rows = query_local_cache(db, item)

        if rows:
            result_count = len(rows)
            cache_hit = True
        else:
            ext = aggregate_external(db, item, indicator_type)
            result_count = len(ext)
            cache_hit = False

        history = models.QueryHistory(
            user_id=user.id,
            query_text=item,
            query_type=indicator_type,
            result_count=result_count,
        )
        db.add(history)

        output.append(
            {
                "indicator": item,
                "indicator_type": indicator_type,
                "result_count": result_count,
                "cache_hit": cache_hit,
            }
        )

    db.commit()
    add_audit_log(db, user.id, "batch_search", f"批量查询 {len(output)} 个指标")

    return {"items": output}