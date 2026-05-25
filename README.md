# Quant Platform · A 股量化交易分析平台

> 当前仓库为 **项目骨架（v0.1）**，仅包含目录结构、基础配置、最小可运行入口与 Docker 编排，
> 不包含任何具体业务逻辑。后续按"数据 → 指标 → 策略 → 回测 → 可视化 → AI"路径迭代。

---

## 一、项目目标

打造一个**自主可控**的 A 股量化交易分析平台，覆盖完整链路：

1. **数据接入**：A 股行情、基本面、资金流向、财报等数据的拉取、清洗、存储与缓存。
2. **指标 / 因子计算**：技术指标、基本面因子、自定义因子的批量计算与持久化。
3. **策略开发**：以统一接口编写策略，输出交易信号。
4. **回测评估**：自研轻量回测引擎给出收益、回撤、夏普等绩效指标。
5. **可视化分析**：K 线、指标叠加、回测曲线、持仓与信号标注等图表展示。
6. **AI 增强（预留）**：大模型选股、新闻情绪分析、自动化因子挖掘等。

---

## 二、技术栈

| 分层 | 选型 | 说明 |
| --- | --- | --- |
| 前端 | Next.js (App Router) + TypeScript + TailwindCSS | 后续接入 ECharts 或 TradingView Lightweight Charts |
| 后端 | Python 3.11 + FastAPI + Pydantic v2 | 提供 REST API |
| ORM | SQLAlchemy 2.x + PyMySQL | |
| 数据计算 | pandas + numpy | |
| 数据源 | akshare（首发）→ tushare（兼容） | 通过统一 `DataSource` 抽象切换 |
| 数据库 | MySQL 8.0 | 行情与业务数据存储 |
| 缓存 | Redis 7 | 行情/因子热点缓存、限流、任务状态 |
| 任务调度 | APScheduler（首发）→ Celery（扩展） | 见 `backend/app/tasks/` |
| 回测 | 自研轻量引擎 → Backtrader 适配（扩展） | 见 `backend/app/backtest/` |
| 部署 | Docker Compose | 一键拉起 mysql / redis / backend / frontend |
| 包管理 | 前端 `pnpm`（via corepack）；后端 `pip` | |

---

## 三、目录结构

```text
quant-platform/
├── backend/                       # FastAPI 后端
│   ├── app/
│   │   ├── main.py                # FastAPI 入口、CORS、路由挂载
│   │   ├── api/                   # HTTP 路由层（按业务域拆分）
│   │   ├── core/                  # 配置 / 数据库 / Redis / 公共依赖
│   │   ├── models/                # SQLAlchemy ORM 模型
│   │   ├── schemas/               # Pydantic 数据契约（入参 / 出参）
│   │   ├── services/              # 业务用例编排（API 层调用此处）
│   │   ├── data/                  # 数据接入层（akshare / tushare 适配）
│   │   ├── indicators/            # 技术 / 基本面指标计算
│   │   ├── strategy/              # 策略基类与具体策略
│   │   ├── backtest/              # 回测引擎（自研 + Backtrader 适配预留）
│   │   ├── tasks/                 # APScheduler 任务（预留 Celery）
│   │   └── ai/                    # AI 能力层（预留）
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                      # Next.js 前端
│   ├── app/                       # App Router 页面
│   ├── components/                # 业务 / 通用组件
│   ├── lib/                       # API 封装、工具方法
│   ├── types/                     # 全局类型定义
│   ├── package.json
│   ├── Dockerfile                 # 生产构建（standalone 输出）
│   ├── Dockerfile.dev             # 本地开发用：pnpm dev + 热重载
│   └── .env.example
│
├── docker-compose.yml             # 一键编排 mysql + redis + backend + frontend
├── README.md
└── .gitignore
```

各目录职责简述：

- **`backend/app/api`**：仅做参数校验与 HTTP 协议适配，业务逻辑下沉到 `services/`。
- **`backend/app/core`**：放置跨模块的基础设施，如 `config.py`、`database.py`、`redis.py`。
- **`backend/app/data`**：所有"外部数据源 → DataFrame"的入口，统一标准列名与异常处理。
- **`backend/app/indicators`**：纯计算函数，输入输出均为 `pandas` 对象，便于在策略 / 回测 / 服务中复用。
- **`backend/app/strategy`**：策略只产生信号，不直接下单，便于复用到回测与未来实盘。
- **`backend/app/backtest`**：事件驱动回测主循环、撮合、组合、绩效指标。
- **`backend/app/tasks`**：定时任务（行情同步、因子刷新等），未来切到 Celery 时只增不改。
- **`backend/app/ai`**：大模型相关能力的统一封装，向上暴露 Service，向下抽象不同 Provider。
- **`frontend/app`**：Next.js 页面与路由。
- **`frontend/components`**：图表、表格、表单等可复用组件。
- **`frontend/lib`**：API 客户端、格式化函数、hooks 等。
- **`frontend/types`**：与后端 schemas 对齐的 TS 类型。

