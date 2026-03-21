from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import Candle, InstrumentMatch, SkillRuntimeError


class YFinanceClient:
    def __init__(self) -> None:
        self._module = None

    def resolve_instrument(self, query: str) -> InstrumentMatch:
        symbol = (query or "").strip().upper()
        if not symbol:
            raise SkillRuntimeError("未提供有效的美股代码。")
        return InstrumentMatch(symbol=symbol, name=symbol, instrument_type="US_STOCK", market="US")

    def fetch_candles(self, symbol: str, interval: str, count: int = 90) -> List[Candle]:
        module = self._ensure_module()
        ticker = module.Ticker(symbol)
        period_map = {
            "5m": "60d",
            "60m": "730d",
            "1d": "2y",
        }
        history = ticker.history(period=period_map.get(interval, "2y"), interval=interval, auto_adjust=False)
        if history is None or getattr(history, "empty", False):
            raise SkillRuntimeError(f"未获取到 {symbol} 的 {interval} 行情。")

        records = history.reset_index().to_dict("records")
        candles: List[Candle] = []
        previous_close: Optional[float] = None
        for record in records:
            timestamp = str(record.get("Datetime") or record.get("Date"))
            close = self._float_or_zero(record.get("Close"))
            candles.append(
                Candle(
                    timestamp=timestamp,
                    open=self._float_or_zero(record.get("Open")),
                    high=self._float_or_zero(record.get("High")),
                    low=self._float_or_zero(record.get("Low")),
                    close=close,
                    volume=self._float_or_zero(record.get("Volume")),
                    amount=0.0,
                    prev_close=previous_close,
                )
            )
            previous_close = close
        return candles[-count:]

    def fetch_basics(self, symbol: str) -> Dict[str, Optional[float]]:
        module = self._ensure_module()
        info = getattr(module.Ticker(symbol), "info", {}) or {}
        return {
            "pe_ttm": self._float_or_none(info.get("trailingPE")),
            "pb": self._float_or_none(info.get("priceToBook")),
            "market_cap": self._float_or_none(info.get("marketCap")),
            "roe_ttm": self._float_or_none(info.get("returnOnEquity")),
            "revenue_growth": self._float_or_none(info.get("revenueGrowth")),
            "profit_growth": self._float_or_none(info.get("earningsGrowth")),
        }

    def _ensure_module(self):
        if self._module is not None:
            return self._module
        try:
            import yfinance  # type: ignore
        except ModuleNotFoundError as exc:
            raise SkillRuntimeError(
                "未安装 yfinance，无法执行美股分析。请先执行 `pip install -r requirements.txt`。"
            ) from exc
        self._module = yfinance
        return self._module

    def _float_or_zero(self, value: Any) -> float:
        return float(value) if value is not None else 0.0

    def _float_or_none(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
