from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Iterable, List, Sequence

from .models import Candle


def parse_timestamp(value: str) -> datetime:
    candidates = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
    )
    for candidate in candidates:
        try:
            return datetime.strptime(value, candidate)
        except ValueError:
            continue
    return datetime.fromisoformat(value)


def sort_candles(candles: Iterable[Candle]) -> List[Candle]:
    return sorted(candles, key=lambda candle: parse_timestamp(candle.timestamp))


def aggregate_candles(candles: Sequence[Candle], bucket_size: int, keep_partial: bool = False) -> List[Candle]:
    ordered = sort_candles(candles)
    grouped: List[Candle] = []
    for start in range(0, len(ordered), bucket_size):
        chunk = ordered[start : start + bucket_size]
        if len(chunk) < bucket_size and not keep_partial:
            break
        grouped.append(_merge_chunk(chunk))
    return grouped


def aggregate_to_4h_from_60m(candles: Sequence[Candle]) -> List[Candle]:
    ordered = sort_candles(candles)
    by_day: defaultdict[str, List[Candle]] = defaultdict(list)
    for candle in ordered:
        by_day[candle.timestamp[:10]].append(candle)

    merged: List[Candle] = []
    for day in sorted(by_day):
        day_candles = sort_candles(by_day[day])
        merged.extend(aggregate_candles(day_candles, bucket_size=4, keep_partial=False))
    return merged


def closing_prices(candles: Sequence[Candle]) -> List[float]:
    return [float(candle.close) for candle in sort_candles(candles)]


def highs(candles: Sequence[Candle]) -> List[float]:
    return [float(candle.high) for candle in sort_candles(candles)]


def lows(candles: Sequence[Candle]) -> List[float]:
    return [float(candle.low) for candle in sort_candles(candles)]


def latest(candles: Sequence[Candle]) -> Candle:
    return sort_candles(candles)[-1]


def _merge_chunk(chunk: Sequence[Candle]) -> Candle:
    first = chunk[0]
    last = chunk[-1]
    return Candle(
        timestamp=last.timestamp,
        open=first.open,
        high=max(candle.high for candle in chunk),
        low=min(candle.low for candle in chunk),
        close=last.close,
        volume=sum(candle.volume for candle in chunk),
        amount=sum(candle.amount for candle in chunk),
        prev_close=first.prev_close,
    )
