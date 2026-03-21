from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import Candle, InstrumentMatch, SkillRuntimeError
from .symbols import CN_INDEX_ALIASES, extract_symbol_token, infer_cn_instrument_type, normalize_cn_symbol


class RQDataClient:
    def __init__(self) -> None:
        self._module = None

    def resolve_instrument(self, query: str, instrument_type: Optional[str] = None) -> InstrumentMatch:
        candidate = normalize_cn_symbol(query or "")
        if not candidate:
            token = extract_symbol_token(query or "")
            candidate = normalize_cn_symbol(token or "")

        if candidate:
            module = self._ensure_module()
            resolved_type = instrument_type or infer_cn_instrument_type(candidate)
            try:
                detail = module.instruments(candidate)
                name = (
                    getattr(detail, "symbol", None)
                    or getattr(detail, "display_name", None)
                    or candidate
                )
            except Exception:
                name = query or candidate
            return InstrumentMatch(symbol=candidate, name=name, instrument_type=resolved_type)

        alias_symbol = next((symbol for alias, symbol in CN_INDEX_ALIASES.items() if alias in (query or "")), None)
        if alias_symbol:
            return InstrumentMatch(symbol=alias_symbol, name=query, instrument_type="INDX")

        module = self._ensure_module()
        today = date.today().strftime("%Y%m%d")
        search_types = [instrument_type] if instrument_type else ["CS", "ETF", "INDX"]
        for item_type in search_types:
            records = self._records(module.all_instruments(type=item_type, date=today))
            match = self._match_records(records, query)
            if match:
                return match
        raise SkillRuntimeError(f"未在 RQData 中找到标的: {query}")

    def fetch_candles(self, symbol: str, frequency: str, count: int = 90) -> List[Candle]:
        module = self._ensure_module()
        end_date = date.today().isoformat()
        start_date = self._start_date(frequency, count)
        fields = ["open", "high", "low", "close", "volume", "total_turnover"]
        if frequency == "1d":
            fields.append("prev_close")
        table = module.get_price(
            order_book_ids=symbol,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            fields=fields,
            adjust_type="pre",
            skip_suspended=False,
            expect_df=True,
            market="cn",
        )
        candles = self._candles_from_price_table(table)
        previous_close: Optional[float] = None
        for candle in candles:
            if candle.prev_close is None:
                candle.prev_close = previous_close
            previous_close = candle.close
        if len(candles) < 2:
            raise SkillRuntimeError(f"{symbol} 的 {frequency} 行情不足，无法生成分析。")
        return candles[-count:]

    def fetch_fundamentals(self, symbol: str) -> Dict[str, Optional[float]]:
        module = self._ensure_module()
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=40)).isoformat()

        factor_map = {
            "pe_ttm": "pe_ratio_ttm",
            "pb": "pb_ratio_lf",
            "market_cap": "market_cap",
            "roe_ttm": "return_on_equity_ttm",
            "revenue_growth": "operating_revenue_growth_ratio_ttm",
            "profit_growth": "net_profit_growth_ratio_ttm",
        }

        payload: Dict[str, Optional[float]] = {}
        for key, factor in factor_map.items():
            try:
                result = module.get_factor(
                    order_book_ids=[symbol],
                    factor=factor,
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception:
                payload[key] = None
                continue
            payload[key] = self._extract_latest_scalar(result)
        return payload

    def fetch_etf_metadata(self, symbol: str) -> Dict[str, Any]:
        module = self._ensure_module()
        metadata: Dict[str, Any] = {
            "tracking_index": None,
            "fund_scale": None,
            "components": [],
        }
        try:
            instrument = module.instruments(symbol)
        except Exception:
            instrument = None

        if instrument is not None:
            metadata["tracking_index"] = (
                getattr(instrument, "underlying_order_book_id", None)
                or getattr(instrument, "benchmark", None)
                or getattr(instrument, "tracking_index", None)
            )
            fund_scale = (
                getattr(instrument, "fund_size", None)
                or getattr(instrument, "asset_size", None)
                or getattr(instrument, "asset_net_value", None)
            )
            metadata["fund_scale"] = self._float_or_none(fund_scale)

        metadata["components"] = self.list_etf_components(symbol)
        return metadata

    def list_etf_components(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        module = self._ensure_module()
        tracking_index = None
        try:
            instrument = module.instruments(symbol)
            tracking_index = (
                getattr(instrument, "underlying_order_book_id", None)
                or getattr(instrument, "benchmark", None)
                or getattr(instrument, "tracking_index", None)
            )
        except Exception:
            tracking_index = None

        if not tracking_index or not hasattr(module, "index_components"):
            return []

        try:
            table = module.index_components(tracking_index)
        except Exception:
            return []

        if isinstance(table, list) and table and isinstance(table[0], str):
            components: List[Dict[str, Any]] = []
            for component_symbol in table[:limit]:
                name = component_symbol
                try:
                    detail = module.instruments(component_symbol)
                    name = (
                        getattr(detail, "symbol", None)
                        or getattr(detail, "display_name", None)
                        or component_symbol
                    )
                except Exception:
                    name = component_symbol
                components.append(
                    {
                        "symbol": component_symbol,
                        "name": name,
                        "weight": None,
                    }
                )
            return components

        records = self._records(table)
        components: List[Dict[str, Any]] = []
        for record in records[:limit]:
            components.append(
                {
                    "symbol": record.get("order_book_id") or record.get("index_component"),
                    "name": record.get("symbol") or record.get("name") or record.get("display_name"),
                    "weight": self._float_or_none(record.get("weight")),
                }
            )
        return components

    def _ensure_module(self):
        if self._module is not None:
            return self._module

        self._load_dotenv()
        try:
            import rqdatac  # type: ignore
        except ModuleNotFoundError as exc:
            raise SkillRuntimeError(
                "未安装 rqdatac。请先执行 `pip install -r requirements.txt`，并确保 A 股场景使用同一 Python 环境。"
            ) from exc

        primary_uri = os.environ.get("RQDATA_PRIMARY_URI")
        if not primary_uri:
            raise SkillRuntimeError(
                "未配置 RQDATA_PRIMARY_URI，无法执行 A 股、ETF 或大盘分析。请先设置 RQData 连接环境变量。"
            )

        try:
            rqdatac.init(uri=primary_uri)
        except Exception:
            backup_password = os.environ.get("RQDATA_BACKUP_PASSWORD")
            backup_host = os.environ.get("RQDATA_BACKUP_HOST")
            if not backup_password or not backup_host:
                raise SkillRuntimeError("RQData 主连接失败，且未配置备用连接。")
            backup_user = os.environ.get("RQDATA_BACKUP_USERNAME", "license")
            backup_port = int(os.environ.get("RQDATA_BACKUP_PORT", "16011"))
            try:
                rqdatac.reset()
            except Exception:
                pass
            try:
                rqdatac.init(backup_user, backup_password, (backup_host, backup_port))
            except Exception as exc:
                raise SkillRuntimeError("RQData 主备连接均失败。") from exc

        self._module = rqdatac
        return self._module

    def _match_records(self, records: List[Dict[str, Any]], query: str) -> Optional[InstrumentMatch]:
        query_clean = (query or "").strip()
        if not query_clean:
            return None

        exact_fields = ("order_book_id", "symbol", "display_name", "name", "abbrev_symbol")
        for record in records:
            for field in exact_fields:
                value = str(record.get(field, "")).strip()
                if value and value == query_clean:
                    return self._record_to_match(record)

        lowered = query_clean.lower()
        for record in records:
            haystacks = [str(record.get(field, "")).lower() for field in exact_fields]
            if any(lowered in value for value in haystacks if value):
                return self._record_to_match(record)

        contained_matches: List[tuple[int, Dict[str, Any]]] = []
        for record in records:
            for field in exact_fields:
                value = str(record.get(field, "")).strip()
                if not value:
                    continue
                value_lower = value.lower()
                if len(value_lower) < 2:
                    continue
                if value_lower in lowered:
                    contained_matches.append((len(value_lower), record))
                    break
        if contained_matches:
            contained_matches.sort(key=lambda item: item[0], reverse=True)
            return self._record_to_match(contained_matches[0][1])
        return None

    def _record_to_match(self, record: Dict[str, Any]) -> InstrumentMatch:
        symbol = str(record.get("order_book_id") or record.get("symbol") or "")
        instrument_type = str(record.get("type") or infer_cn_instrument_type(symbol))
        name = str(record.get("symbol") or record.get("display_name") or record.get("name") or symbol)
        return InstrumentMatch(symbol=symbol, name=name, instrument_type=instrument_type, metadata=record)

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
                    pass
        if isinstance(table, list):
            return [item for item in table if isinstance(item, dict)]
        return []

    def _candles_from_price_table(self, table: Any) -> List[Candle]:
        if table is None:
            return []
        if hasattr(table, "reset_index"):
            try:
                records = table.reset_index().to_dict("records")
            except Exception:
                records = []
        else:
            records = []

        candles: List[Candle] = []
        for record in records:
            timestamp = (
                record.get("datetime")
                or record.get("trading_date")
                or record.get("date")
                or record.get("index")
            )
            if timestamp is None:
                continue
            candles.append(
                Candle(
                    timestamp=str(timestamp),
                    open=self._float_or_zero(record.get("open")),
                    high=self._float_or_zero(record.get("high")),
                    low=self._float_or_zero(record.get("low")),
                    close=self._float_or_zero(record.get("close")),
                    volume=self._float_or_zero(record.get("volume")),
                    amount=self._float_or_zero(record.get("total_turnover") or record.get("amount")),
                    prev_close=self._float_or_none(record.get("prev_close")),
                )
            )
        return candles

    def _extract_latest_scalar(self, table: Any) -> Optional[float]:
        if table is None:
            return None
        if hasattr(table, "dropna"):
            try:
                values = table.dropna().values.tolist()
                flattened: List[Any] = []
                for item in values:
                    if isinstance(item, list):
                        flattened.extend(item)
                    else:
                        flattened.append(item)
                flattened = [item for item in flattened if item is not None]
                if flattened:
                    return self._float_or_none(flattened[-1])
            except Exception:
                pass
        if isinstance(table, (list, tuple)) and table:
            return self._float_or_none(table[-1])
        return None

    def _start_date(self, frequency: str, count: int) -> str:
        if frequency == "5m":
            days = max(20, count // 20)
        elif frequency == "60m":
            days = max(90, count)
        else:
            days = max(180, count * 2)
        return (date.today() - timedelta(days=days)).isoformat()

    def _load_dotenv(self) -> None:
        try:
            from dotenv import load_dotenv  # type: ignore
        except ModuleNotFoundError:
            return
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    def _float_or_zero(self, value: Any) -> float:
        return float(value) if value is not None else 0.0

    def _float_or_none(self, value: Any) -> Optional[float]:
        if value in (None, "", "nan"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