---

## 四、启动方式

### 4.1 前置依赖

- Docker Desktop（推荐，唯一硬性依赖）
- 仅在不依赖 Docker、想原生跑前端时才需要：Node.js 20+ 与 `pnpm`（`corepack enable && corepack prepare pnpm@latest --activate`）
- 仅在不依赖 Docker、想原生跑后端时才需要：Python 3.11+

### 4.2 准备环境变量

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

默认凭证（与 `docker-compose.yml` 一致，无需修改即可跑通）：

| 项 | 值 |
| --- | --- |
| MySQL 数据库名 | `quant_platform` |
| MySQL 用户名 | `quant_user` |
| MySQL 密码 | `quant_password` |
| MySQL 端口（宿主机） | `3306` |
| Redis 端口（宿主机） | `6379` |
| 后端端口 | `8000` |
| 前端端口 | `3000` |

> 容器之间通过服务名 `mysql` / `redis` 互相访问，因此 `MYSQL_HOST=mysql`、`REDIS_HOST=redis`。

### 4.3 Docker Compose 一键启动（推荐）

`docker-compose.yml` 已配置为**本地开发模式**：

- 后端使用 `uvicorn --reload`，挂载 `./backend` → 改 Python 文件即时重启。
- 前端使用 `pnpm dev`（`Dockerfile.dev`），挂载 `./frontend` → 改前端代码即时热更新。
- MySQL / Redis 使用具名卷持久化数据，停机不丢库。

常用命令：

```bash
# 启动（首次会构建镜像，约几分钟）
docker compose up -d

# 查看后端实时日志（Ctrl+C 仅退出日志，不会停服务）
docker compose logs -f backend

# 查看前端实时日志
docker compose logs -f frontend

# 查看全部服务日志
docker compose logs -f

# 查看服务状态
docker compose ps

# 停止但保留数据卷
docker compose stop

# 停止并删除容器（保留数据卷）
docker compose down

# 彻底清理（含 mysql/redis 数据卷，慎用）
docker compose down -v

# 仅重建后端镜像（修改了 requirements.txt 时）
docker compose build backend && docker compose up -d backend

# 仅重建前端镜像（修改了 package.json 时）
docker compose build frontend && docker compose up -d frontend
```

启动完成后：

- 前端首页：<http://localhost:3000>
- 后端根：<http://localhost:8000>
- Swagger 文档：<http://localhost:8000/docs>
- 健康检查：<http://localhost:8000/health>

### 4.4 验证命令（curl）

后端启动成功后，可用以下命令逐一验证（所有占位接口返回 `"detail": "to be implemented"`）：

```bash
# 元信息
curl -s http://localhost:8000/ | jq

# 健康检查（含 MySQL / Redis 探活）
curl -s http://localhost:8000/health | jq

# 股票
curl -s 'http://localhost:8000/api/v1/stocks?page=1&page_size=20' | jq
curl -s http://localhost:8000/api/v1/stocks/600519 | jq

# 日线数据同步（akshare → MySQL，自动 upsert 去重）
curl -s -X POST http://localhost:8000/api/v1/data/sync/daily \
  -H 'Content-Type: application/json' \
  -d '{"stock_code":"600519","start_date":"2024-01-01","end_date":"2024-01-31"}' | jq
# 返回示例：{"stock_code":"600519","fetched":21,"saved":{"total":21,"affected":21},...}

# 查询日线（从本地 MySQL 读，不再走外网）
curl -s 'http://localhost:8000/api/v1/stocks/600519/daily?start_date=2024-01-01&end_date=2024-01-31' | jq

# 通用占位接口
curl -s -X POST 'http://localhost:8000/api/v1/data/sync?target=kline_daily' | jq
curl -s 'http://localhost:8000/api/v1/data/kline/600519?period=daily' | jq

# 回测
curl -s -X POST http://localhost:8000/api/v1/backtest/run | jq
curl -s http://localhost:8000/api/v1/backtest/stub-task-id | jq

# 策略
curl -s http://localhost:8000/api/v1/strategies | jq
curl -s http://localhost:8000/api/v1/strategies/ma_cross | jq
```

预期 `/health` 在 docker compose 启动状态下返回：

```json
{"status": "ok", "version": "0.1.0", "checks": {"mysql": true, "redis": true}}
```

### 4.5 初始化数据库表（首次启动后必做一次）

