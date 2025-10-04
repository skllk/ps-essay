from __future__ import annotations

from typing import Dict
from uuid import UUID, uuid4


class InMemoryStore:
    def __init__(self) -> None:
        self._store: Dict[UUID, Dict[str, object]] = {}

    def save(self, payload: Dict[str, object]) -> UUID:
        record_id = uuid4()
        self._store[record_id] = payload
        return record_id

    def get(self, record_id: UUID) -> Dict[str, object] | None:
        return self._store.get(record_id)


def get_store() -> InMemoryStore:
    if not hasattr(get_store, "_instance"):
        get_store._instance = InMemoryStore()  # type: ignore[attr-defined]
    return get_store._instance  # type: ignore[attr-defined]
