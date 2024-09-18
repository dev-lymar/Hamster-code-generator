from sqlalchemy import Column, Integer, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class GameTableBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    promo_code = Column(Text, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ChainCube2048(GameTableBase):
    __tablename__ = 'chain_cube_2048'
    __table_args__ = (
        Index('ix_chain_cube_2048_promo_code', 'promo_code'),
        Index('ix_chain_cube_2048_created_at', 'created_at')
    )


class TrainMiner(GameTableBase):
    __tablename__ = 'train_miner'
    __table_args__ = (
        Index('ix_train_miner_promo_code', 'promo_code'),
        Index('ix_train_miner_created_at', 'created_at')
    )


class MergeAway(GameTableBase):
    __tablename__ = 'merge_away'
    __table_args__ = (
        Index('ix_merge_away_promo_code', 'promo_code'),
        Index('ix_merge_away_created_at', 'created_at')
    )


class TwerkRace3D(GameTableBase):
    __tablename__ = 'twerk_race_3d'
    __table_args__ = (
        Index('ix_twerk_race_3d_promo_code', 'promo_code'),
        Index('ix_twerk_race_3d_created_at', 'created_at')
    )


class Polysphere(GameTableBase):
    __tablename__ = 'polysphere'
    __table_args__ = (
        Index('ix_polysphere_promo_code', 'promo_code'),
        Index('ix_polysphere_created_at', 'created_at')
    )


class MowAndTrim(GameTableBase):
    __tablename__ = 'mow_and_trim'
    __table_args__ = (
        Index('ix_mow_and_trim_promo_code', 'promo_code'),
        Index('ix_mow_and_trim_created_at', 'created_at')
    )


class CafeDash(GameTableBase):
    __tablename__ = 'cafe_dash'
    __table_args__ = (
        Index('ix_cafe_dash_promo_code', 'promo_code'),
        Index('ix_cafe_dash_created_at', 'created_at')
    )


class Zoopolis(GameTableBase):
    __tablename__ = 'zoopolis'
    __table_args__ = (
        Index('ix_zoopolis_promo_code', 'promo_code'),
        Index('ix_zoopolis_created_at', 'created_at')
    )


class GangsWars(GameTableBase):
    __tablename__ = 'gangs_wars'
    __table_args__ = (
        Index('ix_gangs_wars_promo_code', 'promo_code'),
        Index('ix_gangs_wars_created_at', 'created_at')
    )


class TileTrio(GameTableBase):
    __tablename__ = 'tile_trio'
    __table_args__ = (
        Index('ix_tile_trio_promo_code', 'promo_code'),
        Index('ix_tile_trio_created_at', 'created_at')
    )


class FluffCrusade(GameTableBase):
    __tablename__ = 'fluff_crusade'
    __table_args__ = (
        Index('ix_fluff_crusade_promo_code', 'promo_code'),
        Index('ix_fluff_crusade_created_at', 'created_at')
    )


class StoneAge(GameTableBase):
    __tablename__ = 'stone_age'
    __table_args__ = (
        Index('ix_stone_age_promo_code', 'promo_code'),
        Index('ix_stone_age_created_at', 'created_at')
    )


class Bouncemasters(GameTableBase):
    __tablename__ = 'bouncemasters'
    __table_args__ = (
        Index('ix_bouncemasters_promo_code', 'promo_code'),
        Index('ix_bouncemasters_created_at', 'created_at')
    )


class HideBall(GameTableBase):
    __tablename__ = 'hide_ball'
    __table_args__ = (
        Index('ix_hide_ball_promo_code', 'promo_code'),
        Index('ix_hide_ball_created_at', 'created_at')
    )


class PinOutMaster(GameTableBase):
    __tablename__ = 'pin_out_master'
    __table_args__ = (
        Index('ix_pin_out_master_promo_code', 'promo_code'),
        Index('ix_pin_out_master_created_at', 'created_at')
    )


class CountMasters(GameTableBase):
    __tablename__ = 'count_masters'
    __table_args__ = (
        Index('ix_count_masters_promo_code', 'promo_code'),
        Index('ix_count_masters_created_at', 'created_at')
    )
