"""
搜索工具实现
支持多种搜索引擎，主要使用Tavily搜索
"""

import os
import json
from typing import List, Dict, Any, Optional, Annotated
from dataclasses import dataclass
from tavily import TavilyClient
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str
    url: str
    content: str
    score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "score": self.score
        }


class TavilySearch:
    """Tavily搜索客户端封装"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Tavily搜索客户端
        
        Args:
            api_key: Tavily API密钥，如果不提供则从环境变量读取
        """
        if api_key is None:
            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                raise ValueError("Tavily API Key未找到！请设置TAVILY_API_KEY环境变量或在初始化时提供")
        
        self.client = TavilyClient(api_key=api_key)
    
    def search(self, query: str, max_results: int = 5, include_raw_content: bool = True, 
               timeout: int = 240) -> List[SearchResult]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
            max_results: 最大结果数量
            include_raw_content: 是否包含原始内容
            timeout: 超时时间（秒）
            
        Returns:
            搜索结果列表
        """
        try:
            # 调用Tavily API
            response = self.client.search(
                query=query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                timeout=timeout
            )
            
            # 解析结果
            results = []
            if 'results' in response:
                for item in response['results']:
                    result = SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        content=item.get('content', ''),
                        score=item.get('score')
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.debug(f"搜索错误: {str(e)}")
            return []


# 全局搜索客户端实例
_tavily_client = None


def get_tavily_client() -> TavilySearch:
    """获取全局Tavily客户端实例"""
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilySearch()
    return _tavily_client


def tavily_search(query: str, max_results: int = 5, include_raw_content: bool = True, 
                  timeout: int = 240, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    便捷的Tavily搜索函数
    
    Args:
        query: 搜索查询
        max_results: 最大结果数量
        include_raw_content: 是否包含原始内容
        timeout: 超时时间（秒）
        api_key: Tavily API密钥，如果提供则使用此密钥，否则使用全局客户端
        
    Returns:
        搜索结果字典列表，保持与原始经验贴兼容的格式
    """
    try:
        if api_key:
            # 使用提供的API密钥创建临时客户端
            client = TavilySearch(api_key)
        else:
            # 使用全局客户端
            client = get_tavily_client()
        
        results = client.search(query, max_results, include_raw_content, timeout)
        
        # 转换为字典格式以保持兼容性
        return [result.to_dict() for result in results]
        
    except Exception as e:
        logger.debug(f"搜索功能调用错误: {str(e)}")
        return []


def symbol_tavily_search(
    symbol: Annotated[str, "股票代码，e.g. 000001"],
    symbol_name: Annotated[str, "股票名称，e.g. 平安银行"]
):
    """
    描述：实时搜索引擎，查询个股相关舆情信息
    """
    keywords = [
        f"{symbol} {symbol_name} 新闻 最新",
        # f"{symbol} {symbol_name} 公告 深交所",
        # f"{symbol} {symbol_name} 微博 讨论",
        f"{symbol} {symbol_name} 雪球 股吧"
    ]
    all_res = []
    for kw in keywords:
        try:
            results = tavily_search(kw, max_results=5)
            
            if results:
                logger.debug(f"\ntavily: {kw} 找到 {len(results)} 个结果:")
                for i, result in enumerate(results, 1):
                    res = {}
                    logger.debug(f"\n结果 {i}:")
                    logger.debug(f"标题: {result['title']}")
                    logger.debug(f"链接: {result['url']}")
                    logger.debug(f"内容摘要: {result['content'][:200]}...")
                    if result.get('score'):
                        logger.debug(f"相关度评分: {result['score']}")
                        
                    res["标题"] = result['title']
                    res["内容摘要"] = result['content']
                    res["相关度评分"] = result.get('score',"")
                    all_res.append(res)
                
            else:
                logger.debug("未找到搜索结果")
            
        except Exception as e:
            logger.debug(f"搜索测试失败: {str(e)}")
        
    return json.dumps(all_res, ensure_ascii=False)

def test_search():
    """
    测试搜索功能
    
    """
    logger.debug(f"\n=== 测试Tavily搜索功能 ===")
    
    
    results = symbol_tavily_search("000001", "平安银行")
    
    print(results)


if __name__ == "__main__":
    # 运行测试
    test_search()
