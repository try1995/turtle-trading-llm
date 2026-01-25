## 📈 多智能体股票工具

| 模块 | 说明 |
| ---- | ---- |
| 数据来源 | 主要基于 [AkShare](https://github.com/akfamily/akshare) 实时/历史行情与基本面数据 |

---

### 🤖 智能体清单

| 智能体 | 职责 |
| --- | --- |
| **dataAgent** | 获取并分析个股公开数据（行情、财务、技术指标等），可以单独运行 |
| **reportAgent** | 拉取并解析研报，提炼盈利预测、估值与风险点，可以单独运行 |
| **publicOptionAgent** | 分析个股舆情信息，可以单独运行 |
| **investmentAgent** | 综合前述信息，给出量化+定性投资建议，无法单独运行 |
| **planAgent** | 统筹调度，综合分析单独运行这个即可 |

---

### 🚀 快速上手

1. **安装依赖**  
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**  
   ```bash
   cp env_example .env
   # 编辑 .env 填入必要参数
   api_key="sk-"
   model=""
   base_url=""
   ```

3. **单智能体调试**  
   ```bash
   python <AgentName>.py   # 如 python dataAgent.py
   ```

---

### 盘后自动跑批青龙脚本，跑完自动邮箱发送
```
qionglong.py

在青龙面板-添加订阅，订阅本仓库，关闭自动添加任务和自动删除任务
添加定时任务
try1995_turtle-trading-llm/qionglong.py 
# 定时规则为每天天盘后三点半
30 15 * * *
环境变量里面设置好.env里面的配置信息，额外需要配置好邮箱信息
```

### 回测支持
#### TODO test_single_backtest.py

> ⚠️ 仅供学习与研究参考，不构成投资建议。
