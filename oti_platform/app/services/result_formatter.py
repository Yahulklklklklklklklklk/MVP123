from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

SEVERITY_RANK = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "unknown": 0,
}

SEVERITY_LABEL = {
    "critical": "严重",
    "high": "高危",
    "medium": "中危",
    "low": "低危",
    "unknown": "未知",
}

SOURCE_LABEL = {
    "alienvault_otx": "AlienVault OTX",
    "mock_feed": "Mock Feed",
    "system": "系统",
    "error": "错误",
}


def normalize_severity(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    return text if text in SEVERITY_RANK else "unknown"



def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)



def _normalize_raw(raw_json: Any) -> dict[str, Any]:
    if isinstance(raw_json, dict):
        return raw_json
    if raw_json is None:
        return {}
    return {"value": raw_json}



def _extract_pulse_count(raw_json: dict[str, Any]) -> int | None:
    pulse_info = raw_json.get("pulse_info")
    if isinstance(pulse_info, dict):
        count = pulse_info.get("count")
        if isinstance(count, int):
            return count
        pulses = pulse_info.get("pulses")
        if isinstance(pulses, list):
            return len(pulses)
    return None



def _extract_tags(raw_json: dict[str, Any]) -> list[str]:
    pulse_info = raw_json.get("pulse_info")
    tags: list[str] = []
    if isinstance(pulse_info, dict):
        pulses = pulse_info.get("pulses") or []
        for pulse in pulses:
            if not isinstance(pulse, dict):
                continue
            for tag in pulse.get("tags") or []:
                if isinstance(tag, str) and tag.strip() and tag not in tags:
                    tags.append(tag)
            if len(tags) >= 8:
                break
    verdict = raw_json.get("verdict")
    if isinstance(verdict, str) and verdict not in tags:
        tags.append(verdict)
    return tags[:8]



def build_result_summary(summary: str, raw_json: dict[str, Any]) -> str:
    summary = (summary or "").strip()
    if summary:
        return summary

    pulse_count = _extract_pulse_count(raw_json)
    if pulse_count is not None:
        return f"关联脉冲情报 {pulse_count} 条。"

    reputation = raw_json.get("reputation")
    if reputation is not None:
        return f"信誉值 {reputation}。"

    verdict = raw_json.get("verdict")
    if verdict:
        return f"源返回判定结果：{verdict}。"

    return "未返回可展示的摘要信息。"



def normalize_result_item(item: dict[str, Any], *, cache: bool) -> dict[str, Any]:
    raw_json = _normalize_raw(item.get("raw_json"))
    severity = normalize_severity(item.get("severity"))
    pulse_count = _extract_pulse_count(raw_json)
    tags = _extract_tags(raw_json)
    source_name = str(item.get("source_name") or "unknown")

    normalized = {
        "source_name": source_name,
        "source_label": SOURCE_LABEL.get(source_name, source_name),
        "indicator": item.get("indicator"),
        "indicator_type": item.get("indicator_type"),
        "severity": severity,
        "severity_label": SEVERITY_LABEL[severity],
        "severity_rank": SEVERITY_RANK[severity],
        "summary": build_result_summary(str(item.get("summary") or ""), raw_json),
        "fetched_at": _to_iso(item.get("fetched_at")),
        "expires_at": _to_iso(item.get("expires_at")),
        "pulse_count": pulse_count,
        "tags": tags,
        "cache": cache,
        "cache_label": "缓存命中" if cache else "外部实时查询",
        "raw_json": raw_json,
    }

    if raw_json.get("country_name"):
        normalized["country_name"] = raw_json.get("country_name")
    if raw_json.get("asn"):
        normalized["asn"] = raw_json.get("asn")
    if raw_json.get("city"):
        normalized["city"] = raw_json.get("city")
    if raw_json.get("reputation") is not None:
        normalized["reputation"] = raw_json.get("reputation")

    return normalized



def build_search_response(
    *,
    indicator: str,
    indicator_type: str,
    cache_hit: bool,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized_results = [normalize_result_item(item, cache=cache_hit if item.get("cache") is None else bool(item.get("cache"))) for item in results]
    normalized_results.sort(key=lambda x: (-x["severity_rank"], x["source_name"]))

    highest_severity = normalized_results[0]["severity"] if normalized_results else "unknown"
    counts = Counter(item["severity"] for item in normalized_results)
    source_names = []
    for item in normalized_results:
        if item["source_name"] not in source_names:
            source_names.append(item["source_name"])

    overview = normalized_results[0]["summary"] if normalized_results else "未查询到可用情报。"

    return {
        "indicator": indicator,
        "indicator_type": indicator_type,
        "cache_hit": cache_hit,
        "result_count": len(normalized_results),
        "source_count": len(source_names),
        "highest_severity": highest_severity,
        "highest_severity_label": SEVERITY_LABEL[highest_severity],
        "severity_breakdown": {
            "critical": counts.get("critical", 0),
            "high": counts.get("high", 0),
            "medium": counts.get("medium", 0),
            "low": counts.get("low", 0),
            "unknown": counts.get("unknown", 0),
        },
        "overview": overview,
        "sources": source_names,
        "results": normalized_results,
    }



def build_batch_item(
    *,
    indicator: str,
    indicator_type: str,
    cache_hit: bool,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = build_search_response(
        indicator=indicator,
        indicator_type=indicator_type,
        cache_hit=cache_hit,
        results=results,
    )
    return {
        "indicator": payload["indicator"],
        "indicator_type": payload["indicator_type"],
        "cache_hit": payload["cache_hit"],
        "result_count": payload["result_count"],
        "source_count": payload["source_count"],
        "highest_severity": payload["highest_severity"],
        "highest_severity_label": payload["highest_severity_label"],
        "overview": payload["overview"],
    }
