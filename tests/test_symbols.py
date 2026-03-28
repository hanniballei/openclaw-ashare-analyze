from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.symbols import detect_scenario, extract_position, extract_symbol_token, normalize_cn_symbol  # noqa: E402
from common.rqdata_client import RQDataClient  # noqa: E402


class SymbolsTest(unittest.TestCase):
    def test_normalize_cn_symbol(self) -> None:
        self.assertEqual(normalize_cn_symbol("600875"), "600875.XSHG")
        self.assertEqual(normalize_cn_symbol("sz159206"), "159206.XSHE")
        self.assertEqual(normalize_cn_symbol("000001.XSHE"), "000001.XSHE")

    def test_detect_scenario(self) -> None:
        self.assertEqual(detect_scenario("从 159625 里挑几只强势股"), "STOCK_PICKER")
        self.assertEqual(detect_scenario("29.3 建仓 200 股今天怎么操作"), "TRADING_STRATEGY")
        self.assertEqual(detect_scenario("看看 NVDA 和标普"), "US_STOCK")
        self.assertEqual(detect_scenario("怎么看光纤板块？"), "THEME_ANALYZE")
        self.assertEqual(detect_scenario("A股中卫星通信的公司有哪些头部企业？"), "THEME_ANALYZE")
        self.assertEqual(detect_scenario("AI、算力、半导体、机器人哪个更强？"), "THEME_ANALYZE")
        self.assertEqual(detect_scenario("现在美股的卫星通信涨疯了，是否对明天的A股有影响？"), "EVENT_IMPACT")

    def test_extract_symbol_token_prefers_explicit_symbol(self) -> None:
        self.assertEqual(extract_symbol_token("看看 NVDA 和标普"), "NVDA")
        self.assertEqual(extract_symbol_token("看看NVDA"), "NVDA")
        self.assertEqual(extract_symbol_token("分析NVDA"), "NVDA")
        self.assertEqual(extract_symbol_token("分析 sz159206"), "159206.XSHE")
        self.assertEqual(extract_symbol_token("从159625里挑几只强势股"), "159625.XSHE")

    def test_extract_position(self) -> None:
        position = extract_position("通富微电成本 29.3 持仓 5 手")
        self.assertEqual(position.shares, 500)
        self.assertEqual(position.avg_price, 29.3)

    def test_match_records_supports_name_inside_sentence(self) -> None:
        client = RQDataClient()
        records = [
            {"order_book_id": "600875.XSHG", "symbol": "东方电气", "type": "CS"},
            {"order_book_id": "600487.XSHG", "symbol": "亨通光电", "type": "CS"},
        ]
        match = client._match_records(records, "分析东方电气")
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.symbol, "600875.XSHG")

        match = client._match_records(records, "亨通光电后面怎么走")
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.symbol, "600487.XSHG")


if __name__ == "__main__":
    unittest.main()
