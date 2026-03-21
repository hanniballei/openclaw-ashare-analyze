from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional


class AkshareClient:
    def __init__(self) -> None:
        self._module = None

    def fetch_money_flow(self, symbol: str) -> Dict[str, Optional[float | str]]:
        module = self._ensure_module()
        code = symbol.split(".", 1)[0]
        today_net = self._lookup_money_flow(module, code, "今日")
        five_day_net = self._lookup_money_flow(module, code, "5日")
        return {
            "today_net": today_net,
            "5day_net": five_day_net,
            "source": "akshare",
        }

    def fetch_billboard(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        module = self._ensure_module()
        code = symbol.split(".", 1)[0]
        records: List[Dict[str, Any]] = []
        start_date = (date.today() - timedelta(days=30)).strftime("%Y%m%d")
        end_date = date.today().strftime("%Y%m%d")
        if hasattr(module, "stock_lhb_detail_em"):
            try:
                records = self._records(module.stock_lhb_detail_em(start_date=start_date, end_date=end_date))
            except Exception:
                records = []
        if not records and hasattr(module, "stock_lhb_stock_statistic_em"):
            try:
                records = self._records(module.stock_lhb_stock_statistic_em(symbol=code))
            except Exception:
                records = []

        filtered = [record for record in records if str(record.get("代码") or record.get("股票代码") or "") == code]
        return [
            {
                "date": record.get("上榜日") or record.get("交易日期"),
                "type": record.get("解读") or record.get("上榜原因"),
                "amount": self._float_or_none(record.get("成交额") or record.get("净买额") or record.get("买入额")),
                "trader": record.get("营业部名称") or record.get("营业部"),
            }
            for record in filtered[:limit]
        ]

    def fetch_market_breadth(self) -> Dict[str, Optional[int]]:
        module = self._ensure_module()
        if not hasattr(module, "stock_zh_a_spot_em"):
            return {
                "up_count": None,
                "down_count": None,
                "flat_count": None,
                "limit_up_count": None,
                "limit_down_count": None,
            }
        try:
            records = self._records(module.stock_zh_a_spot_em())
        except Exception:
            records = []

        change_values = [self._float_or_none(record.get("涨跌幅")) for record in records]
        up_count = sum(1 for value in change_values if value is not None and value > 0)
        down_count = sum(1 for value in change_values if value is not None and value < 0)
        flat_count = sum(1 for value in change_values if value == 0)
        limit_up_count = sum(1 for value in change_values if value is not None and value >= 9.7)
        limit_down_count = sum(1 for value in change_values if value is not None and value <= -9.7)

        return {
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "limit_up_count": limit_up_count,
            "limit_down_count": limit_down_count,
        }

    def fetch_sector_performance(self, top_n: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        module = self._ensure_module()
        fetchers = [
            getattr(module, "stock_board_industry_name_em", None),
            getattr(module, "stock_board_industry_spot_em", None),
        ]
        records: List[Dict[str, Any]] = []
        for fetcher in fetchers:
            if fetcher is None:
                continue
            try:
                records = self._records(fetcher())
            except Exception:
                records = []
            if records:
                break

        normalized = [
            {
                "name": record.get("板块名称") or record.get("名称"),
                "change_pct": self._float_or_none(record.get("涨跌幅")),
            }
            for record in records
        ]
        normalized = [item for item in normalized if item["name"]]
        leaders = sorted(normalized, key=lambda item: item["change_pct"] or -10**9, reverse=True)[:top_n]
        laggards = sorted(normalized, key=lambda item: item["change_pct"] or 10**9)[:top_n]
        return {"leaders": leaders, "laggards": laggards}

    def fetch_northbound_flow(self) -> Dict[str, Optional[float | str]]:
        module = self._ensure_module()
        fetchers = [
            getattr(module, "stock_hsgt_north_net_flow_in_em", None),
            getattr(module, "stock_hsgt_fund_flow_summary_em", None),
        ]
        for fetcher in fetchers:
            if fetcher is None:
                continue
            try:
                records = self._records(fetcher())
            except Exception:
                records = []
            if not records:
                continue
            last_row = records[-1]
            return {
                "today_net": self._float_or_none(
                    last_row.get("净流入")
                    or last_row.get("当日资金流入")
                    or last_row.get("北向资金")
                    or last_row.get("净买额")
                ),
                "source": "akshare",
            }
        return {"today_net": None, "source": "akshare"}

    def _ensure_module(self):
        if self._module is not None:
            return self._module
        try:
            import akshare  # type: ignore
        except ModuleNotFoundError:
            self._module = _NullAkshare()
            return self._module
        self._module = akshare
        return self._module

    def _lookup_money_flow(self, module: Any, code: str, indicator: str) -> Optional[float]:
        fetcher = getattr(module, "stock_individual_fund_flow_rank", None)
        if fetcher is None:
            return None
        try:
            records = self._records(fetcher(indicator=indicator))
        except Exception:
            return None
        matched = next(
            (
                record
                for record in records
                if str(record.get("代码") or record.get("股票代码") or "") == code
            ),
            None,
        )
        if matched is None:
            return None

        preferred_keys = [
            f"{indicator}主力净流入-净额",
            f"{indicator}主力净流入净额",
            "主力净流入-净额",
            "主力净流入净额",
        ]
        for key in preferred_keys:
            value = self._float_or_none(matched.get(key))
            if value is not None:
                return value
        return None

    def _records(self, table: Any) -> List[Dict[str, Any]]:
        if table is None:
            return []
        if hasattr(table, "to_dict"):
            try:
                return table.to_dict("records")
            except TypeError:
                try:
                    return table.reset_index().to_dict("records")
                except Exception:
                    return []
        if isinstance(table, list):
            return [item for item in table if isinstance(item, dict)]
        return []

    def _float_or_none(self, value: Any) -> Optional[float]:
        if value in (None, "", "nan"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class _NullAkshare:
    """Compatibility object that makes all optional enrichments return empty values."""

