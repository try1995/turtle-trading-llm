"""
分析结果检查脚本

依赖 daily_stock_analysis.py 先触发跌停股票分析，然后本脚本：

1. 查询当日分析任务是否全部完成
2. 查询分析历史获取分数
3. 分数 > 52 的股票，发送邮件汇总
4. 分数 > 62 的股票，额外调用 planAgent 深入分析

用法：
    python qinglong/check_analysis_results.py
    python qinglong/check_analysis_results.py tenant_xxx
"""
import os
import sys
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests
import pandas as pd
from loguru import logger
from datetime import datetime
from dotenv import load_dotenv
from tools.all_types import Tenant

load_dotenv()

logger.remove()
logger.add(sys.stderr, level="INFO")

anlysis_symbol_url = os.environ.get("anlysis_symbol_url", "")
anlysis_symbol_pasword = os.environ.get("anlysis_symbol_pasword", "")
toaddrs_default = os.environ.get("toaddrs", "").split("|")


def login():
    session = requests.Session()
    data = {"password": anlysis_symbol_pasword, "passwordConfirm": "string"}
    ret = session.post(f"http://{anlysis_symbol_url}/api/v1/auth/login", json=data)
    logger.info(f"登录结果: {ret.json()}")
    return session


def wait_for_tasks_complete(session, timeout_minutes=30, poll_interval=30):
    """
    轮询 /api/v1/analysis/tasks，等待所有任务完成。
    返回当日已完成的任务列表（按 created_at 过滤）。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    deadline = time.time() + timeout_minutes * 60

    while time.time() < deadline:
        ret = session.get(f"http://{anlysis_symbol_url}/api/v1/analysis/tasks")
        data = ret.json()

        pending = data.get("pending", 0)
        processing = data.get("processing", 0)

        if pending == 0 and processing == 0:
            # 翻页获取当日所有任务，按创建时间倒序排列，遇到非当天记录即可停止
            page = 1
            today_tasks = []
            while True:
                ret = session.get(f"http://{anlysis_symbol_url}/api/v1/history?page={page}")
                data = ret.json()
                items = data.get("items", [])
                if not items:
                    break
                for item in items:
                    created = str(item.get("created_at", ""))
                    if created.startswith(today):
                        today_tasks.append(item)
                    else:
                        # 后续页时间更早，无需继续
                        logger.info(f"所有任务已完成，当日共 {len(today_tasks)} 个（翻取至第 {page} 页）")
                        return today_tasks
                page += 1
            logger.info(f"所有任务已完成，当日共 {len(today_tasks)} 个")
            return today_tasks

        logger.info(f"剩余 pending={pending}, processing={processing}，等待 {poll_interval}s...")
        time.sleep(poll_interval)

    logger.error(f"等待超时（{timeout_minutes}min）")
    return []


def fetch_scores_from_tasks(session, tasks):
    """
    对每个已完成任务调用 status 接口，获取 sentiment_score。
    返回带分数的记录列表。
    """
    result = []
    for t in tasks:
        task_id = t.get("query_id")
        stock_code = t.get("stock_code", "")
        stock_name = t.get("stock_name", "")

        ret = session.get(f"http://{anlysis_symbol_url}/api/v1/analysis/status/{task_id}")
        status_data = ret.json()

        # 从 result.report.summary.sentiment_score 提取分数
        score = None
        try:
            score = status_data["result"]["report"]["summary"]["sentiment_score"]
            score = float(score)
        except (KeyError, TypeError, ValueError):
            logger.warning(f"{stock_code} {stock_name} 无法获取 sentiment_score")

        result.append({
            "stock_code": stock_code,
            "stock_name": stock_name,
            "score": score,
            "trend_prediction": t.get("status"),  # 任务状态而非趋势预测
            "created_at": t.get("created_at", ""),
        })

    return result


def send_score_email(qualified, dear="总裁", toaddrs=None):
    """发送分数 > 52 的股票汇总邮件"""
    if not qualified:
        logger.info("没有分数 > 52 的股票，跳过邮件")
        return

    from agents.planAgent import PlanAgent

    df = pd.DataFrame(qualified)
    df = df.sort_values("score", ascending=False)

    # 构造摘要
    summary_df = df[["stock_code", "stock_name", "score"]].copy()
    summary_df.columns = ["股票代码", "股票名称", "分数"]
    md = summary_df.to_markdown(index=False)
    md = f"## 跌停股票分析评分汇总\n\n分析日期：{datetime.now().strftime('%Y-%m-%d')}\n\n{md}"

    logger.info(f"\n{md}")

    recipients = toaddrs or toaddrs_default
    if recipients:
        plan = PlanAgent()
        plan.send_res_email(md, subject=f"跌停分析评分汇总 ({datetime.now().strftime('%m-%d')})",
                            table=True, toaddrs=recipients, dear=dear)
        logger.info("汇总邮件已发送")


def analyze_high_score_stocks(high_score_stocks, dear="总裁", toaddrs=None):
    """对分数 > 62 的股票调用 planAgent 深入分析"""
    from agents.planAgent import PlanAgent

    for item in high_score_stocks:
        symbol = item["stock_code"]
        name = item["stock_name"]
        score = item["score"]
        logger.info(f"开始深入分析 {name}({symbol})，分数: {score}")

        try:
            plan = PlanAgent()
            plan.run(f"详细分析{symbol}行情情况，提供交易建议", human_in_loop=False)
            plan.send_allres_email(
                subject=f"高评分跌停股分析-{symbol}({name}, 分数{score})",
                toaddrs=toaddrs,
                dear=dear,
            )
            logger.info(f"{name}({symbol}) 深入分析完成")
        except Exception as e:
            logger.error(f"{name}({symbol}) 分析失败: {e}")


def daily_task(dear="总裁", toaddrs=None):
    session = login()

    # 1. 等待所有分析任务完成，获取任务列表
    logger.info("等待分析任务完成...")
    tasks = wait_for_tasks_complete(session)
    if not tasks:
        logger.warning("当日无已完成任务，退出")
        return

    # 2. 逐任务查询 status 获取 sentiment_score
    logger.info("获取分析评分...")
    records = fetch_scores_from_tasks(session, tasks)

    # 过滤出有分数的记录
    scored = [r for r in records if r["score"] is not None]
    if not scored:
        logger.info("所有任务均无评分记录")
        return

    logger.info(f"共 {len(scored)} 条评分记录")

    # 3. 按分数阈值筛选
    gt52 = [r for r in scored if r["score"] > 52]
    gt62 = [r for r in scored if r["score"] > 62]

    logger.info(f"分数 > 52: {len(gt52)} 只")
    logger.info(f"分数 > 62: {len(gt62)} 只")

    # 4. 分数 > 52 发送汇总邮件
    if gt52:
        send_score_email(gt52, dear=dear, toaddrs=toaddrs)

    # 5. 分数 > 62 调用 planAgent 深入分析
    if gt62:
        analyze_high_score_stocks(gt62, dear=dear, toaddrs=toaddrs)


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
