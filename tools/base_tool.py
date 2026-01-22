import os
import json
import config
import inspect
from datetime import datetime
from typing import get_type_hints
from markitdown import MarkItDown
from typing import Annotated
from .all_types import EmAllagents


def get_func_schema(func):
    """
    把函数转成 OpenAI tools 格式并注册到全局列表
    """
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)

    # 构造 parameters
    properties = {}
    required = []

    for name, param in sig.parameters.items():
        # 必填性
        if param.default is inspect.Parameter.empty:
            required.append(name)

        # 类型映射：只做 str/int/float/bool 四件套，其余 fallback 到 string
        py_type = type_hints.get(name, str)
        json_type = {
            str:   "string",
            int:   "integer",
            float: "number",
            bool:  "boolean",
        }.get(py_type, "string")

        # 构造参数描述：优先用 func.__annotations__ 里的描述
        description = (
            getattr(param._annotation, "__metadata__", [None])[0] or
            f"The `{name}` parameter"
        )

        properties[name] = {
            "type": json_type,
            "description": description,
        }

    schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }

    return schema


def markdownpdf(file_path):
    md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")
    result = md.convert(file_path)
    return result.text_content


def save_response(func):
    def wrapper(self, *args, **kwargs):
        ret =  func(self, *args, **kwargs)
        date_dir = self.get_date_desc()[-1]
        os.makedirs(os.path.join(config.cache_dir, date_dir, self.symbol), exist_ok=True)
        with open(os.path.join(config.cache_dir, date_dir, self.symbol, self.name+"_"+func.__name__), "w") as f:
            if isinstance(ret, str):
                f.write(ret)
            else:
                f.write(json.dumps(ret, ensure_ascii=False, indent=4))
        return ret
    return wrapper


def get_cache(cur_date, symbol, agent_name):
    path = os.path.join(config.cache_dir, cur_date, symbol, agent_name+"_run")
    if os.path.exists(path):
        with open(path, "r") as f:
            cache_res = f.read()
        return cache_res
    else:
        return "无结果"
        

def get_agent_res(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"]
):
    """
    描述：获取agent的运行结果
    """
    data_agent_res = get_cache(cur_date, symbol, EmAllagents.dataAgent.name)
    report_agent_res = get_cache(cur_date, symbol, EmAllagents.reportAgent.name)
    public_agent_res = get_cache(cur_date, symbol, EmAllagents.publicOptionAgent.name)
    
    res = "行情及技术指标解析：" + data_agent_res + \
        "\n\n研报解析：" + report_agent_res + \
        "\n\n舆情解析：" + public_agent_res
    return res


def get_all_agent_res(symbol: Annotated[str, "股票代码，e.g. 000001"],
    cur_date: Annotated[str, "当前日期 %Y%m%d，e.g. 20210301"]
):
    res = get_agent_res(symbol, cur_date)
    invest_agent_res = get_cache(cur_date, symbol, EmAllagents.investmentAgent.name)
    
    return invest_agent_res + "\n\n*参考*\n\n" + res