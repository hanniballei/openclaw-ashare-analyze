# Query Examples

Use this file when you want concrete examples of user phrasing and the matching script.

## STOCK_ANALYZE

- "分析通富微电"
- "600875 现在强不强"
- "亨通光电各项指标是多少"
- "说一说下周亨通光电的预测"
- "只要分析亨通光电"

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
- "A股早盘复盘"
- "A股全天复盘"
- "下午a股为什么突然涨起来了"
- "今天全天成交量是多少"

Run:

```bash
python3 scripts/analyze_market.py --query "今天 A 股走势如何"
```

## TRADING_STRATEGY

- "29.3 建仓 200 股今天怎么操作"
- "通富微电成本 29.3 持仓 500 股怎么止损止盈"
- "我 3 月 10 日买了 300 股，现在要不要加仓"
- "亨通光电成本价45.54，给我做一版持仓/减仓/止损方案"
- "已经持有"
- "尾盘是该减仓还是可留仓过周末"

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

## THEME_ANALYZE

- "怎么看光纤板块？"
- "A股中卫星通信的公司有哪些头部企业？"
- "AI、算力、半导体、机器人哪个更强？"
- "卫星通信明天在A股有没有机会？"
- "推荐光纤板块 5 只优质股票"
- "帮我从卫星通信板块里挑 3 只最强的票"
- "推荐航天航空领域的股票"
- "推荐半导体行业的优质股"

Run:

```bash
python3 scripts/analyze_theme.py --query "怎么看光纤板块？" --top 5
```

## EVENT_IMPACT

- "现在美股的卫星通信涨疯了，是否对明天的A股有影响？"
- "海外某个主题大涨，对A股哪些公司受益？"

Run:

```bash
python3 scripts/analyze_us_stock.py --query "现在美股的卫星通信涨疯了"
python3 scripts/analyze_theme.py --query "卫星通信" --top 5
```
