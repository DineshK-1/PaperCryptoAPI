from .sql import Base
from sqlalchemy import DATE, TIMESTAMP, Column, Integer, String, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    uid = Column(String(100), primary_key=True)
    First_Name = Column(String(100), nullable=False)
    Last_Name = Column(String(100), nullable=False)
    Email = Column(String(200), nullable=False)
    Phone = Column(String(20))

    Current_Balance = Column(Integer)

    Account_Status = Column(Integer)
    
    created_date = Column(DATE, nullable=False, server_default=func.now())
    time_updated = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    transactions_account = relationship('AccountTransactions', backref='user')

class AccountTransactions(Base):

    __tablename__ = "transactions_accounts"

    transaction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(100), ForeignKey("users.uid"))
    transaction_type = Column(String(50), nullable=False)
    amount = Column(String(30))

    transaction_time = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

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