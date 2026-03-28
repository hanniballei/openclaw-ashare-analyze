---
name: ashare-analyze
description: Live-data financial analysis workflow for China A-shares, theme/concept questions, ETFs, broad-market questions, trading-strategy requests, US equities, and ETF-component screening. Use when a user asks about A股、板块/概念、个股/ETF 代码、大盘走势、持仓操作、美股映射或从 ETF 成分股里选股, and Codex should pull fresh market data with rqdatac/yfinance, then answer in plain language with concrete levels, comparisons, and risk reminders.
---

# A-Share Analyze

## Overview

Use this skill to turn fresh market data into investor-friendly explanations. Most requests map to a single script, but a few are orchestration modes that combine multiple scripts or change the response shape. Pull data first when the question needs market facts, keep JSON as the factual layer, then write the answer in plain language with concrete levels, comparisons, and a short risk note.

## Workflow

1. Classify the request into one data scenario or orchestration mode:
   - `STOCK_ANALYZE`: A-share single-stock questions such as "分析通富微电" or "600875 各项指标是多少"
   - `ETF_ANALYZE`: ETF questions such as "分析 159206" or "ETF159625 适合建仓吗"
   - `MARKET_OVERVIEW`: broad market questions such as "今天 A 股走势如何" or "大盘是不是洗盘"
   - `TRADING_STRATEGY`: position and action questions such as "29.3 建仓 200 股今天怎么操作"
   - `US_STOCK`: US market or US stock questions such as "分析纳斯达克" or "看看 NVDA"
   - `STOCK_PICKER`: screening questions such as "从 159625 里挑几只强势股"
   - `THEME_ANALYZE`: theme / concept / sector questions such as "怎么看光纤板块" or "卫星通信有哪些头部企业"
   - `EVENT_IMPACT`: cross-market mapping questions such as "美股 XX 涨了，对明天 A 股有影响吗"
   - `NEXT_SESSION_OUTLOOK`: next-session / next-week outlook questions such as "明天怎么看" or "下周亨通光电怎么走"
   - `RANK_COMPARE`: ranking / compare / reorganize questions such as "请排序" or "帮我整理一版"
   - Concept-only questions such as "AIDC 是什么意思" do not require any market script.
2. Normalize the symbol or theme before running any scenario script.
   - Accept `600875`, `600875.XSHG`, `sz159206`, ETF codes, Chinese names, and common index aliases.
   - For theme questions, prefer one theme per script call.
   - If the user compares multiple themes, run `scripts/analyze_theme.py` once per theme and compare the returned payloads side by side.
   - Prefer explicit `--symbol` when the user already supplied a clean code.
3. Check runtime prerequisites before claiming anything.
   - A-share, ETF, market overview, trading strategy, stock picker, and theme analysis require `rqdatac`.
   - US stock analysis requires `yfinance`.
   - `EVENT_IMPACT` usually requires both a US-side script and one or more China-side scripts.
4. Run the matching script or orchestration and read the JSON.
   - `python3 scripts/analyze_stock.py --query "分析通富微电"`
   - `python3 scripts/analyze_etf.py --symbol 159206`
   - `python3 scripts/analyze_market.py --query "今天 A 股走势如何"`
   - `python3 scripts/trading_strategy.py --query "29.3 建仓 200 股的通富微电今天怎么操作"`
   - `python3 scripts/analyze_us_stock.py --query "看看纳斯达克和 NVDA"`
   - `python3 scripts/stock_picker.py --query "从 159625 里挑几只强势股" --top 10`
   - `python3 scripts/analyze_theme.py --query "怎么看光纤板块" --top 5`
   - For `EVENT_IMPACT`:
     1. Run `scripts/analyze_us_stock.py` to confirm the overseas move or event backdrop.
     2. Map the event to A-share themes or related stocks using industry / concept knowledge.
     3. Run `scripts/analyze_theme.py` or `scripts/analyze_stock.py` on the mapped A-share side.
     4. Explain the chain as "海外事件 -> A 股映射逻辑 -> 当前技术面/资金面 -> 操作提醒".
     5. Explicitly say the mapping is based on industry correlation, not guaranteed causality.
5. Translate JSON into a human answer.
   - Lead with the conclusion in plain language.
   - Quote the most decision-relevant numbers: current price,涨跌幅,支撑位,压力位,止损位,止盈位.
   - Explain indicator meaning without jargon stacking.
   - Separate hard data from LLM inference when you explain causes, outlooks, or cross-market mapping.
   - State uncertainty when fields are missing.
   - End with a short risk reminder.
6. Before re-running scripts on a short follow-up, check the multi-turn rules below and reuse the previous context when it is clearly the same topic.

## Response Rules

- Pull fresh data before commenting on direction, setup, or operations.
- Keep the JSON source-of-truth. Do not invent values that are missing.
- Prefer the daily timeframe for the headline view, then use `4h`, `1h`, and `5min` to explain shorter-term rhythm.
- Mention the exact level whenever giving an action recommendation.
- Keep the language understandable for non-professional investors.
- Treat all strategy output as educational analysis, not guaranteed returns.

