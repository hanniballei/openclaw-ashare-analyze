from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.rqdata_client import RQDataClient  # noqa: E402
from common.models import ThemeMatch  # noqa: E402


class _RQDataModuleStub:
    def get_capital_flow(self, order_book_ids, start_date=None, end_date=None, frequency="1d", market="cn"):
        return [
            {"order_book_id": "600875.XSHG", "date": "2026-03-20", "buy_volume": 1.0, "buy_value": 100.0, "sell_volume": 1.0, "sell_value": 60.0},
            {"order_book_id": "600875.XSHG", "date": "2026-03-21", "buy_volume": 1.0, "buy_value": 130.0, "sell_volume": 1.0, "sell_value": 90.0},
            {"order_book_id": "600875.XSHG", "date": "2026-03-22", "buy_volume": 1.0, "buy_value": 80.0, "sell_volume": 1.0, "sell_value": 70.0},
        ]

    def get_abnormal_stocks_detail(self, order_book_ids, start_date=None, end_date=None, sides=None, types=None, market="cn"):
        return [
            {
                "order_book_id": "600875.XSHG",
                "date": "2026-03-22",
                "side": "buy",
                "rank": 1,
                "agency": "沪股通专用",
                "buy_value": 123456.0,
                "sell_value": None,
                "type": "U02",
                "reason": "连续三个交易日内，涨幅偏离值累计达20%",
            },
            {
                "order_book_id": "600875.XSHG",
                "date": "2026-03-22",
                "side": "sell",
                "rank": 2,
                "agency": "机构专用",
                "buy_value": None,
                "sell_value": 654321.0,
                "type": "U02",
                "reason": "连续三个交易日内，涨幅偏离值累计达20%",
            },
        ]

    def current_stock_connect_quota(self, connect=None, fields=None):
        return [
            {
                "datetime": "2026-04-07 15:01:00",
                "connect": "hk_to_sh",
                "buy_turnover": 100.0,
                "sell_turnover": 70.0,
                "quota_balance": 1.0,
                "quota_balance_ratio": 0.1,
            },
            {
                "datetime": "2026-04-07 15:01:00",
                "connect": "hk_to_sz",
                "buy_turnover": 80.0,
                "sell_turnover": 40.0,
                "quota_balance": 1.0,
                "quota_balance_ratio": 0.1,
            },
            {
                "datetime": "2026-03-23 16:10:00",
                "connect": "sh_to_hk",
                "buy_turnover": 999.0,
                "sell_turnover": 1.0,
                "quota_balance": 1.0,
                "quota_balance_ratio": 0.1,
            },
        ]


class _StaleNorthboundRQDataModuleStub(_RQDataModuleStub):
    def current_stock_connect_quota(self, connect=None, fields=None):
        return [
            {
                "datetime": "2024-05-10 15:01:00",
                "connect": "hk_to_sh",
                "buy_turnover": 100.0,
                "sell_turnover": 70.0,
            },
            {
                "datetime": "2024-05-10 15:01:00",
                "connect": "hk_to_sz",
                "buy_turnover": 80.0,
                "sell_turnover": 40.0,
            },
        ]

    def get_stock_connect_quota(self, connect=None, start_date=None, end_date=None):
        return []


class _ThemeRQDataModuleStub:
    _NAMES = {
        "600487.XSHG": "亨通光电",
        "000063.XSHE": "中兴通讯",
        "600118.XSHG": "中国卫星",
    }

    def get_concept_list(self, start_date=None, end_date=None, market="cn"):
        return ["光纤概念", "卫星互联网", "算力概念", "航空"]

    def get_concept(self, concepts, start_date=None, end_date=None, market="cn"):
        mapping = {
            "光纤概念": ["600487.XSHG", "000063.XSHE"],
            "卫星互联网": ["600118.XSHG", "000063.XSHE"],
            "航空": ["600118.XSHG", "000063.XSHE"],
        }
        symbols = mapping[concepts]
        return [{"concept": concepts, "order_book_id": symbol} for symbol in symbols]

    def get_industry_mapping(self, source="citics_2019", date=None, market="cn"):
        return [
            {
                "first_industry_code": "10",
                "first_industry_name": "通信",
                "second_industry_code": "1010",
                "second_industry_name": "通信设备",
                "third_industry_code": "101001",
                "third_industry_name": "光通信设备",
            }
        ]

    def instruments(self, symbol):
        name = self._NAMES[symbol]
        return type("Instrument", (), {"symbol": name, "display_name": name})()


