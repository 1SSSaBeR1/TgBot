from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase



class Link(SqlAlchemyBase):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    description = Column(String)
    post = relationship('blogs', backref='links')