### Review and attribution mode

When the user asks "早盘复盘"、"全天复盘"、"为什么突然涨起来了"、"为什么跳水":

1. Run `scripts/analyze_market.py`.
2. Use index structure, northbound flow, and intraday rhythm to explain what changed.
3. If you mention likely drivers, label them as "更可能的原因" or "大概率与...有关", not hard causality.
4. If the explanation depends on one or two leading themes, say that clearly instead of pretending you observed the whole market breadth.

### Outlook mode

When the user asks "下周/明天怎么看"、"预测"、"展望":

1. Run the normal data script for the underlying scenario.
2. Reorganize the answer into:
   - current position
   - key support / resistance or observation points
   - scenario analysis: breakout / hold / breakdown
   - separate actions for holders versus empty-position users
3. Do not give precise percentage forecasts. Prefer price ranges, trigger levels, and conditions.
4. Explicitly say the outlook is based on current technical structure and may change intraday.

### Compare and ranking mode

When the user asks to compare, rank, or reorganize:

1. Default ranking standard is overall strength: technicals + flow + fundamentals. If the user gave a standard, use theirs.
2. Output as a numbered list with each item's key metrics and ranking reason.
3. If comparing more than three names or plans, give a one-sentence summary first, then the detailed ranking.
4. Do not give a naked conclusion. Keep the underlying data or rationale visible.

### Concept explanation mode

When the user only asks what a concept means, such as "AIDC 是什么意思" or "什么是 CDN":

1. Do not call any market data script.
2. Answer directly with LLM knowledge.
3. If helpful, add one short A-share connection sentence such as related themes or representative stocks.
4. Do not force a technical-analysis section onto a pure concept explanation request.

## Multi-turn Rules

For short follow-up messages such as "第二种"、"请排序"、"已经持有"、"只看这个", apply these rules before deciding to rerun scripts:

1. Topic inheritance:
   - If the new message contains no new ticker, theme, or scenario keyword, inherit the previous subject and scenario by default.
2. Intent inference:
   - "第 N 种" / "选 N" -> expand the Nth option from the previous answer.
   - "请排序" / "排个序" -> rank the names or plans already mentioned.
   - "帮我整理一版" -> rewrite the previous answer in a cleaner, more structured format.
   - "已经持有" / "我已经买了" -> switch to `TRADING_STRATEGY` and inherit the previously discussed stock when clear.
   - "只要/只看 XXX" -> filter the previous multi-name answer down to the requested name.
3. Data reuse:
   - If the previous payload is still fresh within roughly five minutes and the topic did not change, reuse it instead of blindly rerunning the script.
4. Clarify when ambiguous:
   - If the short follow-up could point to multiple earlier names or plans, ask one short confirmation question before acting.

## Script Map

### Single-stock and ETF work

- Use `scripts/analyze_stock.py` for A-shares.
- Use `scripts/analyze_etf.py` for ETFs.
- Both scripts output the same core market structure: quote snapshot, multi-timeframe indicators, support/resistance, and flow data.
- Read [references/data-contracts.md](references/data-contracts.md) when you need exact field names.

### Market-wide work

- Use `scripts/analyze_market.py` for Shanghai, Shenzhen, and ChiNext headline conditions.
- Read [references/data-sources.md](references/data-sources.md) when you need to check where index and northbound data come from.

### Theme and concept work

- Use `scripts/analyze_theme.py` for 板块 / 概念 / 主题 / 赛道 questions.
- The script returns a theme-level payload plus representative A-share names with daily indicators and money-flow snapshots.
- If the user compares several themes, run one theme-analysis call per theme, then compare.
- If direct `rqdatac` theme matching fails, say so clearly and only fall back to manual representative-stock mapping when the target theme is still obvious.

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

### Cross-market mapping work

- `EVENT_IMPACT` is not a dedicated script. It is a workflow that combines `analyze_us_stock.py` with one or more A-share scripts.
- Prefer `scripts/analyze_theme.py` when the mapping points to a whole theme, and `scripts/analyze_stock.py` when the user already named a specific A-share target.

## References

- Read [references/data-contracts.md](references/data-contracts.md) for output schemas.
- Read [references/data-sources.md](references/data-sources.md) for environment variables, source priorities, and fallbacks.
- Read [references/query-examples.md](references/query-examples.md) for trigger examples and phrasing patterns.

## Failure Handling

- Surface configuration failures clearly.
  - Missing `RQDATA_PRIMARY_URI`: tell the user the A-share data connection is not configured.
  - Missing Python dependency: tell the user which package is missing and which script needs it.
- When direct theme lookup fails:
  - Say the theme was not matched in `rqdatac`.
  - If the user intent is still clear, fall back to a small representative-stock set and label it as a manual mapping rather than a native theme payload.
- Return partial analysis only when the missing field is non-core.
  - Example: continue without龙虎榜 if quote and indicator data are available.
  - Example: do not continue stock analysis if no price bars were fetched.
- Prefer explicit "未获取到" or "暂缺" wording over vague hedging.
