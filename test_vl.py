import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

def download_stock_chart(stock_code, chart_type='daily', save_path='./charts'):
    """
    下载股票图表图片（新浪源）
    chart_type: min(分时), daily(日K), weekly(周K), monthly(月K)
    """
    # 判断市场
    if stock_code.startswith('6'):
        market = 'sh'  # 上海
    else:
        market = 'sz'  # 深圳

    # 新浪图表API（现成的图片URL）
    chart_urls = {
        'min': f'http://image.sinajs.cn/newchart/min/n/{market}{stock_code}.gif',
        'daily': f'http://image.sinajs.cn/newchart/daily/n/{market}{stock_code}.gif',
        'weekly': f'http://image.sinajs.cn/newchart/weekly/n/{market}{stock_code}.gif',
        'monthly': f'http://image.sinajs.cn/newchart/monthly/n/{market}{stock_code}.gif'
    }

    url = chart_urls.get(chart_type)
    if not url:
        print(f"不支持的图表类型: {chart_type}")
        return None

    # 下载图片
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            # 保存图片
            os.makedirs(save_path, exist_ok=True)
            filename = f"{market}{stock_code}_{chart_type}.gif"
            filepath = os.path.join(save_path, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"✅ 成功下载: {filename}")
            return filepath
        else:
            print(f"❌ 下载失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 下载出错: {e}")
        return None

stock = "601601"

# # 下载分时图
# download_stock_chart(stock, 'min')

# # 下载日K线图
# download_stock_chart(stock, 'daily')

# # 下载周K线图
# download_stock_chart(stock, 'weekly')

# # 下载月K线图
# download_stock_chart(stock, 'monthly')


# ── 多 Key 自动切换调用 LLM ────────────────────────────────────────
from openai import OpenAI
from llm_factory import ALL_API_KEYS, is_quota_error

base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def _create_client(key_index: int) -> OpenAI:
    """创建指定 Key 索引的 OpenAI 客户端 (v2 兼容)。"""
    return OpenAI(
        api_key=ALL_API_KEYS[key_index] if ALL_API_KEYS else os.getenv("api_key"),
        base_url=base_url,
    )


client = _create_client(0)


def url_to_base64(image_url):
    """将图片 URL 转换为 base64 编码"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
    }
    response = requests.get(image_url, headers=headers, timeout=30)
    response.raise_for_status()

    content_type = response.headers.get('content-type', 'image/jpeg')
    base64_data = base64.b64encode(response.content).decode('utf-8')

    return f"data:{content_type};base64,{base64_data}"


# 自动重试：配额耗尽时切换到下一个 Key
last_error = None
for key_idx in range(len(ALL_API_KEYS)):
    try:
        if key_idx > 0:
            client.close()
            client = _create_client(key_idx)

        final_response_stream = client.chat.completions.create(
            model="qwen3.5-plus", # 此处以qwen3.5-plus为例，可按需更换模型名称。模型列表：https://help.aliyun.com/zh/model-studio/models
            # model="qwen3-vl-plus",
            messages=[
               {"role": "user","content": [
                   {"type": "image_url","image_url": {"url": url_to_base64("http://image.sinajs.cn/newchart/min/n/sh601601.gif")}},
                   {"type": "image_url","image_url": {"url": url_to_base64("http://image.sinajs.cn/newchart/daily/n/sh601601.gif")}},
                   {"type": "image_url","image_url": {"url": url_to_base64("http://image.sinajs.cn/newchart/weekly/n/sh601601.gif")}},
                   {"type": "image_url","image_url": {"url": url_to_base64("http://image.sinajs.cn/newchart/monthly/n/sh601601.gif")}},
                   {"type": "text", "text": "对这只股票走势进行分析"},
                    ],
                }
            ],
            stream=True,
        )

        final_response_stream_res = ""
        for event in final_response_stream:
            cur_content = event.choices[0].delta.content
            if cur_content:
                final_response_stream_res += cur_content
                print(cur_content, end="")
        break  # 成功，退出重试循环
    except Exception as e:
        last_error = e
        if is_quota_error(e) and key_idx < len(ALL_API_KEYS) - 1:
            print(f"\n[WARN] API key {key_idx} 配额耗尽，尝试下一个 Key...")
            continue
        # 非配额错误或所有 Key 已耗尽
        if is_quota_error(e):
            print(f"\n[ERROR] 所有 API Key 已耗尽！")
        raise
