# ashare-analyze

这是 `ashare-analyze` skill 的使用说明文档。  
skill 本体定义位于 [SKILL.md](/root/hannibal/ashare-analyze/ashare-skill/ashare-analyze/SKILL.md)，本文件主要面向使用者，说明这个 skill 能做什么、如何安装、如何配置和如何运行。

## 目录说明

```text
ashare-analyze/
├── README.md
├── SKILL.md
├── agents/
│   └── openai.yaml
├── requirements.txt
├── references/
│   ├── data-contracts.md
│   ├── data-sources.md
│   └── query-examples.md
├── scripts/
│   ├── analyze_stock.py
│   ├── analyze_etf.py
│   ├── analyze_market.py
│   ├── trading_strategy.py
│   ├── analyze_us_stock.py
│   ├── stock_picker.py
│   └── common/
└── tests/                 # 本地验证用，可选
```

## Skill 目标

`ashare-analyze` 是一个面向金融分析问答的 skill，核心用途是：

- 对 A 股个股做实时技术面和基础面分析
- 对 ETF 做走势、价位和成分股分析
- 对 A 股大盘做概览分析
- 对持仓和操作问题给出策略化价位建议
- 对美股和三大美指做分析
- 从 ETF 成分股中进行选股和排序

脚本层输出的是结构化 JSON，供上层模型进一步组织成自然语言回答。

## 快速开始

如果你只是想尽快用起来，按下面顺序操作：

1. 创建并激活本地 Python 环境
2. 安装 `requirements.txt`
3. 配置 `RQDATA_*` 环境变量
4. 运行对应场景脚本
5. 读取 JSON 输出，或交给上层模型组织成自然语言回答

## 支持场景

- `STOCK_ANALYZE`
- `ETF_ANALYZE`
- `MARKET_OVERVIEW`
- `TRADING_STRATEGY`
- `US_STOCK`
- `STOCK_PICKER`

字段契约见：

- [references/data-contracts.md](/root/hannibal/ashare-analyze/ashare-skill/ashare-analyze/references/data-contracts.md)

数据源和环境变量见：

- [references/data-sources.md](/root/hannibal/ashare-analyze/ashare-skill/ashare-analyze/references/data-sources.md)

示例问法见：

- [references/query-examples.md](/root/hannibal/ashare-analyze/ashare-skill/ashare-analyze/references/query-examples.md)

## 本地安装

进入当前 skill 目录后创建本地虚拟环境并安装依赖：

