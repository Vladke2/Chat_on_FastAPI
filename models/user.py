from . import Base
from sqlalchemy import Column, String, Integer


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, index=True)
    hashed_password = Column(String)
