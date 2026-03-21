from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from .akshare_client import AkshareClient
from .formatters import change_pct, to_json
from .indicators import compute_indicator_snapshot
from .models import Candle, InstrumentMatch, PositionInput, SkillRuntimeError
from .price_levels import find_price_levels
from .rqdata_client import RQDataClient
from .symbols import CN_INDEX_ALIASES, US_INDEX_ALIASES, extract_position, extract_symbol_token
from .timeseries import aggregate_to_4h_from_60m, latest
from .yfinance_client import YFinanceClient


def analyze_stock_request(query: str, symbol: Optional[str] = None, bars: int = 90) -> Dict[str, Any]:
    rqdata = RQDataClient()
    akshare = AkshareClient()
    instrument = rqdata.resolve_instrument(symbol or query, instrument_type="CS")
    payload = _build_cn_asset_payload("STOCK_ANALYZE", instrument, rqdata, akshare, bars)
    payload["name"] = _clean_name(payload["name"], query)
    return payload


def analyze_etf_request(query: str, symbol: Optional[str] = None, bars: int = 90) -> Dict[str, Any]:
    rqdata = RQDataClient()
    akshare = AkshareClient()
    instrument = rqdata.resolve_instrument(symbol or query, instrument_type="ETF")
    payload = _build_cn_asset_payload(
        "ETF_ANALYZE",
        instrument,
        rqdata,
        akshare,
        bars,
        include_fundamentals=False,
        include_billboard=False,
    )
    payload["etf_details"] = rqdata.fetch_etf_metadata(instrument.symbol)
    payload["name"] = _clean_name(payload["name"], query)
    return payload


def analyze_market_request(query: str, bars: int = 90) -> Dict[str, Any]:
    rqdata = RQDataClient()
    akshare = AkshareClient()
    indices = {
        "shanghai": InstrumentMatch(symbol="000001.XSHG", name="上证指数", instrument_type="INDX"),
        "shenzhen": InstrumentMatch(symbol="399001.XSHE", name="深证成指", instrument_type="INDX"),
        "chinext": InstrumentMatch(symbol="399006.XSHE", name="创业板指", instrument_type="INDX"),
    }
    summaries = {}
    timestamp = None
    for key, instrument in indices.items():
        daily = rqdata.fetch_candles(instrument.symbol, "1d", bars)
        latest_bar = latest(daily)
        previous = latest_bar.prev_close if latest_bar.prev_close is not None else (daily[-2].close if len(daily) > 1 else None)
        timestamp = latest_bar.timestamp
        summaries[key] = {
            "symbol": instrument.symbol,
            "name": instrument.name,
            "current_price": latest_bar.close,
            "change_pct": change_pct(latest_bar.close, previous),
            "indicators": {
                "daily": compute_indicator_snapshot(daily),
            },
        }
    return {
        "scenario": "MARKET_OVERVIEW",
        "query": query,
        "timestamp": timestamp,
        "indices": summaries,
        "market_breadth": akshare.fetch_market_breadth(),
        "sector_performance": akshare.fetch_sector_performance(),
        "northbound_flow": akshare.fetch_northbound_flow(),
    }


def analyze_us_stock_request(query: str, symbol: Optional[str] = None, bars: int = 90) -> Dict[str, Any]:
    yfinance = YFinanceClient()
    target = symbol or extract_symbol_token(query or "")
    indices = {
        alias: _build_us_asset_payload(
            InstrumentMatch(symbol=ticker, name=alias, instrument_type="US_INDEX", market="US"),
            yfinance,
            bars,
        )
        for alias, ticker in US_INDEX_ALIASES.items()
    }
    unique_indices = {}
    for alias in ("道琼斯", "标普", "纳斯达克"):
        unique_indices[alias] = indices[alias]

    payload: Dict[str, Any] = {
        "scenario": "US_STOCK",
        "query": query,
        "timestamp": unique_indices["纳斯达克"]["timestamp"],
        "indices": unique_indices,
    }
    if target and not target.startswith("^"):
        instrument = yfinance.resolve_instrument(target)
        payload["stock"] = _build_us_asset_payload(instrument, yfinance, bars)
    return payload


