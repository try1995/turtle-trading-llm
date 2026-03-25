## 📈 多智能体股票分析工具

基于 LLM 的多智能体 A 股分析系统，通过专业智能体协作提供全面的股票分析报告，支持自动化盘后分析和邮件推送。

### 数据来源

| 数据源 | 说明 |
| ---- | ---- |
| AkShare | 实时/历史行情、财务数据、技术指标 |
| 研报平台 | 个股研报 PDF 解析 |
| 新闻资讯 | 公开舆情信息采集 |
| 图智API | 补充行情数据 |

---

### 🤖 智能体架构

```
planAgent (统筹调度)
    ├── dataAgent          - 行情数据、基本面、技术指标分析
    ├── reportAgent        - 研报内容解析与提炼
    ├── publicOptionAgent  - 舆情信息分析
    ├── vlAgent            - K 线图表视觉分析
    └── investmentAgent    - 综合投资建议（聚合上述智能体）
```

| 智能体 | 职责 | 可独立运行 |
| --- | --- | --- |
| **dataAgent** | 获取并分析个股公开数据（行情、财务、技术指标、同行对比） | ✅ |
| **reportAgent** | 拉取并解析研报，提炼盈利预测、估值与风险点 | ✅ |
| **publicOptionAgent** | 分析个股舆情信息 | ✅ |
| **vlAgent** | 分析股票分时图、日/周/月 K 线图数据 | ✅ |
| **investmentAgent** | 综合前述信息，给出量化+定性投资建议 | ❌ |
| **planAgent** | 统筹调度，综合分析（推荐运行此智能体） | ✅ |

---

### 🚀 快速上手

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置环境变量

```bash
cp env_example .env
# 编辑 .env 文件，填入必要参数
```

**必需配置：**
```bash
# LLM 配置
api_key="sk-..."              # 你的 API Key
base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # API 地址
model="qwen-plus-latest"      # 默认模型
```

**可选配置（推荐）：**
```bash
# 各智能体专用模型（可针对不同能力选择模型）
dataAgentModel="qwen-max"
vlAgentModel="qwen-vl-plus"
reportAgentModel="qwen-long-latest"
publicOptionAgentModel="qwen-max-2025-01-25"
investmentAgentModel="qwen3-max-preview"

# 数据库（部分功能需要）
DATABASE_URL="mysql+pymysql://user:password@host:3306/dbname"

# 邮件推送
smtp_user="your@email.com"
smtp_password="your_password"
smtp_server="smtp.example.com"
toaddrs="recipient1@email.com|recipient2@email.com"  # 多个用 | 分隔

# 第三方 API
TAVILY_API_KEY="..."          # 搜索引擎 API
ZT_TOKEN="..."                # 图智 API
SERVER_JIO_KEY="..."          # Server酱推送

# 交易配置
position_symbol="000001|600000"  # 持仓股票（多个用 | 分隔）
exclude_symbol=""             # 排除股票
```

#### 3. 运行分析

**使用 planAgent 进行综合分析：**
```bash
python test_plan_agent.py
```

**调试单个智能体：**
```bash
python test_data_agent.py        # 测试 dataAgent
python test_report_agent.py       # 测试 reportAgent
python test_publicOptionAgent.py  # 测试 publicOptionAgent
```

**自定义分析：**
```python
from agents.planAgent import PlanAgent

plan = PlanAgent()
plan.run("详细分析 601601 中国人寿，提供交易建议")
plan.send_allres_email(subject="中国人寿分析报告", toaddrs=["your@email.com"])
```

---

### 📦 青龙定时任务集成

支持通过青龙面板实现盘后自动化分析和邮件推送。

#### 配置步骤

1. **添加订阅**
   - 青龙面板 → 订阅管理 → 添加订阅
   - 订阅本仓库，关闭"自动添加任务"和"自动删除任务"

2. **添加定时任务**
   ```bash
   try1995_turtle-trading-llm/qinglong/position_symbol.py tenant_name
   # 定时规则：每天盘后三点半
   # 30 15 * * *
   ```

3. **配置租户环境变量**

   在青龙环境变量中添加租户配置（JSON 格式）：
   ```bash
   tenant_tenant_name='{
     "name": "租户名称",
     "toaddrs": "email1@example.com|email2@example.com",
     "exclude_symbol": "",
     "position_symbol": "000001|600000|600036"
   }'
   ```

4. **设置环境变量**

   确保 `.env` 中的邮箱配置正确，定时任务运行后会自动发送分析报告邮件。

#### 可用的青龙脚本

| 脚本 | 功能 |
| ---- | ---- |
| `position_symbol.py` | 持仓股票每日分析（推荐） |
| `hot_symbol.py` | 热点股票分析 |
| `up_symbol.py` | 涨幅榜股票分析 |
| `news_symbol.py` | 新闻相关股票分析 |

---

### 🧪 测试与调试

```bash
# 测试单个智能体
python test_data_agent.py
python test_report_agent.py
python test_publicOptionAgent.py

# 测试完整流程
python test_plan_agent.py
```

---

### 💾 缓存机制

系统自动缓存分析结果以提升性能：
- **缓存路径**：`.pyturtlecache/{日期}/{股票代码}/{智能体}_run`
- **函数调用缓存**：`.pyturtlecache/cache/{md5_hash}`
- **交易日自动检测**：非交易日自动使用最近交易日数据

**禁用缓存：**
```python
plan = PlanAgent()
plan.run("分析...", use_cache=False)
```

---

### 🔧 回测支持

支持历史日期回测模式：

```python
from agents.planAgent import PlanAgent

plan = PlanAgent()
plan.set_backtest("20240101")  # 设置回测日期
plan.run("分析...", use_cache=False)
```

> ⚠️ 回测功能仍在开发中，详见 `test_single_backtest.py`

---

### 📂 项目结构

```
turtle-trading-llm/
├── agents/              # 智能体实现
│   ├── baseAgent.py     # 基础智能体类
│   ├── planAgent.py     # 统筹调度智能体
│   ├── dataAgent.py     # 数据分析智能体
│   ├── reportAgent.py    # 研报解析智能体
│   └── ...
├── tools/               # 数据工具
│   ├── aktools.py       # AkShare 数据接口
│   ├── zttools.py       # 图智 API 接口
│   ├── search.py        # 搜索引擎接口
│   └── sql_utils.py     # 数据库工具
├── qinglong/           # 青龙定时任务脚本
├── prompt.py           # 各智能体系统提示词
├── config.py           # 配置文件
├── llm.py              # LLM 客户端
├── .pyturtlecache/     # 缓存目录（自动生成）
└── requirements.txt     # 依赖列表
```

---

### ⚠️ 免责声明

> 本项目仅供学习与研究参考，所有分析结果基于公开数据和算法生成，不构成任何投资建议。投资有风险，入市需谨慎。
