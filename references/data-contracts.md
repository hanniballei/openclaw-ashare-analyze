# Data Contracts

Use this file when you need exact output keys or want to keep fields stable across scenarios.

## 1. Stock-like payloads

The following scripts share the same base shape:

- `scripts/analyze_stock.py`
- `scripts/analyze_etf.py`
- `scripts/trading_strategy.py`
- `scripts/analyze_us_stock.py` for the `stock` section when a specific US ticker is supplied

### Base keys

| Key | Type | Notes |
| --- | --- | --- |
| `scenario` | string | One of `STOCK_ANALYZE`, `ETF_ANALYZE`, `TRADING_STRATEGY`, `US_STOCK` |
| `symbol` | string | Normalized ticker such as `600875.XSHG`, `159206.XSHE`, or `NVDA` |
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
| `billboard` | array | Recent龙虎榜 rows; empty array when unavailable |

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

## 2. ETF-only additions

`scripts/analyze_etf.py` adds:

| Key | Type | Notes |
| --- | --- | --- |
| `etf_details` | object | `tracking_index`, `fund_scale`, `components` |

`components` is an array of:

```json
{
  "symbol": "600000.XSHG",
  "name": "浦发银行",
  "weight": null
}
```

## 3. Market overview payload

`scripts/analyze_market.py` returns:

| Key | Type | Notes |
| --- | --- | --- |
| `scenario` | string | `MARKET_OVERVIEW` |
| `timestamp` | string | Latest available market snapshot timestamp |
| `indices` | object | `shanghai`, `shenzhen`, `chinext` |
| `market_breadth` | object | `up_count`, `down_count`, `flat_count`, `limit_up_count`, `limit_down_count` |
| `sector_performance` | object | `leaders`, `laggards` |
| `northbound_flow` | object | `today_net`, `source` |

Each index summary includes:

```json
{
  "symbol": "000001.XSHG",
  "name": "上证指数",
  "current_price": 0,
  "change_pct": 0,
  "indicators": {
    "daily": {}
  }
}
```

## 4. Trading strategy payload

`scripts/trading_strategy.py` returns the full stock-like payload plus:

| Key | Type | Notes |
| --- | --- | --- |
| `position` | object | Parsed user position |
| `strategy` | object | Action levels and explanation |

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

## 5. Stock picker payload

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
