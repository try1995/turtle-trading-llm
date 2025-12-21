import inspect
from typing import get_type_hints, Optional, Any, List, Dict, Annotated
from markitdown import MarkItDown

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


from datetime import datetime

def get_date_desc():
    """
    获取当前时间描述，返回当前日期和星期几
    """
    now = datetime.now().strftime("%Y%m%d %H:%M:%S")
    xinqi = datetime.now().weekday() +1
    return f"当前时间是：{now}， 星期{xinqi}"


def markdownpdf(file_path):
    md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")
    result = md.convert(file_path)
    return result.text_content
