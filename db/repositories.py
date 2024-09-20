import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    AmongWaterr,
    Bouncemasters,
    CafeDash,
    ChainCube2048,
    CountMasters,
    FactoryWorld,
    FluffCrusade,
    GangsWars,
    HideBall,
    InfectedFrontier,
    MergeAway,
    MowAndTrim,
    PinOutMaster,
    Polysphere,
    StoneAge,
    TileTrio,
    TrainMiner,
    TwerkRace3D,
    Zoopolis,
)

logger = logging.getLogger(__name__)


class GamePromoRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_code(self, code_data: str, game_name: str):
        """Save the promo code to the appropriate table"""
        try:
            table_mapping = {
                'Chain Cube 2048': ChainCube2048,
                'Train Miner': TrainMiner,
                'Merge Away': MergeAway,
                'Twerk Race 3D': TwerkRace3D,
                'Polysphere': Polysphere,
                'Mow and Trim': MowAndTrim,
                'Cafe Dash': CafeDash,
                'Zoopolis': Zoopolis,
                'Gangs Wars': GangsWars,
                'Fluff Crusade': FluffCrusade,
                'Tile Trio': TileTrio,
                'Stone Age': StoneAge,
                'Bouncemasters': Bouncemasters,
                'Hide Ball': HideBall,
                'Pin Out Master': PinOutMaster,
                'Count Masters': CountMasters,
                'Infected Frontier': InfectedFrontier,
                'Among Waterr': AmongWaterr,
                'Factory World': FactoryWorld,
            }
            GameTable = table_mapping.get(game_name)
            if GameTable:
                table_entry = GameTable(promo_code=code_data)
                self.session.add(table_entry)
                await self.session.commit()
                logger.info(
                    f"🔑 `KEY` | `{code_data[:12]}` | Saved in table `{game_name.replace(' ', '_').lower()}` 🔑"
                )
        except Exception as e:
            logger.critical(f" ❌ Failed to save promo code `{code_data[:12]}` for game `{game_name}`: {e}")
            await self.session.rollback()
