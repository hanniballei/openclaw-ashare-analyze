from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.models import Candle  # noqa: E402
from common.timeseries import aggregate_to_4h_from_60m  # noqa: E402


class TimeSeriesTest(unittest.TestCase):
    def test_aggregate_to_4h_from_60m(self) -> None:
        candles = [
            Candle(
                timestamp=f"2026-03-21 {hour:02d}:30:00",
                open=10 + index,
                high=10.5 + index,
                low=9.5 + index,
                close=10.2 + index,
                volume=100 + index,
                amount=1000 + index,
            )
            for index, hour in enumerate((9, 10, 11, 13, 9, 10, 11, 13))
        ]
        candles[4].timestamp = "2026-03-22 09:30:00"
        candles[5].timestamp = "2026-03-22 10:30:00"
        candles[6].timestamp = "2026-03-22 11:30:00"
        candles[7].timestamp = "2026-03-22 13:30:00"

        merged = aggregate_to_4h_from_60m(candles)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].open, 10)
        self.assertEqual(merged[0].close, 13.2)
        self.assertEqual(merged[0].volume, 100 + 101 + 102 + 103)


if __name__ == "__main__":
    unittest.main()
