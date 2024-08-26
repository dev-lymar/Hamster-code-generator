from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class GameTableBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    promo_code = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class BikeRide3D(GameTableBase):
    __tablename__ = 'bike_ride_3d'


class ChainCube2048(GameTableBase):
    __tablename__ = 'chain_cube_2048'


class TrainMiner(GameTableBase):
    __tablename__ = 'train_miner'


class MergeAway(GameTableBase):
    __tablename__ = 'merge_away'


class TwerkRace3D(GameTableBase):
    __tablename__ = 'twerk_race_3d'


class Polysphere(GameTableBase):
    __tablename__ = 'polysphere'


class MowAndTrim(GameTableBase):
    __tablename__ = 'mow_and_trim'


class MudRacing(GameTableBase):
    __tablename__ = 'mud_racing'
