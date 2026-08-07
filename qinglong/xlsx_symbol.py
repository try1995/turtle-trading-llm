"""
股票分析脚本

从 xlsx 文件中读取股票列表：

1. 读取配置的 xlsx 文件获取股票列表（代码、名称）
2. 设置股票代码到 GitHub 仓库变量并触发工作流（github_stock_analysis）
3. 逐只调用 analysis_stock_sync 同步分析
4. 从分析结果提取 sentiment_score
5. 全部股票按分数排序，发送汇总邮件
6. 分数 > 60 的股票，额外调用 planAgent 深入分析

用法：
    python qinglong/xlsx_symbol.py
    python qinglong/xlsx_symbol.py tenant_xxx
"""
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from tools.all_types import Tenant
from tools.daily_stock_analysis import analysis_stock_sync
from tools.github_tools import github_stock_analysis

load_dotenv()

logger.remove()
logger.add(sys.stderr, level="INFO")

toaddrs_default = os.environ.get("toaddrs", "").split("|")
# 股票列表 xlsx 文件路径，可在 .env 中配置 anlysis_xlsx_path
xlsx_path = os.environ.get("anlysis_xlsx_path", "股友899X1H2138选股.xlsx")


def read_stocks_from_xlsx(path=xlsx_path):
    """
    读取 xlsx 中的股票列表。

    列要求：包含「代码」「名称」两列。
    返回: [{"code": "601628", "name": "中国人寿"}, ...]
    """
    df = pd.read_excel(path)
    stocks = []
    for _, row in df.iterrows():
        code = str(row["代码"]).strip().zfill(6)  # 补齐6位，如 2714 -> 002714
        name = str(row["名称"]).strip()
        stocks.append({"code": code, "name": name})
    logger.info(f"从 {path} 读取到 {len(stocks)} 只股票")
    return stocks


def extract_score(symbol_result):
    """
    从同步分析结果中提取 sentiment_score。
    result 结构: {"report": {"summary": {"sentiment_score": 80.0}}}
    """
    try:
        return float(symbol_result["report"]["summary"]["sentiment_score"])
    except (KeyError, TypeError, ValueError):
        return None


def send_score_email(qualified, dear="总裁", toaddrs=None):
    """发送全部强势股票的汇总邮件（按分数排序）"""
    if not qualified:
        logger.info("没有有评分的股票，跳过邮件")
        return

    from agents.planAgent import PlanAgent

    df = pd.DataFrame(qualified)
    df = df.sort_values("score", ascending=False)

    # 构造摘要
    summary_df = df[["stock_code", "stock_name", "score"]].copy()
    summary_df.columns = ["股票代码", "股票名称", "分数"]
    md = summary_df.to_markdown(index=False)
    md = f"## 股票分析评分汇总\n\n分析日期：{datetime.now().strftime('%Y-%m-%d')}\n\n{md}"

    logger.info(f"\n{md}")

    recipients = toaddrs or toaddrs_default
    if recipients:
        plan = PlanAgent()
        plan.send_res_email(md, subject=f"股票分析评分汇总 ({datetime.now().strftime('%m-%d')})",
                            table=True, toaddrs=recipients, dear=dear)
        logger.info("汇总邮件已发送")


def analyze_high_score_stocks(high_score_stocks, dear="总裁", toaddrs=None):
    """对分数 > 60 的股票调用 planAgent 深入分析"""
    from agents.planAgent import PlanAgent

    for item in high_score_stocks:
        symbol = item["stock_code"]
        name = item["stock_name"]
        score = item["score"]
        logger.info(f"开始深入分析 {name}({symbol})，分数: {score}")

        try:
            plan = PlanAgent()
            plan.run(f"详细分析{symbol}({name})行情情况，提供交易建议", human_in_loop=False)
            plan.send_allres_email(
                subject=f"高评分强势股分析-{symbol}({name}, 分数{score})",
                toaddrs=toaddrs,
                dear=dear,
            )
            logger.info(f"{name}({symbol}) 深入分析完成")
        except Exception as e:
            logger.error(f"{name}({symbol}) 分析失败: {e}")


def daily_task(dear="总裁", toaddrs=None):
    # 1. 读取 xlsx 股票列表
    stocks = read_stocks_from_xlsx(xlsx_path)
    if not stocks:
        logger.warning("股票列表为空，退出")
        return

    # 1.5 先设置股票代码并触发 GitHub 工作流
    symbols = "|".join(s["code"] for s in stocks)
    logger.info(f"触发 GitHub 股票分析工作流，股票代码: {symbols}")
    try:
        res = github_stock_analysis(symbols)
        logger.info(f"github_stock_analysis: {res}")
    except Exception as e:
        logger.error(f"github_stock_analysis 触发失败: {e}")

    # 2. 逐只同步分析并提取评分
    logger.info("开始同步分析...")
    records = []
    for stock in stocks:
        symbol = stock["code"]
        name = stock["name"]
        logger.info(f"同步分析: {name}({symbol})")

        result = analysis_stock_sync(symbol)
        symbol_result = result.get(symbol, {})
        score = extract_score(symbol_result)
        if score is None:
            logger.warning(f"{symbol} {name} 无法获取 sentiment_score")

        records.append({
            "stock_code": symbol,
            "stock_name": name,
            "score": score,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
        })

    scored = [r for r in records if r["score"] is not None]
    if not scored:
        logger.info("所有股票均无评分记录")
        return

    logger.info(f"共 {len(scored)} 条评分记录")

    # 3. 按分数阈值筛选
    gt60 = [r for r in scored if r["score"] > 60]

    logger.info(f"全部股票: {len(scored)} 只")
    logger.info(f"分数 > 60: {len(gt60)} 只")

    # 4. 全部股票发送汇总邮件（按分数排序）
    if scored:
        send_score_email(scored, dear=dear, toaddrs=toaddrs)

    # 5. 分数 > 60 调用 planAgent 深入分析
    if gt60:
        analyze_high_score_stocks(gt60, dear=dear, toaddrs=toaddrs)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        logger.info(f"tenant参数：{arg1}")

        tenant_raw = os.environ.get(arg1, "")
        if tenant_raw:
            tenant = Tenant.model_validate_json(tenant_raw)
            dear = tenant.name
            toaddrs = tenant.toaddrs.split("|")
            daily_task(dear=dear, toaddrs=toaddrs)
        else:
            logger.error(f"未定义环境变量{arg1}")
    else:
        daily_task()
