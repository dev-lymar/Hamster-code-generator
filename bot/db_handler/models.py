from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id: int = Column(Integer, primary_key=True)
    chat_id: int = Column(BigInteger, unique=True, nullable=False)
    user_id: int = Column(BigInteger, unique=True, nullable=False)
    first_name: Optional[str] = Column(String(100))
    last_name: Optional[str] = Column(String(100))
    username: Optional[str] = Column(String(100))
    registration_date: datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
    language_code: Optional[str] = Column(String(10))
    preferred_currency: Optional[str] = Column(String(3))
    is_banned: bool = Column(Boolean, default=False)
    user_status: str = Column(String(20), default='free')
    user_role: str = Column(String(20), default='user')
    referral_code: Optional[str] = Column(String(50))
    referred_by: Optional[str] = Column(String(50))
    is_subscribed: bool = Column(Boolean, default=True)
    daily_requests_count: int = Column(Integer, default=0)
    last_reset_date: datetime = Column(Date, default=datetime.utcnow().date)
    last_request_time: Optional[datetime] = Column(DateTime(timezone=True))
    total_keys_generated: int = Column(Integer, default=0)
    notes: Optional[str] = Column(Text)


class UserLog(Base):
    __tablename__ = 'user_logs'

    id: int = Column(Integer, primary_key=True)
    user_id: int = Column(BigInteger, nullable=False)
    action: Optional[str] = Column(Text)
    timestamp: datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