def build_trading_strategy_request(query: str, symbol: Optional[str] = None, bars: int = 90) -> Dict[str, Any]:
    payload = analyze_stock_request(query=query, symbol=symbol, bars=bars)
    position = extract_position(query)
    payload["scenario"] = "TRADING_STRATEGY"
    payload["position"] = position.to_dict()
    payload["strategy"] = _generate_strategy(payload, position)
    return payload


def run_stock_picker_request(query: str, symbol: Optional[str] = None, bars: int = 90, top: int = 10) -> Dict[str, Any]:
    rqdata = RQDataClient()
    etf = rqdata.resolve_instrument(symbol or query, instrument_type="ETF")
    components = rqdata.list_etf_components(etf.symbol, limit=max(top * 3, 20))
    if not components:
        raise SkillRuntimeError("未获取到 ETF 成分股。请提供更明确的 ETF 代码，或检查 RQData ETF 元数据是否可用。")

    ranking: List[Dict[str, Any]] = []
    for component in components:
        component_symbol = component.get("symbol")
        if not component_symbol:
            continue
        try:
            candles = rqdata.fetch_candles(component_symbol, "1d", bars)
            indicators = compute_indicator_snapshot(candles)
            fundamentals = rqdata.fetch_fundamentals(component_symbol)
            latest_bar = latest(candles)
            previous = latest_bar.prev_close if latest_bar.prev_close is not None else (candles[-2].close if len(candles) > 1 else None)
            ranking.append(
                _score_component(
                    symbol=component_symbol,
                    name=component.get("name") or component_symbol,
                    latest_bar=latest_bar,
                    previous_close=previous,
                    indicators=indicators,
                    fundamentals=fundamentals,
                )
            )
        except SkillRuntimeError:
            continue

    ranking = sorted(ranking, key=lambda item: item["score"], reverse=True)[:top]
    for rank, item in enumerate(ranking, start=1):
        item["rank"] = rank

    return {
        "scenario": "STOCK_PICKER",
        "etf": {
            "symbol": etf.symbol,
            "name": etf.name,
        },
        "selection_basis": {
            "bars": bars,
            "top": top,
            "score_components": [
                "price_above_ma20",
                "price_above_ma60",
                "positive_macd",
                "healthy_rsi",
                "positive_revenue_growth",
                "positive_profit_growth",
            ],
        },
        "ranking": ranking,
    }


def main_stock() -> None:
    args = _parse_asset_args("Analyze an A-share stock and emit structured JSON.")
    payload = analyze_stock_request(query=args.query, symbol=args.symbol, bars=args.bars)
    print(to_json(payload, pretty=not args.compact))


def main_etf() -> None:
    args = _parse_asset_args("Analyze an ETF and emit structured JSON.")
    payload = analyze_etf_request(query=args.query, symbol=args.symbol, bars=args.bars)
    print(to_json(payload, pretty=not args.compact))


def main_market() -> None:
    parser = argparse.ArgumentParser(description="Analyze the China market and emit structured JSON.")
    parser.add_argument("--query", default="今天 A 股走势如何")
    parser.add_argument("--bars", type=int, default=90)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    payload = analyze_market_request(query=args.query, bars=args.bars)
    print(to_json(payload, pretty=not args.compact))


def main_strategy() -> None:
    args = _parse_asset_args("Generate a trading strategy payload from a user query.")
    payload = build_trading_strategy_request(query=args.query, symbol=args.symbol, bars=args.bars)
    print(to_json(payload, pretty=not args.compact))


def main_us_stock() -> None:
    args = _parse_asset_args("Analyze a US stock or index and emit structured JSON.")
    payload = analyze_us_stock_request(query=args.query, symbol=args.symbol, bars=args.bars)
    print(to_json(payload, pretty=not args.compact))


