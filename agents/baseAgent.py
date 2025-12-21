import json
from llm import client
from loguru import logger


class baseAgent:
    def __init__(self):
        self.tools = []
        self.tools_regist = []
        self.tools_dict = {}
    
    def invork_with_tools(self, messages):
        response = client.chat.completions.create(
            model="myllm:latest",
            messages=messages,
            tools=self.tools_regist,
            tool_choice="auto",
        )
        response_message = response.choices[0].message

        
        # Handle function calls
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                fun = self.tools_dict.get(tool_call.function.name)
                if fun:
                    function_args = json.loads(tool_call.function.arguments)
                    response = fun(**function_args)
                    logger.debug(f"执行函数方法：{tool_call.function.name}, \
                                参数：{tool_call.function.arguments},\
                                执行结果：{response}")
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

        # Second API call: Get the final response from the model
        final_response_stream = client.chat.completions.create(
            model="myllm:latest",
            messages=messages,
            stream=True,
        )
        
        final_response_stream_plan = ""
        for event in final_response_stream:
            cur_content = event.choices[0].delta.content
            if cur_content:
                final_response_stream_plan += cur_content
                print(cur_content, end="")

        return final_response_stream_plan
    
    
    def invork_with_tools_stepbystep(self, messages, max_step=10):
        while max_step:
            response = client.chat.completions.create(
                model="myllm:latest",
                messages=messages,
                tools=self.tools_regist,
                tool_choice="auto",
            )
            response_message = response.choices[0].message

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
                                    执行结果：{response}")
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": fun.__name__,
                            "content": response,
                        })
                        max_step -= 1
                    else:
                        logger.error(f"error fun name from model: {fun.__name__}")
            else:
                logger.info("No tool calls were made by the model.")  
                break

        # Second API call: Get the final response from the model
        final_response_stream = client.chat.completions.create(
            model="myllm:latest",
            messages=messages,
            stream=True,
        )
        
        final_response_stream_plan = ""
        for event in final_response_stream:
            cur_content = event.choices[0].delta.content
            if cur_content:
                final_response_stream_plan += cur_content
                print(cur_content, end="")

        return final_response_stream_plan