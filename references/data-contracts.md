# Data Contracts

Use this file when you need exact output keys or want to keep fields stable across scenarios.

## 1. China stock-like payloads

The following scripts share the same China-market base shape:

- `scripts/analyze_stock.py`
- `scripts/analyze_etf.py`
- `scripts/trading_strategy.py`

### Base keys

| Key | Type | Notes |
| --- | --- | --- |
| `scenario` | string | One of `STOCK_ANALYZE`, `ETF_ANALYZE`, `TRADING_STRATEGY` |
| `symbol` | string | Normalized ticker such as `600875.XSHG` or `159206.XSHE` |
| `name` | string | Instrument display name |
| `timestamp` | string | Timestamp from the latest bar |
| `current_price` | number | Latest close |
| `change_pct` | number or null | Prefer `prev_close`; otherwise use previous bar close |
| `open` | number | Latest bar open |
| `high` | number | Latest bar high |
| `low` | number | Latest bar low |
| `prev_close` | number or null | Latest reference close |
| `volume` | number | Latest bar volume |
| `amount` | number | Latest bar turnover |
| `turnover_rate` | number or null | Optional; may be null when source is missing |
| `indicators` | object | `daily`, `4h`, `1h`, `5min` |
| `price_levels` | object | `support`, `resistance` |
| `fundamentals` | object | Valuation, profitability, and growth |
| `money_flow` | object | `today_net`, `5day_net`, `source` |

### Indicator section

```json
{
  "daily": {
    "ma": {"ma5": 0, "ma10": 0, "ma20": 0, "ma60": 0},
    "macd": {"dif": 0, "dea": 0, "histogram": 0},
    "kdj": {"k": 0, "d": 0, "j": 0},
    "rsi": {"rsi6": 0, "rsi12": 0, "rsi24": 0},
    "bollinger": {"upper": 0, "middle": 0, "lower": 0}
  }
}
```

### Fundamentals section

```json
{
  "pe_ttm": null,
  "pb": null,
  "market_cap": null,
  "roe_ttm": null,
  "revenue_growth": null,
  "profit_growth": null
}
```

## 2. Stock-only additions

`scripts/analyze_stock.py` adds:

| Key | Type | Notes |
| --- | --- | --- |
| `billboard` | array | Recent龙虎榜 detail rows |

## 3. ETF-only additions

`scripts/analyze_etf.py` adds:

| Key | Type | Notes |
| --- | --- | --- |
| `etf_details` | object | `tracking_index`, `fund_scale`, `components` |

ETF payloads do not include `billboard`.

`components` is an array of:

```json
{
  "symbol": "600000.XSHG",
  "name": "浦发银行",
  "weight": null
}
```

## 4. Market overview payload

`scripts/analyze_market.py` returns:

| Key | Type | Notes |
| --- | --- | --- |
| `scenario` | string | `MARKET_OVERVIEW` |
| `timestamp` | string | Latest available market snapshot timestamp |
| `indices` | object | `shanghai`, `shenzhen`, `chinext` |
| `northbound_flow` | object | `today_net`, `source` |

Each index summary includes:

```json
{
  "symbol": "000001.XSHG",
  "name": "上证指数",
  "current_price": 0,
  "change_pct": 0,
  "indicators": {
    "daily": {},
    "1h": {},
    "5min": {}
  }
}
```

## 5. Trading strategy payload

`scripts/trading_strategy.py` returns the full stock-like payload plus:

| Key | Type | Notes |
| --- | --- | --- |
| `position` | object | Parsed user position |
| `strategy` | object | Action levels and explanation |

Trading-strategy payloads also include `billboard`.

Strategy shape:

```json
{
  "entry_levels": [0, 0],
  "add_levels": [0, 0],
  "stop_loss": 0,
  "take_profit": [0, 0],
  "advice": "..."
}
```

## 6. Theme analyze payload

`scripts/analyze_theme.py` returns:

| Key | Type | Notes |
| --- | --- | --- |
| `scenario` | string | `THEME_ANALYZE` |
| `query` | string | Original user query |
| `theme` | string | User-facing theme extracted from the query |
| `resolved_theme` | string | Canonical theme / concept name matched in `rqdatac` |
| `theme_source` | string | Usually `concept` or `industry` |
| `timestamp` | string | Latest timestamp among representative stocks |
| `selection_basis` | object | Theme ranking parameters and score components |
| `ranking` | array | Top-N ranked theme stocks with score and reasons |
| `representative_stocks` | array | A small representative-stock set for the theme |
| `theme_summary` | object | Aggregate strength and flow summary |

Selection basis shape:

```json
{
  "bars": 90,
  "top": 5,
  "component_limit": 25,
  "score_components": [
    "price_above_ma20",
    "price_above_ma60",
    "positive_macd",
    "healthy_rsi",
    "positive_revenue_growth",
    "positive_profit_growth"
  ]
}
```

Each ranking item includes:

```json
{
  "rank": 1,
  "symbol": "600487.XSHG",
  "name": "亨通光电",
  "score": 100.0,
  "current_price": 0,
  "change_pct": 0,
  "ma20": 0,
  "ma60": 0,
  "macd_histogram": 0,
  "revenue_growth": 0,
  "profit_growth": 0,
  "today_net_flow": 0,
  "5day_net_flow": 0,
  "reasons": ["站上 MA20", "利润增速为正"]
}
```

Each representative stock includes:

```json
{
  "symbol": "600487.XSHG",
  "name": "亨通光电",
  "timestamp": "2026-03-28 15:00:00",
  "current_price": 0,
  "change_pct": 0,
  "indicators": {
    "daily": {}
  },
  "money_flow": {
    "today_net": 0,
    "5day_net": 0,
    "source": "rqdata"
  }
}
```

Theme summary shape:

```json
{
  "avg_change_pct": 0,
  "up_count": 0,
  "down_count": 0,
  "flat_count": 0,
  "total_net_flow": 0
}
```

## 7. Stock picker payload

`scripts/stock_picker.py` returns:

| Key | Type | Notes |
| --- | --- | --- |
| `scenario` | string | `STOCK_PICKER` |
| `etf` | object | ETF symbol and name |
| `selection_basis` | object | Scoring factors and limits |
| `ranking` | array | Sorted descending by score |

Each ranking item includes:

```json
{
  "rank": 1,
  "symbol": "002475.XSHE",
  "name": "立讯精密",
  "score": 82.5,
  "current_price": 0,
  "change_pct": 0,
  "ma20": 0,
  "ma60": 0,
  "macd_histogram": 0,
  "revenue_growth": null,
  "profit_growth": null,
  "reasons": ["站上 MA20", "盈利增速为正"]
}
```

## 8. US stock payload

`scripts/analyze_us_stock.py` returns:

| Key | Type | Notes |
| --- | --- | --- |
| `scenario` | string | `US_STOCK` |
| `query` | string | Original user query |
| `timestamp` | string | Timestamp from the Nasdaq index payload |
| `indices` | object | `道琼斯`, `标普`, `纳斯达克` |
| `stock` | object | Present only when a specific US ticker is resolved |

The optional `stock` object includes quote, indicators, price levels, and fundamentals, but does not include China-only `money_flow` or `billboard` fields.
