from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .db_session import SqlAlchemyBase



class Link(SqlAlchemyBase):
    __tablename__ = 'links'

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    description: Mapped[str]=mapped_column(nullable=True)
    is_complited: Mapped[bool] = mapped_column(server_default=False)
    #post = relationship('blogs', backref='links')
