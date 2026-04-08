from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.analysis_engine import (
    _build_cn_asset_payload,
    _build_us_asset_payload,
    analyze_market_request,
    analyze_theme_request,
)  # noqa: E402
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


def _sample_intraday_candles(frequency: str, days: int = 20) -> list[Candle]:
    candles: list[Candle] = []
    close = 10.0
    if frequency == "1d":
        for day in range(1, days + 1):
            close += 0.2
            candles.append(
                Candle(
                    timestamp=f"2026-03-{day:02d}",
                    open=close - 0.1,
                    high=close + 0.2,
                    low=close - 0.3,
                    close=close,
                    volume=1000 + day * 10,
                    amount=10000 + day * 100,
                    prev_close=close - 0.15,
                )
            )
        return candles

    for day in range(1, days + 1):
        slots = ("09:35:00", "09:40:00", "09:45:00", "09:50:00") if frequency == "5m" else ("09:30:00", "10:30:00", "11:30:00", "13:30:00")
        for slot in slots:
            close += 0.2
            candles.append(
                Candle(
                    timestamp=f"2026-03-{day:02d} {slot}",
                    open=close - 0.1,
                    high=close + 0.2,
                    low=close - 0.3,
                    close=close,
                    volume=1000 + len(candles) * 10,
                    amount=10000 + len(candles) * 100,
                    prev_close=close - 0.15,
                )
            )
    return candles


class _RQDataStub:
    def fetch_candles(self, symbol: str, frequency: str, count: int = 90):
        return _sample_intraday_candles(frequency)

    def fetch_northbound_flow(self):
        return {"today_net": 12.3, "latest_timestamp": "2026-03-20 15:01:00", "source": "rqdata"}

    def fetch_fundamentals(self, symbol: str):
        return {
            "pe_ttm": 10.0,
            "pb": 2.0,
            "market_cap": 100.0,
            "roe_ttm": 0.1,
            "revenue_growth": 0.2,
            "profit_growth": 0.3,
        }

    def fetch_money_flow(self, symbol: str, lookback_days: int = 5):
        return {"today_net": 8.0, "5day_net": 30.0, "latest_timestamp": "2026-03-20", "source": "rqdata"}

    def fetch_billboard(self, symbol: str, limit: int = 5):
        return []


class _ThemeRQDataStub:
    def resolve_theme(self, query: str):
        return ThemeMatch(query="光纤", name="光纤概念", source="concept")

    def list_theme_components(self, theme_match: ThemeMatch, limit: int = 20):
        return [
            InstrumentMatch(symbol="600487.XSHG", name="亨通光电", instrument_type="CS"),
            InstrumentMatch(symbol="000063.XSHE", name="中兴通讯", instrument_type="CS"),
            InstrumentMatch(symbol="600118.XSHG", name="中国卫星", instrument_type="CS"),
        ][:limit]

    def fetch_candles(self, symbol: str, frequency: str, count: int = 90):
        return _sample_intraday_candles(frequency)

    def fetch_money_flow(self, symbol: str, lookback_days: int = 5):
        flows = {
            "600487.XSHG": {"today_net": 20.0, "5day_net": 50.0, "latest_timestamp": "2026-03-20", "source": "rqdata"},
            "000063.XSHE": {"today_net": -5.0, "5day_net": 10.0, "latest_timestamp": "2026-03-20", "source": "rqdata"},
            "600118.XSHG": {"today_net": 1.0, "5day_net": 5.0, "latest_timestamp": "2026-03-20", "source": "rqdata"},
        }
        return flows[symbol]

    def fetch_fundamentals(self, symbol: str):
        fundamentals = {
            "600487.XSHG": {
                "pe_ttm": 10.0,
                "pb": 2.0,
                "market_cap": 100.0,
                "roe_ttm": 0.1,
                "revenue_growth": 0.2,
                "profit_growth": 0.3,
            },
            "000063.XSHE": {
                "pe_ttm": 12.0,
                "pb": 1.8,
                "market_cap": 90.0,
                "roe_ttm": 0.08,
                "revenue_growth": 0.05,
                "profit_growth": -0.1,
            },
            "600118.XSHG": {
                "pe_ttm": 15.0,
                "pb": 2.4,
                "market_cap": 120.0,
                "roe_ttm": 0.09,
                "revenue_growth": 0.02,
                "profit_growth": 0.01,
            },
        }
        return fundamentals[symbol]


