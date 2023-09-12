from .sql import Base
from sqlalchemy import DATE, TIMESTAMP, Column, Integer, String, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    uid = Column(String(100), primary_key=True)
    First_Name = Column(String(100), nullable=False)
    Last_Name = Column(String(100), nullable=False)
    Email = Column(String(200), nullable=False)
    Phone = Column(Integer)

    Current_Balance = Column(Integer)

    Account_Status = Column(Integer)
    
    created_date = Column(DATE, nullable=False, server_default=func.now())
    time_updated = Column(TIMESTAMP(timezone=True), onupdate=func.now())

# class Driver(Base):
#     __tablename__ = "drivers"

#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     driver_first_name = Column(String(200), nullable=False)
#     driver_last_name = Column(String(200), nullable=False)
#     driver_ID = Column(Integer, nullable=False)
#     driver_email = Column(String(200), nullable=False)
#     driver_phone = Column(String(15), nullable=False)

#     created_date = Column(DATE, nullable=False, server_default=func.now())
#     time_updated = Column(TIMESTAMP(timezone=True), onupdate=func.now())

#     cab = relationship('Cab', back_populates='driver', uselist=False, cascade='all, delete-orphan')