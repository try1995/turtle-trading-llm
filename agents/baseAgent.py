import os
import json
from llm import client
from loguru import logger
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from markdown import markdown
from tools.send_email import send_message


class baseAgent(ABC):
    def __init__(self):
        self.name = ""
        self.tools = []
        self.tools_regist = []
        self.tools_dict = {}
        # 回测标志
        self.backtest = False
        # 回测日期
        self.backtest_date = ""
        # 股票代码
        self.symbol = ""
    
    @abstractmethod
    def act(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def invork(self, messages, **kwargs):
        final_response_stream = client.chat.completions.create(
            model="myllm:latest",
            messages=messages,
            stream=True,
            temperature=0.1,
            **kwargs
        )
        
        final_response_stream_res = ""
        for event in final_response_stream:
            cur_content = event.choices[0].delta.content
            if cur_content:
                final_response_stream_res += cur_content
                print(cur_content, end="")
                
        return final_response_stream_res

    def invork_with_tools(self, messages):
        response = client.chat.completions.create(
            model="myllm:latest",
            messages=messages,
            tools=self.tools_regist,
            tool_choice="auto"
        )
        response_message = response.choices[0].message
        
        return response_message

    
    def act_with_tools(self, messages: list, response_message):
        # Handle function calls
        tool_call_res = []
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                fun = self.tools_dict.get(tool_call.function.name)
                if fun:
                    function_args = json.loads(tool_call.function.arguments)
                    logger.info(f"执行函数方法：{tool_call.function.name}, \
                                参数：{tool_call.function.arguments}")
                    try:
                        response = fun(**function_args)
                    except Exception as e:
                        logger.error(f"方法执行失败:{e}")
                        response = "未获得"
                    logger.debug(f"执行结果：{response}")
                    tool_call_res.append(response)
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fun.__name__,
                        "content": response,
                    })
                else:
                    logger.error(f"error fun name from model: {fun.__name__}")
        else:
            logger.info("No tool calls were made by the model.")
        
        return messages, tool_call_res
    
    def act_with_tools_stepbystep(self, messages, response_message):
        if response_message.tool_calls:
            if len(response_message.tool_calls) > 1:
                response_message.tool_calls = [response_message.tool_calls[0]]
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                fun = self.tools_dict.get(tool_call.function.name)
                if fun:
                    function_args = json.loads(tool_call.function.arguments)
                    response = fun(**function_args)
                    logger.debug(f"执行函数方法：{tool_call.function.name}, \
                                参数：{tool_call.function.arguments},\
                                执行结果：{str(response)[:500]}...")
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fun.__name__,
                        "content": response,
                    })
                    return False, messages, response
                else:
                    logger.error(f"error fun name from model: {fun.__name__}")
                    return True, messages, ""
        else:
            logger.info("No tool calls were made by the model.")
            return True, messages, ""
    
    
    def set_backtest(self, cur_date):
        self.backtest = True
        self.backtest_date = cur_date

    def set_symbol(self, symbol):
        self.symbol = symbol
    
    def get_date_desc(self):
        if self.backtest:
            xinqi = datetime.strptime(self.backtest_date, "%Y%m%d").weekday() + 1
            return f"当前时间是：{self.backtest_date}，星期{xinqi}"
        else:
            now = datetime.now()
            if datetime.now().hour < 15:
                logger.info("收盘前，改成前一天")
                now = datetime.now() - timedelta(days=1)
            xinqi = now.weekday() +1
            return f"当前时间是：{now.strftime('%Y%m%d')}，星期{xinqi}", now.strftime("%Y%m%d")
    
    @logger.catch
    def send_res_email(self, md):
        html = markdown(md)
        send_message(toaddrs=os.environ.get("toaddrs").split("|"), subject="盘后自动跑批", content=html)