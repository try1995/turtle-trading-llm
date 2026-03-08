import os
import requests
import json
from tools import *
from dotenv import load_dotenv

load_dotenv()

# ret = zt_stock_latest_price("000001")
# ret = zt_stock_hist_price("000001",start_date="20251201", end_date="20260227")
# ret = zt_stock_indicators("000001",start_date="20251201", end_date="20260227")
# ret = zt_stock_info("000001")
# ret = zt_stock_kdj("000001","20260101", "20260305")
ret = zt_pool_dtgc("2026-03-04")
print(ret)