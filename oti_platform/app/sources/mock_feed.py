from datetime import datetime, timedelta
from .base import BaseSourceAdapter


class MockFeedAdapter(BaseSourceAdapter):
    def query(self, indicator: str, indicator_type: str) -> dict:
        suspicious = indicator.endswith("8") or indicator.endswith("9") or "mal" in indicator.lower()
        severity = "high" if suspicious else "low"
        summary = (
            f"MockFeed 判断 {indicator} 存在较高可疑性"
            if suspicious else
            f"MockFeed 未发现 {indicator} 的明显恶意证据"
        )
        return {
            "source_name": "mock_feed",
            "indicator": indicator,
            "indicator_type": indicator_type,
            "severity": severity,
            "summary": summary,
            "raw_json": {
                "mock": True,
                "indicator": indicator,
                "indicator_type": indicator_type,
                "verdict": severity,
            },
            "fetched_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
        }