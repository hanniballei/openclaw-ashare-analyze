# Data Sources

Use this file when you need source priorities, environment setup, or fallback rules.

## Runtime dependencies

Install the runtime packages from `requirements.txt`.

Main packages:

- `rqdatac`
- `yfinance`
- `python-dotenv`

The helper scripts in `scripts/common/` are lazy-loading. Importing them does not require every data package, but executing a source-specific fetch path does.

## Environment variables

### RQData

Set the primary connection URI:

```bash
export RQDATA_PRIMARY_URI='tcp://license:your_license_key@rqdatad-pro.ricequant.com:16011'
```

Optional backup credentials:

```bash
export RQDATA_BACKUP_USERNAME='license'
export RQDATA_BACKUP_PASSWORD='your_backup_license_key'
export RQDATA_BACKUP_HOST='rqdatad-pro.ricequant.com'
export RQDATA_BACKUP_PORT='16011'
```

`.env` is supported as a convenience layer through `python-dotenv`.

## Source priority

| Data family | Primary | Secondary | Notes |
| --- | --- | --- | --- |
| A-share price bars | `rqdatac.get_price()` | none | Required for stock, ETF, strategy, and market scripts |
| ETF metadata | `rqdatac.instruments()` | `rqdatac.index_components()` | Components depend on whether the tracking index can be resolved |
| A-share fundamentals | `rqdatac.get_factor()` | none | Script fetches one factor at a time to keep parsing simple |
| Money flow | `rqdatac.get_capital_flow()` | none | Mapped to `today_net` and rolling `5day_net` |
| 龙虎榜 | `rqdatac.get_abnormal_stocks_detail()` | none | Uses detail rows to expose date, reason, amount, and trader |
| 北向资金 | `rqdatac.current_stock_connect_quota()` | `rqdatac.get_stock_connect_quota()` | Uses `hk_to_sh` + `hk_to_sz` buy/sell turnover delta |
| US price bars | `yfinance.Ticker().history()` | none | Intraday coverage is best-effort |

## Known limitations

- `rqdatac` does not expose native `4h` bars for A-shares. This skill aggregates every four `60m` bars into one `4h` bar.
- `rqdatac` does not provide direct market-breadth or sector-ranking endpoints in the shape this skill previously used, so those fields were removed from the market overview payload.
- `yfinance` intraday data windows are limited and can be sparse for older periods or certain symbols. When the returned `60m` bars are insufficient, keep the JSON valid but acknowledge the gap in the final answer.

## Official references used for this skill

- RiceQuant RQData docs: https://www.ricequant.com/doc/rqdata/python/manual
- RiceQuant index docs: https://www.ricequant.com/doc/rqdata/python/ricequant-index
- yfinance official repository: https://github.com/ranaroussi/yfinance

## Operational guidance

- Treat `rqdatac` as mandatory for China-market scenarios. Do not fake China-market analysis when it is unavailable.
- Prefer partial payloads with explicit nulls over dropping keys entirely.