第一版不使用 Alembic，直接用 SQLAlchemy `create_all` 建表（脚本里同时模型导入注册到 metadata）：

```bash
# Docker 模式（推荐）
docker compose exec backend python -m app.scripts.init_db

# 本地模式
cd backend && python -m app.scripts.init_db

# 危险：开发期重置数据库（先 drop 再 create，会丢失全部数据）
docker compose exec backend python -m app.scripts.init_db --drop
```

成功后会在 MySQL 的 `quant_platform` 库创建 6 张表：

| 表名 | 用途 | 关键索引 |
| --- | --- | --- |
| `stock_basic` | 股票基础信息（代码 / 名称 / 市场 / 行业 / 上市日） | `code` 唯一 |
| `daily_bars` | 日线行情（OHLCV / 成交额 / 涨跌幅 / 换手率） | `(stock_code, trade_date)` 唯一 |
| `strategies` | 策略元信息（参数存 JSON） | `name` 唯一 |
| `backtest_tasks` | 回测任务（含状态机：pending/running/success/failed） | `strategy_id` / `status` / `stock_code` |
| `backtest_results` | 回测绩效指标（每个 task 唯一一条） | `task_id` 唯一 |
| `backtest_trades` | 回测成交明细（BUY/SELL） | `(task_id, trade_date)` |

外键策略：
- `backtest_tasks.strategy_id → strategies.id`：`RESTRICT`（被任务引用的策略不能删）
- `backtest_results.task_id / backtest_trades.task_id → backtest_tasks.id`：`CASCADE`（删除任务时一并清理结果与成交）

### 4.6 日线数据采集模块

**数据流**：`akshare → app.data.akshare_client → app.services.stock_service → daily_bars 表`

| 模块 | 职责 |
| --- | --- |
| `app/data/akshare_client.py` | 封装 `ak.stock_zh_a_hist`，**中文列名集中在 `_AkshareDailyColumns` 常量中维护**，rename 前严格预校验、未知列丢弃；类型转 `Decimal/date/int`；异常包装为 `AkshareError` |
| `app/services/stock_service.py` | 业务函数：`fetch_stock_daily_from_akshare` / `save_daily_bars` / `get_daily_bars` / `sync_daily_bars` |
| `app/api/data_api.py` | `POST /api/v1/data/sync/daily`（上游异常 → 502，参数错 → 400） |
| `app/api/stock_api.py` | `GET /api/v1/stocks/{code}/daily`（按日期范围读本地 MySQL） |

**akshare 字段映射（中文 → 表字段）**：

| akshare 中文列 | `daily_bars` 字段 | 必需 / 可选 | 说明 |
| --- | --- | --- | --- |
| 日期 | `trade_date` | 必需 | |
| 开盘 | `open` | 必需 | |
| 收盘 | `close` | 必需 | |
| 最高 | `high` | 必需 | |
| 最低 | `low` | 必需 | |
| 成交量 | `volume` | 必需 | 单位：手 |
| 成交额 | `amount` | 必需 | 单位：元 |
| 涨跌幅 | `pct_change` | 可选 | 单位：% |
| 换手率 | `turnover` | 可选 | 单位：% |
| 股票代码 / 振幅 / 涨跌额 | — | — | akshare 也返回，但本平台不入库，**自动丢弃** |

> akshare 升级若改了列名（如"开盘 → 开盘价"），错误信息会**直接列出缺失的中文列与实际返回的全部列**做对比，定位极快。
> 修复方式：到 `app/data/akshare_client.py` 的 `_AkshareDailyColumns` 改一行常量。

**去重策略**：`daily_bars` 表上 `(stock_code, trade_date)` 唯一索引；upsert 在
- MySQL：`INSERT ... ON DUPLICATE KEY UPDATE`（一条 SQL）
- SQLite（测试）：`INSERT ... ON CONFLICT DO UPDATE`
- 其他方言：兜底走"先查后写"循环

**单位约定**：与 akshare/tushare 保持一致——`volume` 单位是 **手**（1 手 = 100 股），`amount` 单位是 **元**。

**完整使用流程**：

```bash
# 1. 启动并初始化
docker compose up -d
docker compose exec backend python -m app.scripts.init_db

# 2. 同步贵州茅台 2024 年 1 月日线
curl -s -X POST http://localhost:8000/api/v1/data/sync/daily \
  -H 'Content-Type: application/json' \
  -d '{"stock_code":"600519","start_date":"2024-01-01","end_date":"2024-01-31"}' | jq

# 3. 重复执行同一次请求（验证去重）—— count 不会变多
curl -s -X POST http://localhost:8000/api/v1/data/sync/daily \
  -H 'Content-Type: application/json' \
  -d '{"stock_code":"600519","start_date":"2024-01-01","end_date":"2024-01-31"}' | jq

# 4. 查询本地结果
curl -s 'http://localhost:8000/api/v1/stocks/600519/daily?start_date=2024-01-01&end_date=2024-01-31' | jq '.count, .items[0]'

# 5. 直接看后端日志（同步进度 / 上游错误都在这里）
docker compose logs -f backend
```

