"""
跌停股池后续表现分析脚本

用法：
    python qinglong/limit_down_analysis.py 2026-06-12

功能：
    1. 获取指定日期的跌停股票列表
    2. 查询这些股票从跌停日到现在的涨跌情况
    3. 绘制涨跌幅走势图并保存
"""
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import baostock as bs
from tools.aktools import stock_zt_pool_dtgc_em
from loguru import logger

matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 重建字体缓存确保中文字体可用
import matplotlib.font_manager as fm
fm._load_fontmanager(try_read_cache=False)


def get_stock_performance(symbol: str, start_date: str, end_date: str) -> pd.DataFrame | None:
    """获取个股从 start_date 到 end_date 的日线行情（使用 baostock）"""
    from tools.base_tool import get_market

    try:
        # 转换股票代码格式：get_market 返回 'sh' 或 'sz'
        bs_code = get_market(symbol).lower() + "." + symbol
        # baostock 日期格式为 yyyy-MM-dd
        bs_start = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        bs_end = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"

        rs = bs.query_history_k_data_plus(bs_code,
            fields='date,code,open,high,low,close,volume,amount,pctChg',
            start_date=bs_start, end_date=bs_end,
            frequency='d', adjustflag='3')
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())

        if not rows:
            return None
        df = pd.DataFrame(rows, columns=['交易时间', 'code', '开盘价', '最高价', '最低价', '收盘价', '成交量', '成交额', '涨跌幅'])
        df['交易时间'] = pd.to_datetime(df['交易时间'])
        df['收盘价'] = df['收盘价'].astype(float)
        df = df.sort_values('交易时间')
        return df
    except Exception as e:
        logger.warning(f"获取{symbol}数据失败: {e}")
        return None


def plot_performance(all_data: dict, save_path: str, trade_date: str):
    """绘制所有股票的累计涨跌幅走势图"""
    fig, ax = plt.subplots(figsize=(16, 10))

    colors = plt.cm.tab20.colors
    color_idx = 0

    for label, df in all_data.items():
        if df is None or len(df) < 1:
            continue
        first_close = float(df.iloc[0]['收盘价'])
        if first_close == 0:
            continue
        df = df.copy()
        df['累计涨跌幅'] = (df['收盘价'].astype(float) / first_close - 1) * 100
        ax.plot(df['交易时间'], df['累计涨跌幅'], label=label, color=colors[color_idx % len(colors)], linewidth=1.2)
        color_idx += 1

    ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('累计涨跌幅 (%)', fontsize=12)
    ax.set_title(f'跌停股池后续表现（跌停日: {trade_date}，统计至 {datetime.now().strftime("%Y-%m-%d")}）', fontsize=14)
    ax.legend(loc='best', fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    logger.info(f"图表已保存: {save_path}")


def main():
    if len(sys.argv) < 2:
        logger.error("请指定日期，格式：yyyy-MM-dd，e.g. 2026-06-12")
        sys.exit(1)

    trade_date = sys.argv[1]
    logger.info(f"查询跌停日: {trade_date}")
    trade_date_compact = trade_date.replace("-", "")

    # 获取跌停股池
    raw = stock_zt_pool_dtgc_em(date=trade_date_compact)
    stocks = json.loads(raw)
    if not stocks:
        logger.error(f"{trade_date} 无跌停股票数据")
        sys.exit(1)

    logger.info(f"跌停股票数量: {len(stocks)}")

    # 计算查询日期范围
    end_date = datetime.now().strftime("%Y%m%d")

    # 获取每只股票的走势
    bs.login()
    all_data = {}
    for stock in stocks:
        symbol = stock['代码']
        name = stock['名称']
        logger.info(f"正在查询 {name}({symbol})...")
        df = get_stock_performance(symbol, trade_date_compact, end_date)
        if df is not None:
            df['股票代码'] = symbol
            df['股票名称'] = name
            all_data[f"{name}({symbol})"] = df
    bs.logout()

    if not all_data:
        logger.error("未获取到任何股票数据")
        sys.exit(1)

    # 保存原始数据
    summary = []
    for label, df in all_data.items():
        if len(df) < 1:
            continue
        first = df.iloc[0]
        last = df.iloc[-1]
        total_change = (float(last['收盘价']) / float(first['收盘价']) - 1) * 100
        summary.append({
            '股票': label,
            '跌停日收盘': float(first['收盘价']),
            '最新收盘': float(last['收盘价']),
            '累计涨跌幅(%)': round(total_change, 2)
        })

    if not summary:
        logger.error("无足够数据生成汇总")
        sys.exit(1)

    summary_df = pd.DataFrame(summary)
    summary_df = summary_df.sort_values('累计涨跌幅(%)', ascending=False)

    logger.info("\n" + summary_df.to_string(index=False))

    # 绘制图表
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"limit_down_analysis_{trade_date}.png")
    plot_performance(all_data, output_file, trade_date)

    # 同时保存 CSV
    csv_file = os.path.join(output_dir, f"limit_down_analysis_{trade_date}.csv")
    summary_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    logger.info(f"数据已保存: {csv_file}")


if __name__ == "__main__":
    main()
