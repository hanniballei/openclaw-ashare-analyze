from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any


def round_recursive(value: Any, digits: int = 4) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "isoformat") and callable(value.isoformat):
        try:
            return value.isoformat()
        except TypeError:
            pass
    if isinstance(value, float):
        return round(value, digits)
    if isinstance(value, list):
        return [round_recursive(item, digits) for item in value]
    if isinstance(value, dict):
        return {key: round_recursive(item, digits) for key, item in value.items()}
    return value


def to_json(payload: Any, pretty: bool = True) -> str:
    prepared = round_recursive(payload)
    if pretty:
        return json.dumps(prepared, ensure_ascii=False, indent=2, sort_keys=False)
    return json.dumps(prepared, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def change_pct(current: float, previous: float | None) -> float | None:
    if previous in (None, 0):
        return None
    return (float(current) - float(previous)) / float(previous) * 100
