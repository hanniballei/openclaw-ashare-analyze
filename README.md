# ashare-analyze

`ashare-analyze` 是一个面向投资问答场景的金融分析 skill。  
它会拉取市场数据，产出结构化 JSON，再由上层 agent / LLM 组织成最终中文回答。

这份 README 只保留用户真正需要的内容：

- 这个 skill 是做什么的
- 支持哪些场景
- 需要怎么配置
- 应该怎么运行

## 这个 skill 是做什么的

它主要用来回答下面这些问题：

- A 股个股分析：趋势、支撑压力、资金流、基础面
- ETF 分析：走势、关键价位、成分信息
- 大盘概览：上证 / 深成指 / 创业板的结构和节奏
- 板块 / 概念 / 主题分析：强弱、代表股、优质标的
- 持仓与操作：已有仓位怎么观察、止盈、止损、加减仓
- ETF 成分股筛选：从 ETF 里挑强势股
- 美股与美股指数分析：以近 30 个交易日的日线为主
- 跨市场映射：美股事件对 A 股题材或个股的潜在影响

## 支持场景

这个 skill 支持以下核心 `task`：

| 场景 | `--task` |
| --- | --- |
| A 股个股分析 | `stock_analyze` |
| ETF 分析 | `etf_analyze` |
| 大盘概览 | `market_overview` |
| 主题 / 板块分析 | `theme_analyze` |
| 持仓与策略分析 | `trading_strategy` |
| 美股 / 美股指数分析 | `us_stock` |
| ETF 成分股筛选 | `stock_picker` |

## 推荐调用方式

**推荐始终通过统一入口 `run.py` 调用。**

也就是说，推荐使用：

```bash
python3 run.py --task stock_analyze --query "分析通富微电"
```

而不是直接调用内部脚本：

```bash
python3 scripts/analyze_stock.py ...
```

旧的 `scripts/analyze_*.py` 仍然保留，但主要是兼容层。  
如果你是新接入方，只需要记住一个入口：`run.py`。

## 安装依赖

进入 skill 目录后安装依赖：

```bash
cd <skill_root>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

其中 `<skill_root>` 就是这个 skill 所在目录，也就是包含 `README.md`、`SKILL.md` 和 `run.py` 的目录。

## 环境配置

### A 股相关场景

A 股、ETF、大盘、主题、策略、选股场景都依赖 `RQData`。

至少需要配置：

```bash
export RQDATA_PRIMARY_URI='tcp://<your_username>:<your_license_key>@<your_rqdata_host>:<your_rqdata_port>'
```

可选备用连接：

```bash
export RQDATA_BACKUP_USERNAME='<your_backup_username>'
export RQDATA_BACKUP_PASSWORD='<your_backup_license_key>'
export RQDATA_BACKUP_HOST='<your_backup_host>'
export RQDATA_BACKUP_PORT='<your_backup_port>'
```

### 美股场景

美股场景使用 `yfinance`，**不需要额外密钥**。

## 怎么运行

以下命令默认你已经：

```bash
cd <skill_root>
source .venv/bin/activate
```

### A 股个股

```bash
python3 run.py --task stock_analyze --symbol 600875 --query "分析东方电气" --compact
python3 run.py --task stock_analyze --query "亨通光电后面怎么走" --compact
```

### ETF

```bash
python3 run.py --task etf_analyze --symbol 159625 --query "分析绿色电力ETF" --compact
python3 run.py --task etf_analyze --query "ETF159625 适合建仓吗" --compact
```

### 大盘概览

```bash
python3 run.py --task market_overview --query "今天A股走势如何" --compact
python3 run.py --task market_overview --query "上证和创业板现在是什么状态" --compact
```

### 主题 / 板块

```bash
python3 run.py --task theme_analyze --query "怎么看光纤板块" --top 5 --compact
python3 run.py --task theme_analyze --query "推荐航天航空领域的股票" --top 5 --compact
```

### 持仓与策略

```bash
python3 run.py --task trading_strategy --symbol 600875 --query "成本29.3 持仓200股今天怎么操作" --compact
python3 run.py --task trading_strategy --query "我2026-03-10买了300股东方电气，现在要不要加仓" --compact
```

### 美股

```bash
python3 run.py --task us_stock --query "看看 NVDA" --compact
python3 run.py --task us_stock --query "分析纳斯达克" --compact
python3 run.py --task us_stock --query "看看 NVDA 和标普" --compact
```

### ETF 成分股筛选

```bash
python3 run.py --task stock_picker --symbol 159625 --query "从159625里挑几只强势股" --top 3 --compact
python3 run.py --task stock_picker --query "从嘉实国证绿色电力ETF里挑3只强势股" --top 3 --compact
```

## 输出结果说明

这些命令的直接输出是 **JSON**，不是最终给终端用户看的自然语言分析。

你可以把它理解成两层：

- **事实层**：脚本输出的结构化 JSON
- **表达层**：由上层 agent / LLM 把 JSON 组织成自然语言回答

如果你是在终端里直接运行命令，你看到的是事实层。  
如果你是在上层问答系统里使用这个 skill，通常应该让模型读取 JSON 后，再组织成最终中文回答。

## 当前输出重点

### A 股个股 / ETF / 策略

会返回：

- 顶层行情快照
- 多周期指标：`daily` / `4h` / `1h` / `5min`
- 原始 K 线：`candles.daily` / `candles.1h` / `candles.5min`
- 资金流、支撑位、压力位、基础面

默认会把这些原始 bars 一起给上层模型：

- `daily`：最近 60 根
- `1h`：最近 60 根
- `5min`：最近 60 根

### 大盘概览

会返回：

- 上证、深成指、创业板的结构化结果
- 每个指数的 `daily / 1h / 5min` 指标
- 每个指数最近 60 根 `daily / 1h / 5min` 原始 bars
- 北向资金

### 主题 / 板块

会返回两部分：

- `ranking`：前 `top N` 的排序结果
- `representative_stocks`：少量代表股的细粒度快照

为了控制 payload 大小，当前只有前 **2** 个代表股会返回较重的数据：

- `daily / 1h / 5min` 指标
- `daily / 1h / 5min` 原始 K 线

### 美股

美股场景做了轻量化处理，默认返回：

- 最近 **30 个交易日** 的 `daily` 原始 K 线
- `daily` 指标快照
- `daily_summary`

`daily_summary` 会给上层模型一些更容易解释的摘要字段，例如：

- `return_5d`
- `return_10d`
- `return_20d`
- `distance_to_ma20`
- `position_in_30d_range`
- `volume_vs_20d_avg`
- `high_30d`
- `low_30d`

## 相关文件

- skill 规则：`SKILL.md`
- 统一入口：`run.py`
- 数据契约：`references/data-contracts.md`
- 数据源说明：`references/data-sources.md`
- 示例问法：`references/query-examples.md`
