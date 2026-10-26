from __future__ import annotations

from app.connectors.base import ConnectorError, ConnectorSignal, SourceConnector
from app.connectors.federal_register import FederalRegisterConnector
from app.connectors.gdelt import GDELTConnector

CONNECTOR_REGISTRY: dict[str, SourceConnector] = {
    "gdelt": GDELTConnector(),
    "federal_register": FederalRegisterConnector(),
}


def get_connector(key: str | None) -> SourceConnector | None:
    if not key:
        return None
    return CONNECTOR_REGISTRY.get(key)


def live_connector_keys() -> list[str]:
    return sorted(CONNECTOR_REGISTRY)


__all__ = [
    "CONNECTOR_REGISTRY",
    "ConnectorError",
    "ConnectorSignal",
    "SourceConnector",
    "get_connector",
    "live_connector_keys",
]
