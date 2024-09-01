from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)
    user_id = Column(BigInteger, unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    username = Column(String(100))
    registration_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    language_code = Column(String(10))
    preferred_currency = Column(String(3))
    is_banned = Column(Boolean, default=False)
    user_status = Column(String(20), default='free')
    user_role = Column(String(20), default='user')
    referral_code = Column(String(50))
    referred_by = Column(String(50))
    is_subscribed = Column(Boolean, default=True)
    daily_requests_count = Column(Integer, default=0)
    last_reset_date = Column(Date, default=datetime.utcnow().date)
    last_request_time = Column(DateTime(timezone=True))
    total_keys_generated = Column(Integer, default=0)
    notes = Column(Text)
    daily_safety_keys_requests_count = Column(Integer, default=0)
    last_reset_date_safety_keys = Column(Date, default=datetime.utcnow().date)
    last_safety_keys_request_time = Column(DateTime(timezone=True))


class UserLog(Base):
    __tablename__ = 'user_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    action = Column(Text)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
