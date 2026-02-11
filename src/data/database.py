from __future__ import annotations
"""
修仙文字MUD - 数据库连接和会话管理
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from contextlib import contextmanager
from typing import Generator
import os

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///xiuxian_wuxia.db"
)

# 创建引擎和会话
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """初始化数据库"""
    from src.models import player, sect, item, monster, quest, transaction
    from src.models.player import Player, CultivationStage, SectType
    from src.models.sect import Sect
    from src.models.item import Item, ItemQuality, ItemCategory
    from src.models.monster import Monster
    from src.models.quest import Quest
    from src.models.transaction import Transaction
    
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """获取数据库会话"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
