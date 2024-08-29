from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class GameTableBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    promo_code = Column(Text, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class BikeRide3D(GameTableBase):
    __tablename__ = 'bike_ride_3d'
    __table_args__ = (
        Index('ix_bike_ride_3d_promo_code', 'promo_code'),
    )


class ChainCube2048(GameTableBase):
    __tablename__ = 'chain_cube_2048'
    __table_args__ = (
        Index('ix_chain_cube_2048_promo_code', 'promo_code'),
    )


class TrainMiner(GameTableBase):
    __tablename__ = 'train_miner'
    __table_args__ = (
        Index('ix_train_miner_promo_code', 'promo_code'),
    )


class MergeAway(GameTableBase):
    __tablename__ = 'merge_away'
    __table_args__ = (
        Index('ix_merge_away_promo_code', 'promo_code'),
    )


class TwerkRace3D(GameTableBase):
    __tablename__ = 'twerk_race_3d'
    __table_args__ = (
        Index('ix_twerk_race_3d_promo_code', 'promo_code'),
    )


class Polysphere(GameTableBase):
    __tablename__ = 'polysphere'
    __table_args__ = (
        Index('ix_polysphere_promo_code', 'promo_code'),
    )


class MowAndTrim(GameTableBase):
    __tablename__ = 'mow_and_trim'
    __table_args__ = (
        Index('ix_mow_and_trim_promo_code', 'promo_code'),
    )


class MudRacing(GameTableBase):
    __tablename__ = 'mud_racing'
    __table_args__ = (
        Index('ix_mud_racing_promo_code', 'promo_code'),
    )


class CafeDash(GameTableBase):
    __tablename__ = 'cafe_dash'
    __table_args__ = (
        Index('ix_cafe_dash_promo_code', 'promo_code'),
    )
