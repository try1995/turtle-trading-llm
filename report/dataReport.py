from typing import List
from pydantic import BaseModel


class Paragraph0(BaseModel):
    """报告中单个段落的状态"""
    title: str                                                     # 段落标题
    detail: str                                                    # 内容描述
    content: str = ""                                              # 生成的内容
    is_completed: bool = False             
    
class Paragraph1(BaseModel):
    report_title: str = ""                                         # 报告标题
    paragraphs: List[Paragraph0]                                    # 段落列表
    is_completed: bool = False                                     # 是否完成
    

from typing import List
from pydantic import BaseModel


class Paragraph0(BaseModel):
    """二级段落"""
    title: str                # 段落标题
    detail: str               # 内容描述
    content: str = ""         # 生成的内容
    is_completed: bool = False


class Paragraph1(BaseModel):
    """一级段落"""
    report_title: str         # 报告标题
    paragraphs: List[Paragraph0]  # 段落列表
    is_completed: bool = False   # 是否完成

    # ========== 新增：转 Markdown ==========
    def to_markdown(self) -> str:
        """把当前 Report 转成 Markdown 多级列表"""
        lines = [f"### {self.report_title}"]
        for p in self.paragraphs:
            lines.append(f"- **{p.title}**：\n{p.content}")
        return "\n".join(lines)
    

class Report(BaseModel):
    report_name: str
    report: List[Paragraph1] = []

    def to_markdown(self) -> str:
        lines = [f"## {self.report_name}"]
        for paragraph in self.report:
            lines.append(paragraph.to_markdown())
        return "\n\n".join(lines)

class DataReport(Report):
    report_name: str = "DataReport"

data_report = DataReport(
    report=[
        Paragraph1(
            report_title="一、基本面数据",
            paragraphs=[
                Paragraph0(title="财务报表", detail="分析财务报表"),
                Paragraph0(title="关键指标", detail="分析营收增长率、净利润率、ROE、ROA、毛利率、负债率"),
                Paragraph0(title="盈利能力", detail="EPS（每股收益）、PE（市盈率）、PB（市净率）、PEG"),
                Paragraph0(title="现金流", detail="经营现金流、自由现金流、资本支出"),
                Paragraph0(title="股东回报", detail="分红历史、股息率、股票回购记录"),
            ]
        ),
        Paragraph1(
            report_title="二、技术面数据（价格行为）",
            paragraphs=[
                Paragraph0(title="价格数据", detail="最新的开盘价、收盘价、最高价、最低价、成交量等数据"),
                Paragraph0(title="技术指标", detail="技术指标分析"),
                Paragraph0(title="形态数据", detail="k线形态识别"),
            ]
        ),
        Paragraph1(
            report_title="三、行业与竞争数据（市场地位）",
            paragraphs=[
                Paragraph0(title="行业指标", detail="行业增长率、平均利润率、市场规模"),
                Paragraph0(title="竞争格局", detail="市场份额、竞争对手对比、行业壁垒"),
                # Paragraph0(title="产业链", detail="上下游关系、供应商/客户集中度"),
                # Paragraph0(title="行业政策", detail="监管政策、补贴、准入门槛"),
            ]
        ),
        # Report(
        #     report_title="四、宏观经济数据（大环境）",
        #     paragraphs=[
        #         Paragraph(title="经济指标", detail="GDP增长率、CPI/PPI、利率水平、汇率"),
        #         Paragraph(title="货币政策", detail="央行政策、货币供应量、信贷政策"),
        #         Paragraph(title="市场情绪", detail="市场整体估值、融资融券余额、投资者情绪指数"),
        #     ]
        # ),
        # Report(
        #     report_title="五、公司治理数据（风险因素）",
        #     paragraphs=[
        #         Paragraph(title="股权结构", detail="大股东持股比例、机构持仓、管理层持股"),
        #         Paragraph(title="管理层", detail="高管背景、薪酬结构、历史业绩"),
        #         Paragraph(title="风险事件", detail="法律诉讼、监管处罚、关联交易"),
        #         Paragraph(title="ESG评级", detail="环境、社会责任、公司治理评分"),
        #     ]
        # ),
        # Report(
        #     report_title="六、市场预期数据（情绪面）",
        #     paragraphs=[
        #         Paragraph(title="分析师预测", detail="一致预期、评级变化、目标价调整"),
        #         Paragraph(title="研报数据", detail="机构研报数量、核心观点"),
        #         Paragraph(title="机构动向", detail="北向资金、龙虎榜、大宗交易"),
        #     ]
        # ),
        # Report(
        #     report_title="七、特色数据（辅助判断）",
        #     paragraphs=[
        #         Paragraph(title="舆情数据", detail="新闻情绪、社交媒体热度、突发事件"),
        #         Paragraph(title="另类数据", detail="卫星图像、供应链数据、招聘数据、App下载量"),
        #         Paragraph(title="期权数据", detail="认沽认购比、隐含波动率"),
        #     ]
        # ),
])