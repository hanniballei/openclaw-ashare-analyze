from __future__ import annotations

from typing import Dict, List, Sequence

from .models import Candle
from .timeseries import latest, sort_candles


def find_price_levels(candles: Sequence[Candle], max_levels: int = 3, min_gap_ratio: float = 0.01) -> Dict[str, List[float]]:
    ordered = sort_candles(candles)
    if not ordered:
        return {"support": [], "resistance": []}

    current_price = latest(ordered).close
    supports = [candle.low for candle in ordered if candle.low < current_price]
    resistances = [candle.high for candle in ordered if candle.high > current_price]

    return {
        "support": _pick_distinct(sorted(supports, reverse=True), max_levels, min_gap_ratio),
        "resistance": _pick_distinct(sorted(resistances), max_levels, min_gap_ratio),
    }


def _pick_distinct(values: Sequence[float], max_levels: int, min_gap_ratio: float) -> List[float]:
    selected: List[float] = []
    for value in values:
        if all(abs(value - existing) / max(abs(existing), 1e-9) >= min_gap_ratio for existing in selected):
            selected.append(value)
        if len(selected) == max_levels:
            break
    return selected
