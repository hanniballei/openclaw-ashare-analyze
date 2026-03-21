---
name: ashare-analyze
description: Live-data financial analysis workflow for China A-shares, ETFs, broad-market questions, trading-strategy requests, US equities, and ETF-component screening. Use when a user asks about A股、个股/ETF 代码、大盘走势、建仓/止损/止盈、美股指数或从 ETF 成分股里选股, and Codex should pull fresh market data with rqdatac, yfinance, and akshare, compute indicators, then answer in plain language with concrete price levels and risk reminders.
---

# A-Share Analyze

## Overview

Use this skill to turn fresh market data into investor-friendly explanations. Pull data first, keep the JSON factual, then write the answer in plain language with concrete levels and a short risk note.

## Workflow

1. Classify the request into one of six scenarios:
   - `STOCK_ANALYZE`: A-share single-stock questions such as "分析通富微电" or "600875 各项指标是多少"
   - `ETF_ANALYZE`: ETF questions such as "分析 159206" or "ETF159625 适合建仓吗"
   - `MARKET_OVERVIEW`: broad market questions such as "今天 A 股走势如何" or "大盘是不是洗盘"
   - `TRADING_STRATEGY`: position and action questions such as "29.3 建仓 200 股今天怎么操作"
   - `US_STOCK`: US market or US stock questions such as "分析纳斯达克" or "看看 NVDA"
   - `STOCK_PICKER`: screening questions such as "从 159625 里挑几只强势股"
2. Normalize the symbol before running any scenario script.
   - Accept `600875`, `600875.XSHG`, `sz159206`, ETF codes, Chinese names, and common index aliases.
   - Prefer explicit `--symbol` when the user already supplied a clean code.
3. Check runtime prerequisites before claiming anything.
   - A-share, ETF, market overview, trading strategy, and stock picker require `rqdatac`.
   - US stock analysis requires `yfinance`.
   - Money-flow,龙虎榜,北向资金, and sector breadth rely on `akshare` as a best-effort supplement.
4. Run the matching script and read the JSON.
   - `python3 scripts/analyze_stock.py --query "分析通富微电"`
   - `python3 scripts/analyze_etf.py --symbol 159206`
   - `python3 scripts/analyze_market.py --query "今天 A 股走势如何"`
   - `python3 scripts/trading_strategy.py --query "29.3 建仓 200 股的通富微电今天怎么操作"`
   - `python3 scripts/analyze_us_stock.py --query "看看纳斯达克和 NVDA"`
   - `python3 scripts/stock_picker.py --query "从 159625 里挑几只强势股" --top 10`
5. Translate JSON into a human answer.
   - Lead with the conclusion in plain language.
   - Quote the most decision-relevant numbers: current price,涨跌幅,支撑位,压力位,止损位,止盈位.
   - Explain indicator meaning without jargon stacking.
   - State uncertainty when fields are missing.
   - End with a short risk reminder.

## Response Rules

- Pull fresh data before commenting on direction, setup, or operations.
- Keep the JSON source-of-truth. Do not invent values that are missing.
- Prefer the daily timeframe for the headline view, then use `4h`, `1h`, and `5min` to explain shorter-term rhythm.
- Mention the exact level whenever giving an action recommendation.
- Keep the language understandable for non-professional investors.
- Treat all strategy output as educational analysis, not guaranteed returns.

## Script Map

### Single-stock and ETF work

- Use `scripts/analyze_stock.py` for A-shares.
- Use `scripts/analyze_etf.py` for ETFs.
- Both scripts output the same core market structure: quote snapshot, multi-timeframe indicators, support/resistance, and flow data.
- Read [references/data-contracts.md](references/data-contracts.md) when you need exact field names.

### Market-wide work

- Use `scripts/analyze_market.py` for Shanghai, Shenzhen, and ChiNext headline conditions.
- Read [references/data-sources.md](references/data-sources.md) when you need to check where breadth, sectors, or northbound flow come from.

### Position and action work

- Use `scripts/trading_strategy.py` when the user asks what to do with an existing or planned position.
- Let the script parse share count, average cost, and entry date from the user query when possible.
- If the user gave incomplete position info, state the missing part before overcommitting.

### US market work

- Use `scripts/analyze_us_stock.py` for US indices and US single names.
- Expect `yfinance` intraday data limitations; when intraday bars are sparse, say so instead of pretending the signal is complete.

### Screening work

- Use `scripts/stock_picker.py` for ETF-component ranking.
- Keep the ranking transparent: price trend, momentum, and growth metrics drive the score.
- If ETF components cannot be resolved, say that explicitly and ask for a clearer ETF or index identifier.

## References

- Read [references/data-contracts.md](references/data-contracts.md) for output schemas.
- Read [references/data-sources.md](references/data-sources.md) for environment variables, source priorities, and fallbacks.
- Read [references/query-examples.md](references/query-examples.md) for trigger examples and phrasing patterns.

## Failure Handling

- Surface configuration failures clearly.
  - Missing `RQDATA_PRIMARY_URI`: tell the user the A-share data connection is not configured.
  - Missing Python dependency: tell the user which package is missing and which script needs it.
- Return partial analysis only when the missing field is non-core.
  - Example: continue without龙虎榜 if quote and indicator data are available.
  - Example: do not continue stock analysis if no price bars were fetched.
- Prefer explicit "未获取到" or "暂缺" wording over vague hedging.
