import asyncio
import logging

from src.database.connection import connect_to_database
from src.repositories.level_rewards_repository import LevelRewardsRepository
from src.database.models.level_rewards import LevelRewardsModel

logger = logging.getLogger(__name__)

async def seed_rewards():
    logger.info("Iniciando seed de recompensas")
    db = await connect_to_database()

    rewards_repo = LevelRewardsRepository(db)

    # Certifique-se de importar o modelo no topo do arquivo:
    # from src.database.models.level_reward import LevelRewardsModel

    rewards_data = [
        LevelRewardsModel(
            level_required=1,
            role_id=1462942238584606782,
            role_name="[Lvl 1] Iniciado do Hello World"
        ),
        LevelRewardsModel(
            level_required=2,
            role_id=1462942465760956446,
            role_name="[Lvl 2] Aprendiz de Lógica"
        ),
        LevelRewardsModel(
            level_required=3,
            role_id=1462942550431240253,
            role_name="[Lvl 3] Caçador de Bugs"
        ),
        LevelRewardsModel(
            level_required=4,
            role_id=1462942852752343243,
            role_name="[Lvl 4] Feiticeiro do Script"
        ),
        LevelRewardsModel(
            level_required=5,
            role_id=1462942615891611854,
            role_name="[Lvl 5] Guardião do Git"
        ),
        LevelRewardsModel(
            level_required=6,
            role_id=1462942984201961724,
            role_name="[Lvl 6] Arquimago do Sistema"
        ),
        LevelRewardsModel(
            level_required=7,
            role_id=1462943050769891483,
            role_name="[Lvl 7] Mestre da Máquina"
        )
    ]

    for reward in rewards_data:
        logger.info(f"Criando recompensa {reward.role_name}")
        await rewards_repo.create(reward)

if __name__ == "__main__":
    # Roda o loop async
    asyncio.run(seed_rewards())