from loguru import logger
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from contextlib import contextmanager
from sqlalchemy import create_engine, select, update, or_
from sqlalchemy.exc import IntegrityError 
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import pandas as pd

# 连接字符串：mysql+pymysql://user:password@host:port/dbname?charset=utf8mb4
DATABASE_URL = "mysql+pymysql://root:123456@192.168.0.128:3306/instockdb?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    echo=False,           # 打印SQL（开发调试）
    pool_size=5,         # 连接池大小
    max_overflow=10,     # 超出池大小的连接数
    pool_recycle=3600,   # 连接回收时间（秒），防止MySQL超时断开（默认8小时）
    pool_pre_ping=True,   # 连接前ping测试，避免使用僵尸连接
    connect_args={
        "init_command": "SET time_zone = '+8:00'"  # 东八区
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class StockNews(Base):
    __tablename__ = "stock_news"
    
    id = Column(String(32), primary_key=True)
    title = Column(String(200), nullable=False, comment="标题 or 摘要")
    content = Column(Text, comment="内容")
    source = Column(String(20), default="财联社", comment="来源")
    
    # 情绪分析维度
    sentiment = Column(String(20), nullable=True, comment="舆情情绪")
    sentiment_basis = Column(Text, nullable=True, comment="情绪判断依据")
    
    # 行业影响维度
    affected_industry = Column(String(200), nullable=True, comment="影响行业/板块")
    impact_logic = Column(Text, nullable=True, comment="影响逻辑说明")
    
    # 标的关联
    company_name = Column(String(300), nullable=True, comment="涉及公司名称")
    symbol = Column(String(300), nullable=True, comment="股票代码")
    
    # 风险维度
    risk_focus = Column(Text, nullable=True, comment="风险与关注点")
    
    # 系统字段
    notifyed = Column(Boolean, default=False, comment="是否已通知")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, onupdate=func.now(), comment="更新时间")

    def __repr__(cls):
        return f"{cls.title}\n\n{cls.content}\n\n{cls.sentiment}\n{cls.sentiment_basis}\n\n\
            {cls.affected_industry}\n{cls.impact_logic}\n\n{cls.company_name}\n{cls.symbol}\n\n{cls.risk_focus}"
        
    
class AStockInfos(Base):
    # A股
    __tablename__ = "a_stock_infos"
    
    symbol = Column(String(20), primary_key=True, comment="股票代码")
    name = Column(String(40), nullable=True, comment="股票名称")
    jys = Column(String(4), nullable=True, comment="交易所")
    
    
# 创建表（同步）
Base.metadata.create_all(bind=engine)

# ============ 使用方式 ============

# 方法1：上下文管理器（推荐）
@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# 查
def find_record(smt):
    with Session(engine) as session:
        # 查询所有
        result = session.execute(smt)
        records = result.mappings().all()  # 返回 [dict, dict, ...]
        return records

# 增
def add_record(data):
    try:
        with Session(engine) as session:
            # 单条添加，防止出错整个回滚
            session.add(data)
            session.commit()
            logger.info("插入一条数据")
    except IntegrityError as _:
        pass
    except Exception as e:
        logger.error(e)
        
def add_records(datas):
    try:
        with Session(engine) as session:
            session.add_all(datas)
            session.commit()
    except IntegrityError as _:
        pass
    except Exception as e:
        logger.error(e)
# 删改
def exec_record(smt):
    with Session(engine) as session:
        # 查询所有
        try:
            session.execute(smt)
            session.commit()
        except Exception as e:
            logger.error(e)
            
# 清空表
def clear_record(table):
    with Session(engine) as session:
        # 查询所有
        try:
            session.query(table).delete()
            session.commit()
        except Exception as e:
            logger.error(e)