def main_stock_picker() -> None:
    parser = argparse.ArgumentParser(description="Rank ETF components and emit structured JSON.")
    parser.add_argument("--query", default="")
    parser.add_argument("--symbol", default="")
    parser.add_argument("--bars", type=int, default=90)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    if not args.query and not args.symbol:
        raise SkillRuntimeError("请至少提供 --query 或 --symbol，用于确定 ETF。")
    payload = run_stock_picker_request(query=args.query, symbol=args.symbol, bars=args.bars, top=args.top)
    print(to_json(payload, pretty=not args.compact))


def _parse_asset_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--query", default="")
    parser.add_argument("--symbol", default="")
    parser.add_argument("--bars", type=int, default=90)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    if not args.query and not args.symbol:
        raise SkillRuntimeError("请至少提供 --query 或 --symbol。")
    return args


def _build_cn_asset_payload(
    scenario: str,
    instrument: InstrumentMatch,
    rqdata: RQDataClient,
    akshare: AkshareClient,
    bars: int,
    include_fundamentals: bool = True,
    include_billboard: bool = True,
) -> Dict[str, Any]:
    candles_5m = rqdata.fetch_candles(instrument.symbol, "5m", bars)
    candles_60m = rqdata.fetch_candles(instrument.symbol, "60m", bars)
    candles_daily = rqdata.fetch_candles(instrument.symbol, "1d", bars)
    candles_4h = aggregate_to_4h_from_60m(candles_60m)

    latest_bar = latest(candles_daily)
    previous = latest_bar.prev_close if latest_bar.prev_close is not None else (candles_daily[-2].close if len(candles_daily) > 1 else None)

    return {
        "scenario": scenario,
        "symbol": instrument.symbol,
        "name": instrument.name,
        "timestamp": latest_bar.timestamp,
        "current_price": latest_bar.close,
        "change_pct": change_pct(latest_bar.close, previous),
        "open": latest_bar.open,
        "high": latest_bar.high,
        "low": latest_bar.low,
        "prev_close": previous,
        "volume": latest_bar.volume,
        "amount": latest_bar.amount,
        "turnover_rate": None,
        "indicators": {
            "daily": compute_indicator_snapshot(candles_daily),
            "4h": compute_indicator_snapshot(candles_4h),
            "1h": compute_indicator_snapshot(candles_60m),
            "5min": compute_indicator_snapshot(candles_5m),
        },
        "price_levels": find_price_levels(candles_daily),
        "fundamentals": rqdata.fetch_fundamentals(instrument.symbol) if include_fundamentals else _empty_fundamentals(),
        "money_flow": akshare.fetch_money_flow(instrument.symbol),
        "billboard": akshare.fetch_billboard(instrument.symbol) if include_billboard else [],
    }


def _build_us_asset_payload(instrument: InstrumentMatch, yfinance: YFinanceClient, bars: int) -> Dict[str, Any]:
    candles_5m = yfinance.fetch_candles(instrument.symbol, "5m", bars)
    candles_60m = yfinance.fetch_candles(instrument.symbol, "60m", bars)
    candles_daily = yfinance.fetch_candles(instrument.symbol, "1d", bars)
    candles_4h = aggregate_to_4h_from_60m(candles_60m)

    latest_bar = latest(candles_daily)
    previous = latest_bar.prev_close if latest_bar.prev_close is not None else (candles_daily[-2].close if len(candles_daily) > 1 else None)

    return {
        "symbol": instrument.symbol,
        "name": instrument.name,
        "timestamp": latest_bar.timestamp,
        "current_price": latest_bar.close,
        "change_pct": change_pct(latest_bar.close, previous),
        "open": latest_bar.open,
        "high": latest_bar.high,
        "low": latest_bar.low,
        "prev_close": previous,
        "volume": latest_bar.volume,
        "amount": latest_bar.amount,
        "turnover_rate": None,
        "indicators": {
            "daily": compute_indicator_snapshot(candles_daily),
            "4h": compute_indicator_snapshot(candles_4h),
            "1h": compute_indicator_snapshot(candles_60m),
            "5min": compute_indicator_snapshot(candles_5m),
        },
        "price_levels": find_price_levels(candles_daily),
        "fundamentals": yfinance.fetch_basics(instrument.symbol),
        "money_flow": {
            "today_net": None,
            "5day_net": None,
            "source": "unavailable",
        },
        "billboard": [],
    }