### 4.7 技术指标模块（实时计算，不入库）

**目录布局**：

```text
backend/app/indicators/
├── __init__.py    # apply_indicators(df, ["ma","rsi","macd","boll"]) 统一入口
├── ma.py          # ma() / add_ma()
├── rsi.py         # rsi() / add_rsi()  ── Wilder 平滑
├── macd.py        # macd() / add_macd() ── HIST=2*(DIF-DEA) 国内惯例
└── boll.py        # boll() / add_boll() ── 第一版预留
```

**第一版指标清单**：

| 指标 | 默认参数 | 输出列 | 备注 |
| --- | --- | --- | --- |
| MA | `windows=(5, 10, 20, 60)` | `ma5` `ma10` `ma20` `ma60` | 简单移动平均 (SMA) |
| RSI | `period=14` | `rsi14` | Wilder 指数平滑；纯涨→100，纯跌→0，flat→NaN |
| MACD | `fast=12, slow=26, signal=9` | `macd_dif` `macd_dea` `macd_hist` | HIST = 2×(DIF-DEA) |
| BOLL | `period=20, std_mult=2.0` | `boll_upper` `boll_mid` `boll_lower` | 仅在显式调用时计算 |

**API 使用**：

```bash
# 不带指标（默认）—— 返回 trade_date / open / high / low / close / volume / amount / pct_change
curl -s 'http://localhost:8000/api/v1/stocks/600519/daily?start_date=2024-01-01&end_date=2024-03-31' | jq '.items[0]'

# 带指标 —— 在每行追加 ma5/10/20/60、rsi14、macd_dif/dea/hist
curl -s 'http://localhost:8000/api/v1/stocks/600519/daily?start_date=2024-01-01&end_date=2024-03-31&indicators=true' \
  | jq '.items[-1]'
# 示例输出：
# {
#   "trade_date": "2024-03-29", "open": 1700.0, "high": 1720.0, "low": 1690.0, "close": 1710.5,
#   "volume": 12345, "amount": 21000000.0, "pct_change": 0.65,
#   "ma5": 1705.34, "ma10": 1700.18, "ma20": 1695.04, "ma60": 1680.02,
#   "rsi14": 63.83, "macd_dif": 2.0014, "macd_dea": 1.5320, "macd_hist": 0.9388
# }
```

**输出格式约定**：
- 价格 (`open` / `high` / `low` / `close` / `amount`)：保留 3 位小数（float）
- 指标 (`maN` / `rsi14` / `macd_*`)：保留 4 位小数（float）
- 数据不足以计算时返回 `null`（例如前 4 行 `ma5` 为 null，前 59 行 `ma60` 为 null）
- `volume`：整数（单位：手）
- `trade_date`：ISO 字符串 `YYYY-MM-DD`，按升序排列

**代码层使用**（策略 / 回测层）：

```python
import pandas as pd
from app.indicators import apply_indicators, add_ma, ma, rsi, macd

# 高层批量
df_with = apply_indicators(df, ["ma", "rsi", "macd"])  # 默认全集

# 低层精细控制
ma20_series = ma(df["close"], 20)
rsi14_series = rsi(df["close"], 14)
dif, dea, hist = macd(df["close"], fast=12, slow=26, signal=9)
```

### 4.8 回测引擎（自研轻量版 v1）

**目录布局**：

```text
backend/app/strategy/                 # 策略层（产生信号，不下单）
├── base.py            # Signal 枚举 + Strategy 抽象基类
└── ma_cross.py        # MACrossStrategy 双均线（防未来函数）

backend/app/backtest/                 # 回测引擎四件套
├── broker.py          # 滑点 + 手续费 + 印花税
├── portfolio.py       # 资金/持仓状态机（100 股整数倍 + 现金/持仓约束）
├── engine.py          # 主循环 → trades + equity_curve
├── performance.py     # total/annual/drawdown/sharpe/win_rate
└── __init__.py        # 统一汇出
```

**回测流程**：

```
bars + signals ──▶ engine.run_backtest ──▶ trades + equity_curve
                          │
                          ▼
                    Broker / Portfolio
                          │
                          ▼
                  performance.compute_metrics ──▶ metrics dict
                          │
                          ▼
                  backtest_service.run_ma_cross_backtest
                          │
                          ▼
              backtest_tasks / results / trades 三表
```

