from datetime import datetime, timedelta
import requests
from .base import BaseSourceAdapter


class AlienVaultOTXAdapter(BaseSourceAdapter):
    def query(self, indicator: str, indicator_type: str) -> dict:
        api_key = self.config.api_key if self.config else None
        headers = {"X-OTX-API-KEY": api_key} if api_key else {}

        section_map = {
            "ip": "IPv4",
            "domain": "domain",
            "md5": "file",
            "sha1": "file",
            "sha256": "file",
        }
        otx_type = section_map.get(indicator_type)
        if not otx_type:
            raise ValueError(f"Unsupported indicator type for OTX: {indicator_type}")

        if otx_type == "file":
            url = f"https://otx.alienvault.com/api/v1/indicators/file/{indicator}/general"
        else:
            url = f"https://otx.alienvault.com/api/v1/indicators/{otx_type}/{indicator}/general"

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        pulse_info = data.get("pulse_info", {})
        pulses = pulse_info.get("pulses", [])
        pulse_count = len(pulses)

        severity = "high" if pulse_count >= 5 else "medium" if pulse_count >= 1 else "low"
        summary = f"OTX 返回 {pulse_count} 条相关脉冲情报"

        # 只保留关键字段，避免整包 JSON 过大
        filtered_data = {
            "indicator": indicator,
            "indicator_type": indicator_type,
            "reputation": data.get("reputation"),
            "asn": data.get("asn"),
            "country_name": data.get("country_name"),
            "city": data.get("city"),
            "pulse_info": {
                "count": pulse_info.get("count"),
                "pulses": [
                    {
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "created": p.get("created"),
                        "modified": p.get("modified"),
                        "tags": p.get("tags", [])[:10],
                        "references": p.get("references", [])[:5],
                    }
                    for p in pulses[:10]
                ],
            },
        }

        return {
            "source_name": "alienvault_otx",
            "indicator": indicator,
            "indicator_type": indicator_type,
            "severity": severity,
            "summary": summary,
            "raw_json": filtered_data,
            "fetched_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=12),
        }