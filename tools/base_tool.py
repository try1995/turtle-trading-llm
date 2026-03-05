import os
import json
import config
import inspect
import requests
from hashlib import md5
from typing import get_type_hints
from markitdown import MarkItDown
from typing import Annotated
from .all_types import EmAllagents
from readability import Document
from bs4 import BeautifulSoup
from loguru import logger
import pymupdf # imports the pymupdf library



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
    result = ""
    try:
        md = MarkItDown(docintel_endpoint="<document_intelligence_endpoint>")
        result = md.convert(file_path)
        return result.text_content
    except Exception as e:
        logger.error(e)
    if not result:
        try:
            doc = pymupdf.open(file_path) # open a document
            for page in doc: # iterate the document pages
                result += page.get_text() #
            return result
        except Exception as e:
            logger.error(e)
    return "未抽取到结果"

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

def save_func_response(params, ret):
    
    # 创建一个md5对象
    obj = md5()

    # 更新哈希对象，这里需要将字符串转换为字节
    obj.update(params.encode("utf-8"))

    # 获取十六进制格式的哈希值
    md5_file_name = obj.hexdigest()
    with open(os.path.join(config.cache_dir, "cache", md5_file_name), "w") as f:
        f.write(ret)

def get_func_response(params):
    # 创建一个md5对象
    obj = md5()

    # 更新哈希对象，这里需要将字符串转换为字节
    obj.update(params.encode("utf-8"))

    # 获取十六进制格式的哈希值
    md5_file_name = obj.hexdigest()
    
    os.makedirs(os.path.join(config.cache_dir, "cache"), exist_ok=True)
    file_path = os.path.join(config.cache_dir, "cache", md5_file_name)
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            data = f.read()
            return data

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


def fetch_url_content(url):
    """
    # 描述：爬取url的内容
    """
    HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
    html = requests.get(url, headers=HEADERS, timeout=10).text
    doc = Document(html)
    main_html = doc.summary(html_partial=True)

    soup = BeautifulSoup(main_html, "html.parser")
    return soup.get_text(separator="\n", strip=True)


def push_server_jio(title, desp):
    SENDKEY = os.environ.get("SERVER_JIO_KEY","")
    if SENDKEY:
        push_url = f'https://sctapi.ftqq.com/{SENDKEY}.send'
        data = {'title': title, 'desp': desp}
        requests.post(push_url, data=data)


def get_a_symbol_info(symbol):
    # 只有A股信息
    from .sql_utils import select, AStockInfos, find_record
    smt = select(AStockInfos).where(AStockInfos.symbol==symbol)
    records = find_record(smt)
    if records:
        res: AStockInfos = records[0]["AStockInfos"]
        return res.name, res.symbol, res.jys
    return None


def get_market(code: str) -> str:
    """返回 'sh' / 'sz' / 'bj'"""
    code = code.strip()
    if code.startswith(('6', '9')):          # 6xxxxxx、900xxx
        return 'sh'
    if code.startswith(('0', '3')):          # 0xxxxxx、3xxxxxx
        return 'sz'
    # 其余按北交所处理（8xxxxxx 或 8 位代码）
    return 'bj'