**避免未来函数**：在第 t 日，策略产生的 `signal[t]` 仅基于 `t-1` 及更早的 close（实现上 `ma.shift(1)` + 对前一日交叉判断）；引擎在 t 日 **open 价**成交，**close 价**估值——彻底杜绝"今天的 close 影响今天的决策"这种隐性偏差。

**API 调用示例**：

```bash
# 1. 先确保有足够日线（至少 long_window+2 行）
curl -s -X POST http://localhost:8000/api/v1/data/sync/daily \
  -H 'Content-Type: application/json' \
  -d '{"stock_code":"600519","start_date":"2023-01-01","end_date":"2024-12-31"}' | jq '.fetched'

# 2. 运行双均线回测（参数全可省，见下表）
curl -s -X POST http://localhost:8000/api/v1/backtest/ma-cross \
  -H 'Content-Type: application/json' \
  -d '{
    "stock_code": "600519",
    "start_date": "2023-01-01",
    "end_date":   "2024-12-31",
    "initial_cash": 100000,
    "short_window": 5,
    "long_window":  20,
    "commission_rate": 0.0003,
    "stamp_tax_rate":  0.001,
    "slippage_rate":   0.0005
  }' | jq '{task_id, status, metrics}'

# 3. 查看持久化结果
docker compose exec mysql mysql -uquant_user -pquant_password quant_platform \
  -e "SELECT id, total_return, annual_return, max_drawdown, sharpe_ratio, win_rate, trade_count FROM backtest_results;"
```

**API 入参**：

| 字段 | 默认 | 范围 | 说明 |
| --- | --- | --- | --- |
| `stock_code` | — | string ≤20 | 股票代码（不带前缀） |
| `start_date` / `end_date` | — | YYYY-MM-DD | 回测起止日 |
| `initial_cash` | 100000 | (0, 1e10] | 初始资金 |
| `short_window` | 5 | [1, 120] | 快线均值窗口 |
| `long_window` | 20 | [2, 250] | 慢线均值窗口（必须 > short_window） |
| `commission_rate` | 0.0003 | [0, 0.01] | 手续费率（双向） |
| `stamp_tax_rate` | 0.001 | [0, 0.01] | 印花税率（仅卖出） |
| `slippage_rate` | 0.0005 | [0, 0.01] | 滑点（买入加 / 卖出减） |

**返回结构**：

```jsonc
{
  "task_id": 1,
  "status": "success",
  "stock_code": "600519",
  "start_date": "2023-01-01",
  "end_date":   "2024-12-31",
  "initial_cash": 100000.0,
  "params": {"short_window": 5, "long_window": 20},
  "metrics": {
    "total_return":  0.1236,
    "annual_return": 0.0612,
    "max_drawdown": -0.0808,
    "sharpe_ratio":  0.834,
    "win_rate":      0.667,
    "trade_count":   6
  },
  "trades": [
    {"trade_date": "2024-03-12", "action": "BUY", "price": 1700.85, "quantity": 500,
     "cash_after": 14958.20, "position_after": 500, "reason": "MA 金叉"},
    /* ... */
  ],
  "equity_curve": [
    {"trade_date": "2023-01-03", "cash": 100000.0, "position": 0, "close": 100.0, "equity": 100000.0},
    /* ... */
  ]
}
```

**绩效指标公式**（trading_days_per_year=252，rf=0）：

| 指标 | 公式 | 数据要求 |
| --- | --- | --- |
| total_return | `equity[-1] / equity[0] - 1` | ≥ 2 行 equity_curve |
| annual_return | `(1 + total_return) ^ (252/n) - 1` | 同上 |
| max_drawdown | `min((equity / cummax(equity)) - 1)` | 同上 |
| sharpe_ratio | `mean(daily_returns) / std(daily_returns) × √252` | std > 0 |
| win_rate | 完整 BUY→SELL 中卖价 > 买价的笔数 / 总笔数 | 至少 1 笔完整交易 |
| trade_count | trades 列表长度（买卖各计 1 次） | — |

数据不足或无意义时返回 `null`（例如全程不交易则 `win_rate=null`）。

### 4.9 CRUD Service 用法示例

每个领域提供一个**单例服务对象**，API/任务层直接使用：

```python
from app.core.database import SessionLocal
from app.services import (
    stock_service, daily_bar_service, strategy_service,
    backtest_task_service, backtest_result_service, backtest_trade_service,
)
from app.schemas.stock import StockBasicCreate

with SessionLocal() as db:
    # 普通 CRUD
    stock = stock_service.create(db, StockBasicCreate(code="600519", name="贵州茅台", market="SH"))
    stock = stock_service.get_by_code(db, "600519")           # 领域查询
    stock_service.upsert_by_code(db, payload)                 # 数据同步常用

    # 列表 / 分页 / 计数
    stocks = stock_service.list(db, skip=0, limit=100)
    total = stock_service.count(db)

    # 范围查询（K 线）
    bars = daily_bar_service.list_by_code(db, "600519", start=date(2024, 1, 1), end=date(2024, 6, 30))

    # 状态机
    backtest_task_service.mark_status(db, task, BacktestStatus.RUNNING)
    pending_tasks = backtest_task_service.list_by_status(db, BacktestStatus.PENDING)
```

