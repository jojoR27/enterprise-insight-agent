# ORM模型基类,以后所有数据库模型都继承它

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass