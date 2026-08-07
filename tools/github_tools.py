# GitHub Actions 工作流/变量管理工具
# 通过 GitHub API 触发工作流、读写仓库级环境变量
import os
import json
import requests
from typing import Annotated
from loguru import logger

# 从 .env 读取 token，只支持单个 token
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# 默认仓库
DEFAULT_OWNER = "try1995"
DEFAULT_REPO = "github-actions"


def _github_request(method, url, data=None):
    """发送 GitHub API 请求。"""
    if not GITHUB_TOKEN:
        return None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
    }
    return requests.request(method, url, headers=headers, json=data)


def github_dispatch_workflow(
    event_type: Annotated[str, "事件类型，工作流中通过 github.event.action 或 grep 匹配，e.g. curl-event"],
    owner: Annotated[str, "GitHub 仓库所属用户名，默认 try1995"] = DEFAULT_OWNER,
    repo: Annotated[str, "GitHub 仓库名，默认 github-actions"] = DEFAULT_REPO,
):
    """
    描述：触发指定 GitHub 仓库的 Actions 工作流（workflow_dispatch），返回触发结果。
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/dispatches"
    data = {"event_type": event_type}
    resp = _github_request("POST", url, data=data)
    if resp is None:
        return "未配置 GITHUB_TOKEN"
    if resp.status_code == 204:
        return f"工作流已触发成功：{event_type}"
    try:
        return json.dumps(resp.json(), ensure_ascii=False)
    except Exception:
        return resp.text


def github_get_repo_variable(
    var_name: Annotated[str, "仓库环境变量名，e.g. STOCK_CODE"],
    owner: Annotated[str, "GitHub 仓库所属用户名，默认 try1995"] = DEFAULT_OWNER,
    repo: Annotated[str, "GitHub 仓库名，默认 github-actions"] = DEFAULT_REPO,
):
    """
    描述：获取指定 GitHub 仓库 Actions 的环境变量值（仓库级 variables），返回变量名与值。
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/variables/{var_name}"
    resp = _github_request("GET", url)
    if resp is None:
        return "未配置 GITHUB_TOKEN"
    if resp.status_code == 200:
        data = resp.json()
        return json.dumps({"name": data.get("name"), "value": data.get("value")}, ensure_ascii=False)
    try:
        return json.dumps(resp.json(), ensure_ascii=False)
    except Exception:
        return resp.text


def github_update_repo_variable(
    var_name: Annotated[str, "仓库环境变量名，e.g. STOCK_CODE"],
    var_value: Annotated[str, "新的变量值，多个值用|分隔，e.g. 601601|000001"],
    owner: Annotated[str, "GitHub 仓库所属用户名，默认 try1995"] = DEFAULT_OWNER,
    repo: Annotated[str, "GitHub 仓库名，默认 github-actions"] = DEFAULT_REPO,
):
    """
    描述：修改指定 GitHub 仓库 Actions 的环境变量值（仓库级 variables），返回修改结果。
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/variables/{var_name}"
    data = {"name": var_name, "value": var_value}
    resp = _github_request("PATCH", url, data=data)
    if resp is None:
        return "未配置 GITHUB_TOKEN"
    if resp.status_code == 204:
        return f"变量 {var_name} 已更新为：{var_value}"
    try:
        return json.dumps(resp.json(), ensure_ascii=False)
    except Exception:
        return resp.text


def github_stock_analysis(
    symbol: Annotated[str, "股票代码，多个用|分隔，e.g. 601601|000001"],
    var_name: Annotated[str, "仓库环境变量名，默认 STOCK_CODE"] = "STOCK_CODE",
    event_type: Annotated[str, "事件类型，工作流中通过 github.event.action 或 grep 匹配，e.g. curl-event"] = "curl-event",
    owner: Annotated[str, "GitHub 仓库所属用户名，默认 try1995"] = DEFAULT_OWNER,
    repo: Annotated[str, "GitHub 仓库名，默认 github-actions"] = DEFAULT_REPO,
):
    """
    描述：股票分析流程。先把股票代码写入仓库环境变量（默认 STOCK_CODE），再触发 Actions 工作流进行股票分析，返回两步的结果。
    """
    # 1. 先设置股票代码
    set_res = github_update_repo_variable(var_name, symbol, owner, repo)
    logger.info(f"设置 {var_name}: {set_res}")
    # 2. 再触发工作流
    dispatch_res = github_dispatch_workflow(event_type, owner, repo)
    logger.info(f"触发工作流: {dispatch_res}")
    return json.dumps({"set_variable": set_res, "dispatch": dispatch_res}, ensure_ascii=False)