### 4.10 前端页面（Next.js + ECharts）

**页面清单**：

| 路径 | 用途 | 关键功能 |
| --- | --- | --- |
| `/` | Dashboard | 项目说明、快捷查股、四阶段流程图 |
| `/stocks/[code]` | 股票详情 | K 线 + MA5/10/20 + 成交量 + 最近 20 交易日表格 |
| `/backtest` | 回测表单 | 参数输入 + 历史任务列表 |
| `/backtest/[id]` | 回测结果 | 6 大指标卡 + 净值曲线 + 交易明细表 |
| `/data` | 数据管理 | akshare 同步表单 + 同步结果展示 |

**目录布局**：

```text
frontend/
├── lib/
│   ├── api.ts            # 类型化 API 客户端，唯一入口
│   └── format.ts         # formatPercent / formatCurrency 等工具
├── types/
│   └── index.ts          # 与后端 schema 一一对应的全量类型
├── components/
│   ├── Navbar.tsx        # 顶部导航 + active 高亮
│   ├── ui/
│   │   ├── Card.tsx      # 通用容器
│   │   ├── Button.tsx    # primary / secondary / ghost 三态
│   │   ├── Field.tsx     # Field + TextInput / NumberInput / DateInput
│   │   └── Metric.tsx    # 数字卡片（支持百分比着色）
│   └── charts/
│       ├── KLineChart.tsx       # 蜡烛图 + MA + 成交量 + dataZoom
│       └── EquityCurveChart.tsx # 净值曲线 + 买卖点 markPoint
└── app/
    ├── layout.tsx               # 嵌 Navbar
    ├── page.tsx                 # Dashboard
    ├── stocks/[code]/page.tsx   # K 线 + 表格
    ├── backtest/page.tsx        # 表单 + 历史
    ├── backtest/[id]/page.tsx   # 结果详情
    └── data/page.tsx            # 同步表单
```

**配色约定**：

- **K 线**：A 股惯例（红涨绿跌）
- **绩效指标**（如总收益、年化）：全球惯例（**绿色为正、红色为负**）；K 线区配色与指标卡的配色含义不同——前者反映"今天涨/跌"，后者反映"赢/亏"，刻意区分以避免混淆。

**API 调用**：所有后端请求都走 `frontend/lib/api.ts` 的 `api.getDaily / api.syncDaily / api.runMaCross / api.getBacktest / api.listBacktestTasks`，不允许在组件里手写 `fetch`。错误统一抛 `ApiError`，含 `status / detail / path`。

**启动**：

```bash
# Docker（前后端一起，含热重载）
docker compose up -d
docker compose logs -f frontend     # 看到 "Ready in ..." 即可访问 http://localhost:3000

# 不用 Docker
cd frontend
pnpm install
pnpm dev      # http://localhost:3000
```

**典型流程演示**：

1. 打开 <http://localhost:3000/data>，输入 `600519 / 2023-01-01 / 2024-12-31`，点击「同步日线数据」
2. 进入 <http://localhost:3000/stocks/600519>，看到 K 线 + MA5/10/20
3. 进入 <http://localhost:3000/backtest>，默认参数即可，点击「运行回测」→ 自动跳转 `/backtest/[id]`
4. 在结果页查看 6 大指标 + 净值曲线（含买卖点）+ 交易明细

### 4.11 定时任务（APScheduler，第一版）

**目录布局**：

```text
backend/app/tasks/
├── __init__.py             # 汇出公共 API
├── scheduler.py            # BackgroundScheduler 单例 + SchedulerState（线程安全）
└── sync_daily_data.py      # sync_watchlist_daily 业务实现
```

**核心 Job**：每天 `SCHEDULER_DAILY_SYNC_HOUR:MINUTE`（默认 16:30 Asia/Shanghai）触发 `sync_watchlist_daily()`，对配置中 `WATCH_STOCKS` 列出的所有股票拉**当日**日线并 upsert。

**运行模式**：FastAPI lifespan 内嵌——启动时 `start_scheduler()`，关闭时 `shutdown_scheduler(wait=False)`。任何调度器异常都不会阻断 API 启动。