def _generate_strategy(payload: Dict[str, Any], position: PositionInput) -> Dict[str, Any]:
    supports = payload["price_levels"]["support"]
    resistances = payload["price_levels"]["resistance"]
    current = payload["current_price"]
    avg_price = position.avg_price
    ma20 = payload["indicators"]["daily"]["ma"]["ma20"]

    entry_levels = supports[:2] if supports else [current * 0.98, current * 0.95]
    add_levels = supports[:2] if supports else [current * 0.97, current * 0.94]
    take_profit = resistances[:2] if resistances else [current * 1.05, current * 1.1]

    stop_loss_candidates = [current * 0.94]
    if supports:
        stop_loss_candidates.append(supports[0] * 0.99)
    if avg_price:
        stop_loss_candidates.append(avg_price * 0.93)
    stop_loss = min(stop_loss_candidates)

    advice = "先按支撑和压力位分批应对。"
    if avg_price and current < avg_price and current > stop_loss:
        advice = "股价还在成本下方，但没有彻底破位，先控仓等待，不要追着补。"
    if ma20 and current > ma20 and take_profit:
        advice = "短线节奏还没坏，靠近第一压力位可以考虑分批止盈。"
    if current <= stop_loss:
        advice = "已经接近或跌破止损区，优先控制风险。"

    return {
        "entry_levels": entry_levels,
        "add_levels": add_levels,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "advice": advice,
    }


def _score_component(
    symbol: str,
    name: str,
    latest_bar: Candle,
    previous_close: Optional[float],
    indicators: Dict[str, Any],
    fundamentals: Dict[str, Optional[float]],
) -> Dict[str, Any]:
    score = 0.0
    reasons: List[str] = []
    ma20 = indicators["ma"]["ma20"]
    ma60 = indicators["ma"]["ma60"]
    macd_histogram = indicators["macd"]["histogram"]
    rsi6 = indicators["rsi"]["rsi6"]

    if ma20 and latest_bar.close > ma20:
        score += 20
        reasons.append("站上 MA20")
    if ma60 and latest_bar.close > ma60:
        score += 15
        reasons.append("站上 MA60")
    if macd_histogram and macd_histogram > 0:
        score += 20
        reasons.append("MACD 柱体为正")
    if rsi6 and 50 <= rsi6 <= 70:
        score += 10
        reasons.append("RSI 处于偏强但未过热区")
    if (fundamentals.get("revenue_growth") or 0) > 0:
        score += 15
        reasons.append("营收增速为正")
    if (fundamentals.get("profit_growth") or 0) > 0:
        score += 20
        reasons.append("利润增速为正")

    return {
        "rank": None,
        "symbol": symbol,
        "name": name,
        "score": score,
        "current_price": latest_bar.close,
        "change_pct": change_pct(latest_bar.close, previous_close),
        "ma20": ma20,
        "ma60": ma60,
        "macd_histogram": macd_histogram,
        "revenue_growth": fundamentals.get("revenue_growth"),
        "profit_growth": fundamentals.get("profit_growth"),
        "reasons": reasons,
    }


def _clean_name(current_name: str, query: str) -> str:
    if current_name and current_name != query:
        return current_name
    symbol = extract_symbol_token(query or "")
    if symbol and symbol in CN_INDEX_ALIASES.values():
        return next(alias for alias, code in CN_INDEX_ALIASES.items() if code == symbol)
    return current_name


def _empty_fundamentals() -> Dict[str, None]:
    return {
        "pe_ttm": None,
        "pb": None,
        "market_cap": None,
        "roe_ttm": None,
        "revenue_growth": None,
        "profit_growth": None,
    }
