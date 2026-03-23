from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from .models import PositionInput

CN_INDEX_ALIASES = {
    "上证": "000001.XSHG",
    "上证指数": "000001.XSHG",
    "沪指": "000001.XSHG",
    "大盘": "000001.XSHG",
    "深成指": "399001.XSHE",
    "深证成指": "399001.XSHE",
    "创业板": "399006.XSHE",
    "创业板指": "399006.XSHE",
}

US_INDEX_ALIASES = {
    "道琼斯": "^DJI",
    "道指": "^DJI",
    "标普": "^GSPC",
    "标普500": "^GSPC",
    "纳斯达克": "^IXIC",
    "纳指": "^IXIC",
}

US_TICKER_STOPWORDS = {
    "A",
    "AN",
    "AND",
    "ETF",
    "FOR",
    "THE",
    "USD",
}


def normalize_cn_symbol(raw: str) -> Optional[str]:
    if not raw:
        return None

    token = raw.strip().upper()
    if re.fullmatch(r"\d{6}\.(XSHG|XSHE)", token):
        return token

    prefixed = re.fullmatch(r"(SH|SZ)(\d{6})", token)
    if prefixed:
        exchange = "XSHG" if prefixed.group(1) == "SH" else "XSHE"
        return f"{prefixed.group(2)}.{exchange}"

    digits = re.fullmatch(r"\d{6}", token)
    if digits:
        code = digits.group(0)
        if code.startswith(("5", "6", "9")):
            return f"{code}.XSHG"
        return f"{code}.XSHE"

    return None


def infer_cn_instrument_type(symbol: str) -> str:
    code = symbol.split(".", 1)[0]
    if code in {"000001", "399001", "399006"}:
        return "INDX"
    if code.startswith(("15", "16", "50", "51", "52", "56", "58")):
        return "ETF"
    return "CS"


def extract_symbol_token(query: str) -> Optional[str]:
    if not query:
        return None

    match = re.search(r"(?<![A-Za-z0-9])(?:sh|sz)\d{6}(?![A-Za-z0-9])", query, flags=re.IGNORECASE)
    if match:
        return normalize_cn_symbol(match.group(0))

    match = re.search(r"(?<!\d)\d{6}(?:\.(?:XSHG|XSHE))?(?!\d)", query, flags=re.IGNORECASE)
    if match:
        return normalize_cn_symbol(match.group(0))

    for token in _extract_us_ticker_candidates(query):
        if token in US_TICKER_STOPWORDS:
            continue
        if token in {"XSHG", "XSHE"}:
            continue
        return token

    for alias, symbol in {**CN_INDEX_ALIASES, **US_INDEX_ALIASES}.items():
        if alias in query:
            return symbol

    return None


def _extract_us_ticker_candidates(query: str) -> list[str]:
    matches = re.findall(r"(?<![A-Za-z0-9])[A-Za-z][A-Za-z\.-]{0,5}(?![A-Za-z0-9])", query)
    normalized: list[tuple[str, str]] = []
    for candidate in matches:
        token = candidate.upper()
        if token in US_TICKER_STOPWORDS or token in {"XSHG", "XSHE"}:
            continue
        normalized.append((candidate, token))

    ordered: list[str] = []
    seen: set[str] = set()
    for selector in (
        lambda item: item[0].isupper(),
        lambda item: not item[0].islower(),
        lambda item: True,
    ):
        for candidate, token in normalized:
            if not selector((candidate, token)):
                continue
            if token in seen:
                continue
            seen.add(token)
            ordered.append(token)
    return ordered


def detect_scenario(query: str) -> str:
    text = query or ""
    lower = text.lower()

    if any(keyword in text for keyword in ("选股", "筛选", "推荐股票", "成分股", "挑几只", "选几只", "选出")):
        return "STOCK_PICKER"

    if any(keyword in text for keyword in ("建仓", "止损", "止盈", "仓位", "加仓", "减仓", "网格", "怎么操作")):
        return "TRADING_STRATEGY"

    if any(keyword in text for keyword in ("美股", "道琼斯", "标普", "纳斯达克")):
        return "US_STOCK"

    if any(keyword in lower for keyword in ("nyse", "nasdaq", "dow", "sp500")):
        return "US_STOCK"

    symbol = extract_symbol_token(text)
    if symbol and symbol.startswith("^"):
        return "US_STOCK"
    if symbol and re.fullmatch(r"[A-Z][A-Z\.-]{0,5}", symbol):
        return "US_STOCK"

    if "etf" in lower:
        return "ETF_ANALYZE"

    if symbol and symbol.endswith((".XSHG", ".XSHE")) and infer_cn_instrument_type(symbol) == "ETF":
        return "ETF_ANALYZE"

    if any(keyword in text for keyword in ("大盘", "A股", "股市", "行情", "上证", "深成指", "创业板")) and not symbol:
        return "MARKET_OVERVIEW"

    return "STOCK_ANALYZE"


def guess_market(query: str) -> str:
    return "US" if detect_scenario(query) == "US_STOCK" else "CN"


def extract_position(query: str) -> PositionInput:
    text = query or ""
    shares: Optional[int] = None
    avg_price: Optional[float] = None
    entry_date: Optional[str] = None

    price_match = re.search(r"(?:成本|均价|建仓价|买入价)\s*[:：]?\s*(\d+(?:\.\d+)?)", text)
    if price_match:
        avg_price = float(price_match.group(1))

    if avg_price is None:
        combo_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:元)?\s*(?:建仓|买入)\s*(\d+)\s*(股|手)", text)
        if combo_match:
            avg_price = float(combo_match.group(1))
            count = int(combo_match.group(2))
            shares = count * 100 if combo_match.group(3) == "手" else count

    if shares is None:
        shares_match = re.search(r"(?:持仓|仓位|买了|建仓)\s*(\d+)\s*(股|手)", text)
        if shares_match:
            count = int(shares_match.group(1))
            shares = count * 100 if shares_match.group(2) == "手" else count

    if shares is None:
        fallback_shares = re.search(r"(\d+)\s*(股|手)", text)
        if fallback_shares:
            count = int(fallback_shares.group(1))
            shares = count * 100 if fallback_shares.group(2) == "手" else count

    if avg_price is None:
        fallback_price = re.search(r"(\d+(?:\.\d+)?)\s*(?:元)?\s*(?:成本|附近|位置)", text)
        if fallback_price:
            avg_price = float(fallback_price.group(1))

    date_match = re.search(r"(20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}日?)", text)
    if date_match:
        entry_date = _normalize_date(date_match.group(1))

    return PositionInput(shares=shares, avg_price=avg_price, entry_date=entry_date)


def _normalize_date(raw: str) -> str:
    cleaned = raw.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-").replace(".", "-")
    try:
        value = datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError:
        return raw
    return value.date().isoformat()