```bash
cd /root/hannibal/ashare-analyze/ashare-skill/ashare-analyze
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 环境变量

### A 股相关场景必须

需要提前配置 RQData：

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

如果你的部署方式不是通过环境变量注入，也可以把这些值写入你自己的启动脚本或服务器配置系统中。关键是脚本运行时这些变量必须可见。

### 美股场景

- `yfinance` 无需额外密钥

### 补充数据源

- `akshare` 无需额外密钥

## 常用运行命令

在以下命令前，先执行：

```bash
cd /root/hannibal/ashare-analyze/ashare-skill/ashare-analyze
source .venv/bin/activate
```

### 个股分析

```bash
python scripts/analyze_stock.py --query "600875" --compact
python scripts/analyze_stock.py --query "分析东方电气" --compact
python scripts/analyze_stock.py --query "亨通光电后面怎么走" --compact
```

### ETF 分析

```bash
python scripts/analyze_etf.py --query "159625" --compact
python scripts/analyze_etf.py --query "嘉实国证绿色电力ETF" --compact
python scripts/analyze_etf.py --query "ETF159625 适合建仓吗" --compact
```

### 大盘概览

```bash
python scripts/analyze_market.py --query "今天A股走势如何" --compact
python scripts/analyze_market.py --query "大盘是不是洗盘" --compact
python scripts/analyze_market.py --query "上证和创业板现在是什么状态" --compact
```

### 交易策略

```bash
python scripts/trading_strategy.py --query "600875 成本29.3 持仓200股今天怎么操作" --compact
python scripts/trading_strategy.py --query "东方电气成本35.8 持仓5手怎么止损止盈" --compact
python scripts/trading_strategy.py --query "我2026-03-10买了300股东方电气，现在要不要加仓" --compact
```

### 美股分析

```bash
python scripts/analyze_us_stock.py --query "NVDA" --compact
python scripts/analyze_us_stock.py --query "看看 NVDA 和标普" --compact
python scripts/analyze_us_stock.py --query "分析纳斯达克" --compact
```

### 选股筛选

```bash
python scripts/stock_picker.py --query "从159625里挑几只强势股" --top 3 --compact
python scripts/stock_picker.py --query "从嘉实国证绿色电力ETF里挑3只强势股" --top 3 --compact
```

## 输出说明

这些脚本的直接输出是 JSON，而不是最终面向投资者的自然语言结论。

- 如果你直接在终端运行脚本，看到的是结构化 JSON
- 如果你在上层 agent / LLM 中使用这个 skill，通常应当由模型基于 JSON 再组织成最终中文分析

不同场景的 JSON 形态略有区别：

- 个股、ETF、交易策略、美股分析：以单标的分析字段为主
- 大盘概览：以指数、市场情绪、板块、北向资金为主
- 选股筛选：以排序结果和打分理由为主

详细字段请看：

- [references/data-contracts.md](/root/hannibal/ashare-analyze/ashare-skill/ashare-analyze/references/data-contracts.md)

## 测试与校验

### Skill 结构校验

```bash
python3 /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py /root/hannibal/ashare-analyze/ashare-skill/ashare-analyze
```

### 单元测试

```bash
cd /root/hannibal/ashare-analyze/ashare-skill/ashare-analyze
source .venv/bin/activate
python -m unittest discover tests
```

### 编译检查

```bash
cd /root/hannibal/ashare-analyze/ashare-skill/ashare-analyze
source .venv/bin/activate
python -m compileall .
```

## 当前测试状态

当前版本已经完成以下验证：

- skill 结构校验通过
- 单元测试通过
- 6 个主场景全部实测通过
- 扩展输入回归通过

扩展输入覆盖了：

- 中文股票名称问法
- 带自然语言前后缀的股票问法
- ETF 中文名问法
- ETF 策略式问法
- 市场别名问法
- 美股组合问法
- 按 ETF 名称进行选股筛选

## 已知限制

- `akshare` 作为补充数据源，速度和稳定性弱于 `rqdatac`，个别资金流、龙虎榜、板块字段可能为空或偏慢
- 高歧义中文简称仍可能需要进一步做 disambiguation
- 当前输出以 JSON 为核心事实层，上层模型仍需负责把 JSON 组织成自然语言分析

## 对用户的建议

- 如果你是第一次部署，先跑 `analyze_stock.py` 和 `analyze_market.py` 做连通性检查
- 如果你主要做 A 股分析，优先确认 `RQDATA_PRIMARY_URI` 是否生效
- 如果你主要做美股分析，只要 Python 依赖安装完整即可，不依赖 RQData
- 如果你要把这个 skill 接到上层问答系统，建议让上层模型把 JSON 转成自然语言，不要直接把 JSON 原样展示给终端用户

## 相关文件

- Skill 定义：
  [SKILL.md](/root/hannibal/ashare-analyze/ashare-skill/ashare-analyze/SKILL.md)
- 设计文档：
  [../docs/plans/2026-03-21-ashare-analyze-skill-design.md](/root/hannibal/ashare-analyze/ashare-skill/docs/plans/2026-03-21-ashare-analyze-skill-design.md)
- 数据契约：
  [references/data-contracts.md](/root/hannibal/ashare-analyze/ashare-skill/ashare-analyze/references/data-contracts.md)
- 数据源说明：
  [references/data-sources.md](/root/hannibal/ashare-analyze/ashare-skill/ashare-analyze/references/data-sources.md)
- 示例问法：
  [references/query-examples.md](/root/hannibal/ashare-analyze/ashare-skill/ashare-analyze/references/query-examples.md)
