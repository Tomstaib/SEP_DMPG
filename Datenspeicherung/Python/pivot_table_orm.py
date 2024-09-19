from sqlalchemy import Column, ForeignKey, Integer, String, Float, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class PivotTable(Base):
    __tablename__ = 'pivot_table'
    id = Column(Integer, primary_key=True)
    type = Column(String(255))
    name = Column(String(255))
    stat = Column(String(255))
    average = Column(Float)
    minimum = Column(Float)
    maximum = Column(Float)
    half_width = Column(Float)
