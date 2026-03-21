# Query Examples

Use this file when you want concrete examples of user phrasing and the matching script.

## STOCK_ANALYZE

- "分析通富微电"
- "600875 现在强不强"
- "亨通光电各项指标是多少"

Run:

```bash
python3 scripts/analyze_stock.py --query "分析通富微电"
```

## ETF_ANALYZE

- "分析 sz159206"
- "159625 适合建仓吗"
- "科创 ETF 现在强不强"

Run:

```bash
python3 scripts/analyze_etf.py --query "159625 适合建仓吗"
```

## MARKET_OVERVIEW

- "今天 A 股走势如何"
- "大盘是不是洗盘"
- "上证和创业板现在是什么状态"

Run:

```bash
python3 scripts/analyze_market.py --query "今天 A 股走势如何"
```

## TRADING_STRATEGY

- "29.3 建仓 200 股今天怎么操作"
- "通富微电成本 29.3 持仓 500 股怎么止损止盈"
- "我 3 月 10 日买了 300 股，现在要不要加仓"

Run:

```bash
python3 scripts/trading_strategy.py --query "通富微电成本 29.3 持仓 500 股怎么止损止盈"
```

## US_STOCK

- "分析纳斯达克"
- "看看 NVDA 和标普"
- "美股现在适合追吗"

Run:

```bash
python3 scripts/analyze_us_stock.py --query "看看 NVDA 和标普"
```

## STOCK_PICKER

- "从 159625 里挑几只强势股"
- "帮我从这个 ETF 成分股里选 10 只"
- "从科创 ETF 里面筛选趋势最好的票"

Run:

```bash
python3 scripts/stock_picker.py --query "从 159625 里挑几只强势股" --top 10
```
