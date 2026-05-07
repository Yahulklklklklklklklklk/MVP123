import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from sqlalchemy.orm import Session
from app import models
from .source_manager import build_adapters


def query_local_cache(db: Session, indicator: str):
    now = datetime.utcnow()
    rows = (
        db.query(models.ThreatIntel)
        .filter(models.ThreatIntel.indicator == indicator)
        .filter(models.ThreatIntel.expires_at >= now)
        .all()
    )
    return rows


def save_intel_records(db: Session, records: list[dict]):
    for record in records:
        row = models.ThreatIntel(
            indicator=record["indicator"],
            indicator_type=record["indicator_type"],
            source_name=record["source_name"],
            severity=record.get("severity", "unknown"),
            summary=record.get("summary", ""),
            raw_json=json.dumps(record.get("raw_json", {}), ensure_ascii=False),
            fetched_at=record.get("fetched_at"),
            expires_at=record.get("expires_at"),
        )
        db.add(row)
    db.commit()


def aggregate_external(db: Session, indicator: str, indicator_type: str) -> list[dict]:
    adapters = build_adapters(db)
    results = []

    with ThreadPoolExecutor(max_workers=max(1, len(adapters))) as executor:
        futures = [executor.submit(adapter.query, indicator, indicator_type) for adapter in adapters]
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                results.append({
                    "source_name": "error",
                    "indicator": indicator,
                    "indicator_type": indicator_type,
                    "severity": "unknown",
                    "summary": f"外部源查询失败: {exc}",
                    "raw_json": {"error": str(exc)},
                    "fetched_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow(),
                })

    valid_results = [r for r in results if r.get("source_name") != "error"]
    if valid_results:
        save_intel_records(db, valid_results)
    return results