class _YFinanceStub:
    def fetch_candles(self, symbol: str, interval: str, count: int = 90):
        mapping = {"1d": "1d", "60m": "60m", "5m": "5m"}
        return _sample_intraday_candles(mapping[interval])

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
    def test_cn_asset_payload_exposes_per_timeframe_latest_timestamps(self) -> None:
        payload = _build_cn_asset_payload(
            "STOCK_ANALYZE",
            InstrumentMatch(symbol="600875.XSHG", name="东方电气", instrument_type="CS"),
            _RQDataStub(),
            bars=30,
        )

        self.assertEqual(payload["timestamp"], "2026-03-20")
        self.assertEqual(payload["indicators"]["daily"]["latest_timestamp"], "2026-03-20")
        self.assertEqual(payload["indicators"]["4h"]["latest_timestamp"], "2026-03-20 13:30:00")
        self.assertEqual(payload["indicators"]["1h"]["latest_timestamp"], "2026-03-20 13:30:00")
        self.assertEqual(payload["indicators"]["5min"]["latest_timestamp"], "2026-03-20 09:50:00")
        self.assertEqual(payload["money_flow"]["latest_timestamp"], "2026-03-20")
        self.assertEqual(payload["candles"]["daily"]["bar_count"], 20)
        self.assertEqual(payload["candles"]["daily"]["start_timestamp"], "2026-03-01")
        self.assertEqual(payload["candles"]["daily"]["latest_timestamp"], "2026-03-20")
        self.assertEqual(len(payload["candles"]["daily"]["bars"]), 20)
        self.assertEqual(payload["candles"]["1h"]["bar_count"], 60)
        self.assertEqual(payload["candles"]["1h"]["start_timestamp"], "2026-03-06 09:30:00")
        self.assertEqual(payload["candles"]["1h"]["latest_timestamp"], "2026-03-20 13:30:00")
        self.assertEqual(len(payload["candles"]["1h"]["bars"]), 60)
        self.assertEqual(payload["candles"]["5min"]["bar_count"], 60)
        self.assertEqual(payload["candles"]["5min"]["start_timestamp"], "2026-03-06 09:35:00")
        self.assertEqual(payload["candles"]["5min"]["latest_timestamp"], "2026-03-20 09:50:00")
        self.assertEqual(len(payload["candles"]["5min"]["bars"]), 60)
        self.assertEqual(
            set(payload["candles"]["5min"]["bars"][0].keys()),
            {"timestamp", "open", "high", "low", "close", "volume", "amount", "prev_close"},
        )

    def test_market_overview_omits_removed_fields(self) -> None:
        import common.analysis_engine as analysis_engine

        rqdata_patch = patch.object(analysis_engine, "RQDataClient", return_value=_RQDataStub())
        with rqdata_patch:
            payload = analyze_market_request("今天A股走势如何", bars=30)

        self.assertNotIn("market_breadth", payload)
        self.assertNotIn("sector_performance", payload)
        self.assertEqual(
            payload["northbound_flow"],
            {"today_net": 12.3, "latest_timestamp": "2026-03-20 15:01:00", "source": "rqdata"},
        )
        self.assertEqual(
            set(payload["indices"]["shanghai"]["indicators"].keys()),
            {"daily", "1h", "5min"},
        )
        self.assertNotIn("4h", payload["indices"]["shanghai"]["indicators"])
        self.assertEqual(payload["indices"]["shanghai"]["indicators"]["daily"]["latest_timestamp"], "2026-03-20")
        self.assertEqual(payload["indices"]["shanghai"]["indicators"]["1h"]["latest_timestamp"], "2026-03-20 13:30:00")
        self.assertEqual(payload["indices"]["shanghai"]["indicators"]["5min"]["latest_timestamp"], "2026-03-20 09:50:00")
        self.assertEqual(payload["indices"]["shanghai"]["candles"]["daily"]["bar_count"], 20)
        self.assertEqual(payload["indices"]["shanghai"]["candles"]["1h"]["bar_count"], 60)
        self.assertEqual(payload["indices"]["shanghai"]["candles"]["5min"]["bar_count"], 60)

    def test_us_payload_omits_cn_only_enrichment_fields(self) -> None:
        instrument = InstrumentMatch(symbol="NVDA", name="NVDA", instrument_type="US_STOCK", market="US")

        payload = _build_us_asset_payload(instrument, _YFinanceStub(), bars=30)

        self.assertNotIn("money_flow", payload)
        self.assertNotIn("billboard", payload)
        self.assertEqual(payload["indicators"]["daily"]["latest_timestamp"], "2026-03-20")
        self.assertEqual(set(payload["indicators"].keys()), {"daily"})
        self.assertEqual(payload["candles"]["daily"]["bar_count"], 20)
        self.assertEqual(set(payload["candles"].keys()), {"daily"})
        self.assertIn("daily_summary", payload)
        self.assertIn("return_5d", payload["daily_summary"])
        self.assertIn("position_in_30d_range", payload["daily_summary"])

    def test_etf_payload_omits_billboard(self) -> None:
        payload = _build_cn_asset_payload(
            "ETF_ANALYZE",
            InstrumentMatch(symbol="159206.XSHE", name="国证芯片ETF", instrument_type="ETF"),
            _RQDataStub(),
            bars=30,
            include_fundamentals=False,
            include_billboard=False,
        )

        self.assertNotIn("billboard", payload)

    def test_theme_payload_contains_representative_stocks_and_summary(self) -> None:
        import common.analysis_engine as analysis_engine

        rqdata_patch = patch.object(analysis_engine, "RQDataClient", return_value=_ThemeRQDataStub())
        with rqdata_patch:
            payload = analyze_theme_request("怎么看光纤板块？", bars=30, top=3)

        self.assertEqual(payload["scenario"], "THEME_ANALYZE")
        self.assertEqual(payload["theme"], "光纤")
        self.assertEqual(payload["resolved_theme"], "光纤概念")
        self.assertEqual(payload["theme_source"], "concept")
        self.assertIn("selection_basis", payload)
        self.assertEqual(payload["selection_basis"]["top"], 3)
        self.assertEqual(payload["selection_basis"]["representative_limit"], 2)
        self.assertIn("ranking", payload)
        self.assertEqual(len(payload["ranking"]), 3)
        self.assertEqual(payload["ranking"][0]["rank"], 1)
        self.assertIn("score", payload["ranking"][0])
        self.assertIn("reasons", payload["ranking"][0])
        self.assertEqual(len(payload["representative_stocks"]), 2)
        self.assertIn("indicators", payload["representative_stocks"][0])
        self.assertEqual(set(payload["representative_stocks"][0]["indicators"].keys()), {"daily", "1h", "5min"})
        self.assertIn("candles", payload["representative_stocks"][0])
        self.assertEqual(set(payload["representative_stocks"][0]["candles"].keys()), {"daily", "1h", "5min"})
        self.assertEqual(payload["representative_stocks"][0]["candles"]["daily"]["bar_count"], 20)
        self.assertEqual(payload["representative_stocks"][0]["candles"]["1h"]["bar_count"], 60)
        self.assertEqual(payload["representative_stocks"][0]["candles"]["5min"]["bar_count"], 60)
        self.assertIn("money_flow", payload["representative_stocks"][0])
        self.assertEqual(payload["representative_stocks"][0]["symbol"], payload["ranking"][0]["symbol"])
        self.assertEqual(payload["representative_stocks"][0]["indicators"]["daily"]["latest_timestamp"], "2026-03-20")
        self.assertEqual(payload["representative_stocks"][0]["indicators"]["1h"]["latest_timestamp"], "2026-03-20 13:30:00")
        self.assertEqual(payload["representative_stocks"][0]["indicators"]["5min"]["latest_timestamp"], "2026-03-20 09:50:00")
        self.assertEqual(payload["representative_stocks"][0]["money_flow"]["latest_timestamp"], "2026-03-20")
        self.assertEqual(payload["theme_summary"]["up_count"], 3)
        self.assertEqual(payload["theme_summary"]["down_count"], 0)
        self.assertEqual(payload["theme_summary"]["total_net_flow"], 16.0)


if __name__ == "__main__":
    unittest.main()