**相关配置**（`backend/.env.example`）：

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `SCHEDULER_ENABLED` | `true` | 设 `false` 可纯 API 模式，单测 / 调试常用 |
| `SCHEDULER_TIMEZONE` | `Asia/Shanghai` | cron 解释时区 |
| `SCHEDULER_DAILY_SYNC_HOUR` | `16` | 每日触发小时 |
| `SCHEDULER_DAILY_SYNC_MINUTE` | `30` | 每日触发分钟 |
| `WATCH_STOCKS` | `600519,000001,300750` | CSV，自动 strip 空格 / 跳过空项 |

**API**：

```bash
# 1. 查看调度器状态 + 已注册 jobs（含 next_run_time）+ 最近一次运行结果
curl -s http://localhost:8000/api/v1/data/sync/status | jq
# 返回示例：
# {
#   "scheduler_enabled": true,
#   "scheduler_running": true,
#   "timezone": "Asia/Shanghai",
#   "schedule": {"hour": 16, "minute": 30},
#   "watch_stocks": ["600519", "000001", "300750"],
#   "jobs": [{
#     "id": "watchlist_daily_sync",
#     "name": "watchlist daily sync",
#     "trigger": "cron[hour='16', minute='30']",
#     "next_run_time": "2026-05-24T16:30:00+08:00"
#   }],
#   "last_runs": {
#     "watchlist_daily_sync": {
#       "status": "success",
#       "triggered_by": "schedule",
#       "started_at": "2026-05-23T16:30:00",
#       "finished_at": "2026-05-23T16:30:12",
#       "duration_seconds": 12.345,
#       "target_date": "2026-05-23",
#       "total": 3, "success": 3, "failed": 0,
#       "per_stock": [...]
#     }
#   }
# }

# 2. 立即触发一次（不等定时任务）
curl -s -X POST http://localhost:8000/api/v1/data/sync/watchlist \
  -H 'Content-Type: application/json' -d '{}' | jq
# 不传 stock_codes 时使用配置中的 WATCH_STOCKS

# 3. 自定义同步特定股票池
curl -s -X POST http://localhost:8000/api/v1/data/sync/watchlist \
  -H 'Content-Type: application/json' \
  -d '{"stock_codes":["600519","000001"]}' | jq
```

**容错策略**：

- 单只股票同步失败（akshare 抛错 / 网络 / 解析）：仅该只标 `failed`，**不影响其它**
- 状态结构里 `per_stock` 列出每只股票的详细结果（含 `error` 字段）
- 整体失败级别按 `failed > 0 ? "partial" : "success"`（API 层都返回 200，业务状态在 body 里区分）
- 节假日 akshare 通常返回空，`fetched=0` / `affected=0` 视为正常完成

### 4.12 后期切换 Celery 的指引（仅文档，第一版未实现）

切到 Celery 的最小改动路径：

1. 新增 `app/tasks/celery_app.py`，暴露 `celery_app = Celery(...)`，broker / result backend 用 Redis（已有）。
2. 给 `sync_watchlist_daily` 加 `@celery_app.task` 装饰器，使其**同时可作 APScheduler 函数与 Celery task**——签名不变。
3. 用独立 `celery worker` + `celery beat` 进程替代 `BackgroundScheduler`；不再在 FastAPI lifespan 启动调度器。
4. 把 `SchedulerState` 的"最近运行结果"换成 Redis（多进程共享）。

调度器对外接口（`start_scheduler` / `trigger_watchlist_sync_now` / API 端点）保持不变，前端不感知切换。

### 4.13 回测分析报告（第一版规则化，不调用大模型）

**模块位置**：`backend/app/ai/report_generator.py`

**设计为可替换的 provider**：第一版固定 `provider=rule-based`（按指标阈值映射中文文案），未来加 OpenAI / 通义 / Ollama 时只需新增 `app/ai/providers/openai_provider.py` 等，**对外接口 `generate_report(detail) -> dict` 不变**。

**API**：

```bash
curl -s http://localhost:8000/api/v1/backtest/1/report | jq
```

返回结构：

```jsonc
{
  "task_id": 1,
  "stock_code": "600519",
  "params": {"short_window": 5, "long_window": 20},
  "summary": "策略整体表现较好：总收益 12.59%，最大回撤 -8.14%，共 2 笔交易。",
  "sections": [
    {
      "title": "策略总体表现",
      "level": "good",                      // info | good | warning | danger
      "content": ["..."]                    // 多行中文描述
    },
    { "title": "收益情况",                 "level": "...", "content": [...] },
    { "title": "最大回撤风险",              "level": "...", "content": [...] },
    { "title": "交易频率",                 "level": "...", "content": [...] },
    { "title": "胜率评价",                 "level": "...", "content": [...] },
    { "title": "过拟合 / 数据陷阱提醒",     "level": "...", "content": [...] }
  ],
  "disclaimer": "本报告由本平台基于历史回测数据规则化生成，仅供技术研究...",
  "generated_at": "2026-05-23T20:35:42",
  "provider": "rule-based"
}
```

