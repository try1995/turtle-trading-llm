import os
from loguru import logger
from llm import client
from copy import deepcopy
from prompt import sys_plan_prompt
from .dataAgent import DataAgent
from .reportAgent import ReportAgent
from .publicOptionAgent import PublicOptionAgent
from .baseAgent import baseAgent
from .InvestmentAgent import InvestmentAgent
from json_repair import repair_json
from tools.all_types import EmAllagents
from tools.base_tool import get_cache, get_all_agent_res, save_response


class PlanAgent(baseAgent):
    def __init__(self):
        super().__init__()
        self.name = EmAllagents.planAgent.name
        self.model = os.environ.get(self.name+"Model", self.model)
        self.agent = [DataAgent, ReportAgent, PublicOptionAgent]
        self.agent_dict:dict[str, baseAgent] = {
            EmAllagents.dataAgent.name:DataAgent(), 
            EmAllagents.reportAgent.name:ReportAgent(),
            EmAllagents.publicOptionAgent.name:PublicOptionAgent(),
            EmAllagents.investmentAgent.name: InvestmentAgent()}
        self.agent_res = {}
        self.last_invest_suggestion = ""
        self.use_cache = True

    def set_symbol(self, symbol, name):
        super().set_symbol(symbol, name)
        for _, v in self.agent_dict.items():
            v.set_symbol(symbol, name)
    
    def set_backtest(self, cur_date, last_invest_suggestion="无", use_cache=True):
        self.backtest = True
        self.use_cache = use_cache
        self.backtest_date = cur_date
        self.last_invest_suggestion = last_invest_suggestion
        for _, v in self.agent_dict.items():
            v.set_backtest(cur_date)
        
    def invork(self, message, human_in_loop):
        messages = [
            {"role": "system", "content": sys_plan_prompt},
            {
                "role": "user",
                "content": message
            },
        ]
        stream = client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        plan = ""
        for event in stream:
            cur_content = event.choices[0].delta.content
            if cur_content:
                plan += cur_content
                print(cur_content, end="")
        
        if human_in_loop:
            while True:
                __messages = deepcopy(messages)
                human_input = input("\n\nneed replan? or give advice. if not, just input no\n\n")
                logger.debug(human_input)
                if human_input.strip().lower() != "no":
                    __messages.extend([
                        {
                            "role":"assistant",
                            "content": f"Previous plan - {plan}"
                        },
                        {
                            "role":"user",
                            "content":human_input
                        }]
                    )
                    stream = client.chat.completions.create(
                        model=self.model,
                        messages=__messages,
                        stream=True,
                    )
                    plan = ""
                    for event in stream:
                        cur_content = event.choices[0].delta.content
                        if cur_content:
                            plan += cur_content
                            print(cur_content, end="")
                else:
                    break
        return plan

    
    def get_cache_res(self, symbol, agent_name):
        res = get_cache(self.get_date_desc()[1], symbol, agent_name)
        if res != "无结果":
            logger.info(f"{agent_name}：load cache successfully!!!")
        return res
            
    def act(self, plans):
        # 这是一个pipeline
        for plan in plans:
            name, symbol = plan["name"], plan["symbol"].split(".")[0]
            self.set_symbol(symbol, name)
            for task in plan["tasks"]:
                agent_name, agent_task = task['assigned_agent'], task['task_details']
                agent = self.agent_dict[agent_name]
                if self.use_cache:
                    agent_res = self.get_cache_res(self.symbol, agent_name)
                    if agent_res == "无结果":
                        agent_res = agent.run(agent_task)
                else:
                    agent_res = agent.run(agent_task)
                self.agent_res[agent_name] = agent_res
                logger.info("*"*99)
                
    @logger.catch
    @save_response
    def run(self, question, human_in_loop=False, use_cache=True, symbol=""):
        logger.info(f"{self.name}：当前执行任务：{question}")
        self.use_cache = use_cache
        self.symbol = symbol
        if self.use_cache:
            agent_res = self.get_cache_res(self.symbol, self.name)
            if agent_res == "无结果":
                plan_raw = self.invork(question, human_in_loop)
            else:
                plan_raw = agent_res
        else:
            plan_raw = self.invork(question, human_in_loop)
        plans = repair_json(plan_raw, return_objects=True)
        self.act(plans)
        return plan_raw


    def send_allres_email(self, subject):
        cur_date = self.get_date_desc()[1]
        hight_format = """\n\n### <span style="color: red;">{agent} POWER BY {model} </span>\n\n"""
        invest_agent_res = get_cache(cur_date, self.symbol, EmAllagents.investmentAgent.name)
        invest_agent_res += hight_format.format(agent=EmAllagents.investmentAgent.name, model=self.agent_dict[EmAllagents.investmentAgent.name].model)
        data_agent_res = get_cache(cur_date, self.symbol, EmAllagents.dataAgent.name)
        data_agent_res += hight_format.format(agent=EmAllagents.dataAgent.name, model=self.agent_dict[EmAllagents.dataAgent.name].model)
        report_agent_res = get_cache(cur_date, self.symbol, EmAllagents.reportAgent.name)
        report_agent_res += hight_format.format(agent=EmAllagents.reportAgent.name, model=self.agent_dict[EmAllagents.reportAgent.name].model)
        public_agent_res = get_cache(cur_date, self.symbol, EmAllagents.publicOptionAgent.name)
        public_agent_res += hight_format.format(agent=EmAllagents.publicOptionAgent.name, model=self.agent_dict[EmAllagents.publicOptionAgent.name].model)
    
        md = "\n\n# 投资建议：\n" + invest_agent_res+\
            "\n\n\n# 行情及技术指标解析：\n" + data_agent_res + \
            "\n\n# 研报解析：\n" + report_agent_res + \
            "\n\n# 舆情解析：\n" + public_agent_res
        self.send_res_email(md, subject, table=True)