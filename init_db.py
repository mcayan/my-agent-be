"""
数据库初始化脚本
运行此脚本以创建所有数据库表
"""
from database import engine, Base
from models.user import User


def init_db():
    """初始化数据库，创建所有表"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功！")


if __name__ == "__main__":
    init_db()

