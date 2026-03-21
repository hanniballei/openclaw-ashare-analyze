from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.indicators import compute_indicator_snapshot, macd, moving_average, rsi  # noqa: E402
from common.models import Candle  # noqa: E402


def sample_candles(length: int = 70) -> list[Candle]:
    candles = []
    for index in range(length):
        close = 10 + index * 0.2
        candles.append(
            Candle(
                timestamp=f"2026-03-{(index % 28) + 1:02d}",
                open=close - 0.1,
                high=close + 0.2,
                low=close - 0.3,
                close=close,
                volume=1000 + index * 10,
                amount=10000 + index * 100,
                prev_close=close - 0.15,
            )
        )
    return candles


class IndicatorTest(unittest.TestCase):
    def test_moving_average(self) -> None:
        self.assertAlmostEqual(moving_average([1, 2, 3, 4, 5], 5), 3.0)

    def test_macd_returns_values(self) -> None:
        snapshot = macd([1 + index * 0.1 for index in range(30)])
        self.assertIsNotNone(snapshot["dif"])
        self.assertIsNotNone(snapshot["dea"])
        self.assertIsNotNone(snapshot["histogram"])

    def test_rsi_returns_in_range(self) -> None:
        value = rsi([1 + index * 0.2 for index in range(40)], 6)
        self.assertIsNotNone(value)
        assert value is not None
        self.assertGreaterEqual(value, 0)
        self.assertLessEqual(value, 100)

    def test_snapshot_shape(self) -> None:
        snapshot = compute_indicator_snapshot(sample_candles())
        self.assertIn("ma", snapshot)
        self.assertIn("macd", snapshot)
        self.assertIn("kdj", snapshot)
        self.assertIn("rsi", snapshot)
        self.assertIn("bollinger", snapshot)
        self.assertIsNotNone(snapshot["ma"]["ma20"])


if __name__ == "__main__":
    unittest.main()
