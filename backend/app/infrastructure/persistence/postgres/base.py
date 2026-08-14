from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """PostgreSQL ORM 模型的声明式基类。"""