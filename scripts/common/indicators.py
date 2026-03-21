from __future__ import annotations

import statistics
from typing import Dict, Optional, Sequence

from .models import Candle
from .timeseries import closing_prices, highs, lows, sort_candles


def moving_average(values: Sequence[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    window = values[-period:]
    return sum(window) / period


def exponential_moving_average(values: Sequence[float], period: int) -> Optional[float]:
    if not values:
        return None
    multiplier = 2 / (period + 1)
    ema = float(values[0])
    for value in values[1:]:
        ema = (float(value) - ema) * multiplier + ema
    return ema


def macd(values: Sequence[float]) -> Dict[str, Optional[float]]:
    if not values:
        return {"dif": None, "dea": None, "histogram": None}

    short_multiplier = 2 / (12 + 1)
    long_multiplier = 2 / (26 + 1)
    signal_multiplier = 2 / (9 + 1)

    ema_short = float(values[0])
    ema_long = float(values[0])
    dea = 0.0

    for value in values[1:]:
        value = float(value)
        ema_short = (value - ema_short) * short_multiplier + ema_short
        ema_long = (value - ema_long) * long_multiplier + ema_long
        dif = ema_short - ema_long
        dea = (dif - dea) * signal_multiplier + dea

    dif = ema_short - ema_long
    histogram = (dif - dea) * 2
    return {
        "dif": dif,
        "dea": dea,
        "histogram": histogram,
    }


def kdj(candles: Sequence[Candle], period: int = 9) -> Dict[str, Optional[float]]:
    ordered = sort_candles(candles)
    if not ordered:
        return {"k": None, "d": None, "j": None}

    k_value = 50.0
    d_value = 50.0
    for index in range(len(ordered)):
        window = ordered[max(0, index - period + 1) : index + 1]
        highest = max(item.high for item in window)
        lowest = min(item.low for item in window)
        close = ordered[index].close
        if highest == lowest:
            rsv = 50.0
        else:
            rsv = (close - lowest) / (highest - lowest) * 100
        k_value = (2 * k_value + rsv) / 3
        d_value = (2 * d_value + k_value) / 3

    j_value = 3 * k_value - 2 * d_value
    return {"k": k_value, "d": d_value, "j": j_value}


def rsi(values: Sequence[float], period: int) -> Optional[float]:
    if len(values) <= period:
        return None

    gains = []
    losses = []
    for left, right in zip(values[:-1], values[1:]):
        delta = float(right) - float(left)
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for gain, loss in zip(gains[period:], losses[period:]):
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def bollinger(values: Sequence[float], period: int = 20, width: float = 2.0) -> Dict[str, Optional[float]]:
    if len(values) < period:
        return {"upper": None, "middle": None, "lower": None}

    window = [float(value) for value in values[-period:]]
    middle = sum(window) / period
    stdev = statistics.pstdev(window)
    return {
        "upper": middle + width * stdev,
        "middle": middle,
        "lower": middle - width * stdev,
    }


def compute_indicator_snapshot(candles: Sequence[Candle]) -> Dict[str, Dict[str, Optional[float]]]:
    closes = closing_prices(candles)
    return {
        "ma": {
            "ma5": moving_average(closes, 5),
            "ma10": moving_average(closes, 10),
            "ma20": moving_average(closes, 20),
            "ma60": moving_average(closes, 60),
        },
        "macd": macd(closes),
        "kdj": kdj(candles),
        "rsi": {
            "rsi6": rsi(closes, 6),
            "rsi12": rsi(closes, 12),
            "rsi24": rsi(closes, 24),
        },
        "bollinger": bollinger(closes, 20, 2.0),
    }