**评价阈值表**（A 股语境经验值）：

| 维度 | 阈值规则 |
| --- | --- |
| 总收益 | ≥30% 极佳 / ≥10% 亮眼 / >0 持平 / >-10% 小亏 / 其余 亏损明显 |
| 年化 | 与无风险 3% 对比，超额 ≥5% 称"出色"，否则按差值梯度 |
| 最大回撤 | <5% 极小 / <15% 可控 / <30% 中等 / 其余 较高 |
| 夏普 | （在过拟合 R2 中）>5 视为异常高 |
| 胜率 | ≥60% 高 / ≥50% 中 / 其余 偏低 |
| 年化交易次数 | <4 极少 / <24 低频 / <120 中频 / 其余 高频 |

**过拟合自动检测规则**（命中越多越警惕）：

| 规则 | 触发条件 | 含义 |
| --- | --- | --- |
| R1 | `trade_count<4` 且 `total_return>20%` | 极少样本撑起的高收益 |
| R2 | `sharpe>5` | 异常高夏普，疑似过拟合 / 未来函数 |
| R3 | `\|max_drawdown\|<2%` 且 `total_return>20%` | 回撤过小可能是单边行情 |
| R4 | `long_window > days/3` | 参数自由度不足 |
| R5 | `trade_count==0` | 等同 buy-and-hold，无策略意义 |

**前端**：`/backtest/[id]` 页面内置「生成报告」按钮，按钮点击后渲染 `BacktestReport` 组件——按 `level` 给每个 section 着色（绿/黄/红/灰），底部固定显示风险免责声明。

### 4.14 不使用 Docker 的本地开发（可选）

后端：

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# 此时需要本机已有 mysql / redis，或仍用 docker compose 起 mysql/redis 两个服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd frontend
pnpm install
pnpm dev
```

---

## 五、后续开发路线

> 按"先打通链路、再迭代深度"的原则推进，每个阶段产出可演示的最小闭环。

### Phase 1 · 数据底座
- [ ] `data/sources/akshare_source.py`：实现日线、复权、基础信息、财报接口
- [ ] `models/`：建立 `stock`, `kline_daily`, `financial_report` 等表
- [ ] `tasks/jobs/sync_market.py`：日终行情同步任务（APScheduler）
- [ ] Redis 行情缓存策略

### Phase 2 · 指标与策略
- [ ] `indicators/`：MA / EMA / MACD / RSI / KDJ / BOLL
- [ ] `strategy/base.py`：定义统一 `Strategy` 抽象
- [ ] 实现 1~2 个示例策略（如双均线、动量）

### Phase 3 · 回测引擎
- [ ] `backtest/engine.py`：事件驱动主循环
- [ ] `backtest/portfolio.py` + `broker.py`：资金、持仓、撮合、滑点、手续费
- [ ] `backtest/metrics.py`：年化收益、最大回撤、夏普、卡玛等
- [ ] API：提交回测任务 → 返回任务 ID → 查询结果

### Phase 4 · 可视化
- [ ] 选定 ECharts 或 TradingView Lightweight Charts
- [ ] K 线 + 指标叠加 + 买卖点标注
- [ ] 回测净值曲线、回撤曲线、交易明细表

### Phase 5 · 工程化扩展
- [ ] `tasks/celery_app.py`：切换/并存 Celery，处理重计算任务
- [ ] `backtest/adapters/backtrader_adapter.py`：复用 Backtrader 生态
- [ ] `data/sources/tushare_source.py`：多数据源容灾
- [ ] CI / 单元测试 / 代码风格（ruff、mypy、eslint、prettier）

### Phase 6 · AI 能力
- [ ] `ai/providers/`：封装 OpenAI / 本地模型等
- [ ] 新闻 & 公告情绪分析
- [ ] 大模型辅助选股 / 复盘解读
- [ ] 自动化因子挖掘实验

---

## 六、约定

- **命名**：模块、文件均用 `snake_case`；前端组件用 `PascalCase`。
- **业务边界**：API 层不写业务、Service 层不直接依赖 FastAPI、计算层不依赖数据库。
- **分支策略**：`main`（稳定）/ `develop`（集成）/ `feature/*`（特性）。
- **提交信息**：建议 Conventional Commits（`feat:` / `fix:` / `chore:` ...）。

---

## 七、免责声明

本项目仅用于**技术研究与个人学习**，不构成任何投资建议。使用者应自行承担因使用本项目相关代码与数据所产生的全部风险。
