from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.analysis_engine import _build_us_asset_payload, analyze_market_request, analyze_theme_request  # noqa: E402
from common.models import Candle, InstrumentMatch, ThemeMatch  # noqa: E402


def _sample_candles(length: int = 70) -> list[Candle]:
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


class _RQDataStub:
    def fetch_candles(self, symbol: str, frequency: str, count: int = 90):
        return _sample_candles()

    def fetch_northbound_flow(self):
        return {"today_net": 12.3, "source": "rqdata"}


class _ThemeRQDataStub:
    def resolve_theme(self, query: str):
        return ThemeMatch(query="光纤", name="光纤概念", source="concept")

    def list_theme_components(self, theme_match: ThemeMatch, limit: int = 20):
        return [
            InstrumentMatch(symbol="600487.XSHG", name="亨通光电", instrument_type="CS"),
            InstrumentMatch(symbol="000063.XSHE", name="中兴通讯", instrument_type="CS"),
        ][:limit]

    def fetch_candles(self, symbol: str, frequency: str, count: int = 90):
        return _sample_candles()

    def fetch_money_flow(self, symbol: str, lookback_days: int = 5):
        flows = {
            "600487.XSHG": {"today_net": 20.0, "5day_net": 50.0, "source": "rqdata"},
            "000063.XSHE": {"today_net": -5.0, "5day_net": 10.0, "source": "rqdata"},
        }
        return flows[symbol]


class _YFinanceStub:
    def fetch_candles(self, symbol: str, interval: str, count: int = 90):
        return _sample_candles()

    def fetch_basics(self, symbol: str):
        return {
            "pe_ttm": 1.0,
            "pb": 2.0,
            "market_cap": 3.0,
            "roe_ttm": 4.0,
            "revenue_growth": 5.0,
            "profit_growth": 6.0,
        }


class AnalysisEngineContractsTest(unittest.TestCase):
    def test_market_overview_omits_removed_fields(self) -> None:
        import common.analysis_engine as analysis_engine

        rqdata_patch = patch.object(analysis_engine, "RQDataClient", return_value=_RQDataStub())
        with rqdata_patch:
            payload = analyze_market_request("今天A股走势如何", bars=30)

        self.assertNotIn("market_breadth", payload)
        self.assertNotIn("sector_performance", payload)
        self.assertEqual(payload["northbound_flow"], {"today_net": 12.3, "source": "rqdata"})

    def test_us_payload_omits_cn_only_enrichment_fields(self) -> None:
        instrument = InstrumentMatch(symbol="NVDA", name="NVDA", instrument_type="US_STOCK", market="US")

        payload = _build_us_asset_payload(instrument, _YFinanceStub(), bars=30)

        self.assertNotIn("money_flow", payload)
        self.assertNotIn("billboard", payload)

    def test_theme_payload_contains_representative_stocks_and_summary(self) -> None:
        import common.analysis_engine as analysis_engine

        rqdata_patch = patch.object(analysis_engine, "RQDataClient", return_value=_ThemeRQDataStub())
        with rqdata_patch:
            payload = analyze_theme_request("怎么看光纤板块？", bars=30, top=2)

        self.assertEqual(payload["scenario"], "THEME_ANALYZE")
        self.assertEqual(payload["theme"], "光纤")
        self.assertEqual(payload["resolved_theme"], "光纤概念")
        self.assertEqual(payload["theme_source"], "concept")
        self.assertEqual(len(payload["representative_stocks"]), 2)
        self.assertIn("indicators", payload["representative_stocks"][0])
        self.assertIn("money_flow", payload["representative_stocks"][0])
        self.assertEqual(payload["theme_summary"]["up_count"], 2)
        self.assertEqual(payload["theme_summary"]["down_count"], 0)
        self.assertEqual(payload["theme_summary"]["total_net_flow"], 15.0)


if __name__ == "__main__":
    unittest.main()
