# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A multi-agent stock analysis system (turtle-trading-llm) that uses LLMs to analyze A-share stocks through specialized agents. The system orchestrates multiple agents (data, report, public opinion, visual, and investment) to provide comprehensive stock analysis with automated email delivery.

## Architecture

### Agent Hierarchy

```
planAgent (orchestrator)
    ├── dataAgent       - Market data, fundamentals, technical indicators
    ├── reportAgent     - Research reports analysis
    ├── publicOptionAgent - Public opinion/sentiment analysis
    ├── vlAgent         - K-line chart visual analysis
    └── investmentAgent - Investment recommendations (aggregates other agents)
```

All agents inherit from `baseAgent` (agents/baseAgent.py) which provides:
- LLM invocation (`invork`, `invork_with_tools`)
- Tool execution framework with retry logic
- Backtesting mode support (`set_backtest(date)`)
- Response caching via `@save_response` decorator
- Email delivery functionality

### Tool Registration

Tools are functions decorated with type hints for schema generation. The `get_func_schema()` function (tools/base_tool.py) converts functions to OpenAI tool format. Each agent registers its tools via `self.tools_regist` and maps them via `self.tools_dict`.

### Key Modules

- **agents/**: Agent implementations (dataAgent, planAgent, reportAgent, etc.)
- **tools/**: Data source tools (aktools.py - AkShare, zttools.py - ZhiTuAPI, search.py - Tavily)
- **prompt.py**: System prompts for each agent role
- **qinglong/**: Scheduled task scripts for automation (青龙/Qinglong integration)
- **.pyturtlecache/**: Response cache organized as `{date}/{symbol}/{agent}_run`

## Environment Setup

Copy `env_example` to `.env` and configure:

```bash
# Required LLM settings
api_key="sk-..."
base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
model="qwen-plus-latest"

# Optional: Per-agent model overrides
dataAgentModel="qwen-max"
vlAgentModel="qwen-vl-plus"
# etc.

# Database (required for some tools)
DATABASE_URL="mysql+pymysql://..."

# Email delivery (optional but typical)
smtp_user="..."
smtp_password="..."
smtp_server="..."
toaddrs="email1|email2"

# API keys for tools
TAVILY_API_KEY="..."      # For search agent
ZT_TOKEN="..."             # For zttools
SERVER_JIO_KEY="..."       # For push notifications
```

## Development Commands

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run individual agents (debugging)
```bash
python test_data_agent.py      # Test dataAgent
python test_report_agent.py     # Test reportAgent
python test_publicOptionAgent.py # Test publicOptionAgent
python test_plan_agent.py       # Test full analysis via planAgent
```

### Run with backtesting mode
Agents support backtesting via `set_backtest(date_string)` where date format is `%Y%m%d`.

### Qinglong automation
Scheduled tasks are in `qinglong/`. For position analysis:
```bash
python qinglong/position_symbol.py tenant_name
```
Where `tenant_name` maps to an environment variable `tenant_tenant_name` containing JSON with tenant config (position symbols, email addresses, etc.).

## Important Design Patterns

### Date Handling
Agents determine the current trade date via `get_date_desc()`. If not in a trade day, they automatically use the last trade date. Backtesting mode overrides this with a fixed date.

### Cache System
- Agent responses are cached in `.pyturtlecache/{date}/{symbol}/{agent}_run`
- Function call results cached via MD5 hash of parameters in `.pyturtlecache/cache/{hash}`
- Cache is controlled via `use_cache` parameter (default True)
- `@save_response` decorator automatically caches `run()` results

### Agent Orchestration (planAgent)
1. `planAgent.run()` generates a JSON plan assigning tasks to agents
2. `planAgent.act()` executes the plan sequentially, running each agent's `run()` method
3. Results are aggregated and can be emailed via `send_allres_email()`

### Tool Call Error Handling
The framework uses `json_repair` to fix malformed JSON from LLMs. Tool execution has built-in retry (default 3 attempts) with 3-second sleep between attempts.

### Email Delivery
Emails are formatted as HTML with CSS styling for tables. Content uses Markdown syntax converted via `markdown` library. Supports table format for data display.

## Database

Uses SQLAlchemy via `tools/sql_utils.py`. Main tables include `AStockInfos` for stock metadata. Database is required for symbol lookup operations.

## Agent-Specific Notes

- **dataAgent**: Divides analysis into sub-tasks (基本面数据, 技术面数据, 同行对比)
- **reportAgent**: Parses research reports (PDF) using markitdown or pymupdf
- **vlAgent**: Visual analysis using VL-capable models (qwen-vl-plus)
- **publicOptionAgent**: Analyzes news sentiment
- **investmentAgent**: Aggregates results from other agents via `get_all_agent_res()` tool
