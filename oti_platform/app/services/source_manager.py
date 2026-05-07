from sqlalchemy.orm import Session
from app import models
from app.sources.mock_feed import MockFeedAdapter
from app.sources.alienvault_otx import AlienVaultOTXAdapter


ADAPTER_REGISTRY = {
    "mock_feed": MockFeedAdapter,
    "alienvault_otx": AlienVaultOTXAdapter,
}


def get_enabled_sources(db: Session):
    return db.query(models.SourceConfig).filter(models.SourceConfig.enabled == True).all()


def build_adapters(db: Session):
    configs = get_enabled_sources(db)
    adapters = []
    for cfg in configs:
        adapter_cls = ADAPTER_REGISTRY.get(cfg.source_type)
        if adapter_cls:
            adapters.append(adapter_cls(cfg))
    return adapters