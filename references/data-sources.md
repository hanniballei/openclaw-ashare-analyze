# Data Sources

Use this file when you need source priorities, environment setup, or fallback rules.

## Runtime dependencies

Install the runtime packages from `requirements.txt`.

Main packages:

- `rqdatac`
- `yfinance`
- `akshare`
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
| US price bars | `yfinance.Ticker().history()` | none | Intraday coverage is best-effort |
| Money flow | `akshare.stock_individual_fund_flow_rank()` | none | Uses `今日` and `5日` snapshots |
| 龙虎榜 | `akshare.stock_lhb_detail_em()` | `akshare.stock_lhb_stock_statistic_em()` | Script tolerates missing rows |
| A-share breadth | `akshare.stock_zh_a_spot_em()` | none | Counts positive, negative, and near limit-up / limit-down movers |
| Sector ranking | `akshare.stock_board_industry_name_em()` | `akshare.stock_board_industry_spot_em()` | Returns leaders and laggards |
| 北向资金 | `akshare.stock_hsgt_north_net_flow_in_em()` | `akshare.stock_hsgt_fund_flow_summary_em()` | First available method wins |

## Known limitations

- `rqdatac` does not expose native `4h` bars for A-shares. This skill aggregates every four `60m` bars into one `4h` bar.
- `yfinance` intraday data windows are limited and can be sparse for older periods or certain symbols. When the returned `60m` bars are insufficient, keep the JSON valid but acknowledge the gap in the final answer.
- `akshare` community endpoints change more often than `rqdatac`. The client wrappers therefore use best-effort method detection and return partial data instead of crashing the whole analysis.

## Official references used for this skill

- RiceQuant RQData docs: https://www.ricequant.com/doc/rqdata/python/manual
- RiceQuant index docs: https://www.ricequant.com/doc/rqdata/python/ricequant-index
- yfinance official repository: https://github.com/ranaroussi/yfinance
- AKShare stock docs: https://akshare.akfamily.xyz/data/stock/stock.html
- AKShare quick start: https://akshare.akfamily.xyz/tutorial.html

## Operational guidance

- Treat `rqdatac` as mandatory for China-market scenarios. Do not fake China-market analysis when it is unavailable.
- Treat `akshare` enrichments as optional. Continue if quote, indicator, and fundamentals data are already valid.
- Prefer partial payloads with explicit nulls over dropping keys entirely.
