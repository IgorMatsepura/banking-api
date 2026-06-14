from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime

DATABASE_URL = "sqlite:///./banking.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Моделі
class CustomerDB(Base):
    __tablename__ = "customers"
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True)
    hashed_password = Column(String)

class AccountDB(Base):
    __tablename__ = "accounts"
    account_id = Column(String, primary_key=True, default=lambda: f"acc-{uuid.uuid4().hex[:8]}")
    customer_id = Column(Integer)
    balance = Column(Float)
    currency = Column(String, default="UAH")

class TransferDB(Base):
    __tablename__ = "transfers"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_account_id = Column(String)
    to_account_id = Column(String)
    amount = Column(Float)
    currency = Column(String, default="UAH")
    created_at = Column(DateTime, default=datetime.now)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