class RQDataClientTest(unittest.TestCase):
    def test_fetch_money_flow_uses_latest_and_rolling_net(self) -> None:
        client = RQDataClient()
        client._module = _RQDataModuleStub()

        result = client.fetch_money_flow("600875.XSHG")

        self.assertEqual(
            result,
            {
                "today_net": 10.0,
                "5day_net": 90.0,
                "latest_timestamp": "2026-03-22",
                "source": "rqdata",
            },
        )

    def test_fetch_billboard_maps_abnormal_detail_rows(self) -> None:
        client = RQDataClient()
        client._module = _RQDataModuleStub()

        result = client.fetch_billboard("600875.XSHG")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["date"], "2026-03-22")
        self.assertEqual(result[0]["type"], "连续三个交易日内，涨幅偏离值累计达20%")
        self.assertEqual(result[0]["amount"], 123456.0)
        self.assertEqual(result[0]["trader"], "沪股通专用")
        self.assertEqual(result[1]["amount"], 654321.0)

    def test_fetch_northbound_flow_sums_hk_to_sh_and_hk_to_sz(self) -> None:
        client = RQDataClient()
        client._module = _RQDataModuleStub()

        result = client.fetch_northbound_flow()

        self.assertEqual(result, {"today_net": 70.0, "latest_timestamp": "2026-04-07 15:01:00", "source": "rqdata"})

    def test_fetch_northbound_flow_discards_stale_snapshots(self) -> None:
        client = RQDataClient()
        client._module = _StaleNorthboundRQDataModuleStub()

        result = client.fetch_northbound_flow()

        self.assertEqual(result, {"today_net": None, "latest_timestamp": None, "source": "rqdata"})

    def test_resolve_theme_matches_concept_and_alias_keywords(self) -> None:
        client = RQDataClient()
        client._module = _ThemeRQDataModuleStub()

        direct_match = client.resolve_theme("怎么看光纤板块？")
        self.assertEqual(direct_match, ThemeMatch(query="光纤", name="光纤概念", source="concept"))

        alias_match = client.resolve_theme("A股中卫星通信的公司有哪些头部企业？")
        self.assertEqual(alias_match, ThemeMatch(query="卫星通信", name="卫星互联网", source="concept"))

        ranked_match = client.resolve_theme("推荐光纤板块 5 只优质股票")
        self.assertEqual(ranked_match, ThemeMatch(query="光纤", name="光纤概念", source="concept"))

        domain_match = client.resolve_theme("推荐航天航空领域的股票")
        self.assertEqual(domain_match, ThemeMatch(query="航天航空", name="航空", source="concept"))

        typo_match = client.resolve_theme("分析航空航天版块走势")
        self.assertEqual(typo_match, ThemeMatch(query="航空航天", name="航空", source="concept"))

    def test_list_theme_components_returns_named_instruments(self) -> None:
        client = RQDataClient()
        client._module = _ThemeRQDataModuleStub()

        components = client.list_theme_components(
            ThemeMatch(query="光纤", name="光纤概念", source="concept"),
            limit=2,
        )

        self.assertEqual([component.symbol for component in components], ["600487.XSHG", "000063.XSHE"])
        self.assertEqual([component.name for component in components], ["亨通光电", "中兴通讯"])


if __name__ == "__main__":
    unittest.main()
