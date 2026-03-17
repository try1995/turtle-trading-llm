from enum import Enum
from pydantic import BaseModel

class EmAllagents(Enum):
    planAgent = -1
    
    dataAgent = 0
    reportAgent = 1
    publicOptionAgent = 2
    investmentAgent = 3
    xuanguAgent=4
    vlAgent=5   # 视觉理解agent

class Tenant(BaseModel):
    name: str = "总裁"
    toaddrs: str
    exclude_symbol: str
    position_symbol: str