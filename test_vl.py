import requests
import os
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
import os
from openai import OpenAI

client = OpenAI(
    # 各地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    api_key=os.getenv("api_key"),
    # 以下为北京地域的 base_url，若使用弗吉尼亚地域模型，需要将base_url换成https://dashscope-us.aliyuncs.com/compatible-mode/v1
    # 若使用新加坡地域的模型，需将base_url替换为：https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

import base64

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
                
