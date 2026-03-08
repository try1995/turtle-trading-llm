import json
import base64
from llm import client
from loguru import logger
from prompt import sys_tool_prompt, sys_vl_prompt
from .baseAgent import baseAgent
from tools.all_types import EmAllagents
from tools import *
from json_repair import repair_json


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


class VlAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.tools = [zt_stock_latest_price, zt_stock_hist_price]
        self.name = EmAllagents.vlAgent.name
        self.model = os.environ.get(self.name+"Model", self.model)
        self.tools_regist = [get_func_schema(func) for func in self.tools]
        self.tools_dict = {fun.__name__:fun for fun in self.tools}
    
    @save_response
    def act(self, messages, response_message):
        messages, tool_call_res = self.act_with_tools(messages, response_message)
        return tool_call_res

    
    @save_response
    def run(self, question):
        logger.info(f"{self.name}：当前执行任务：{self.symbol_name} {question}")
        messages = [
            {"role": "system", "content": sys_tool_prompt},
            {
                "role": "user",
                "content": self.get_date_desc()[0]
            },
            {
                "role": "user",
                "content": f"{question}：{self.symbol_name}({self.symbol})"
            }
        ]
        response_message = self.invork_with_tools(messages)
        tool_call_res = self.act(messages, response_message)
        res_str = '\n\n'.join(tool_call_res)
        symbol = get_market(self.symbol) + self.symbol
        new_messages=[
            {"role": "system", "content": sys_vl_prompt},
            {"role": "user","content": [
                {"type": "image_url","image_url": {"url": url_to_base64(f"http://image.sinajs.cn/newchart/min/n/{symbol}.gif")},},
                {"type": "image_url","image_url": {"url": url_to_base64(f"http://image.sinajs.cn/newchart/daily/n/{symbol}.gif")},},
                {"type": "image_url","image_url": {"url": url_to_base64(f"http://image.sinajs.cn/newchart/weekly/n/{symbol}.gif")},},
                {"type": "image_url","image_url": {"url": url_to_base64(f"http://image.sinajs.cn/newchart/monthly/n/{symbol}.gif")},},
                {"type": "text", "text": f"{self.get_date_desc()[0]}, 根据用户上传的图片信息，分析股票的趋势信息。\n\n参考信息如下：{res_str}"}],
            }
        ]
        response_stream_res = self.invork(new_messages)
        return response_stream_res