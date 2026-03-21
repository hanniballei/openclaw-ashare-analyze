from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.models import Candle  # noqa: E402
from common.price_levels import find_price_levels  # noqa: E402


class PriceLevelsTest(unittest.TestCase):
    def test_find_price_levels(self) -> None:
        candles = [
            Candle(
                timestamp=f"2026-03-{index + 1:02d}",
                open=10 + index * 0.1,
                high=10.8 + index * 0.1,
                low=9.2 + index * 0.1,
                close=10.0 + index * 0.1,
                volume=1000,
                amount=10000,
            )
            for index in range(20)
        ]
        levels = find_price_levels(candles)
        self.assertTrue(levels["support"])
        self.assertTrue(levels["resistance"])
        self.assertLess(levels["support"][0], candles[-1].close)
        self.assertGreater(levels["resistance"][0], candles[-1].close)


if __name__ == "__main__":
    unittest.main()
