from pymongo.database import Database
from typing import Optional, List
import logging
from pymongo.errors import DuplicateKeyError


from src.database.models.level_rewards import LevelRewardsModel


logger = logging.getLogger(__name__)

class LevelRewardsRepository:

    def __init__(self, db: Database):
        self.collection = db.level_rewards

    async def get_role_for_level(self, current_level: int) -> Optional[LevelRewardsModel]:
        """
        Busca a maior recompensa aplicável para o nível atual.
        Retorna o Modelo se encontrar, ou None.
        :param current_level: Nível atual.
        :return:Retorna o Modelo se encontrar, ou None.
        """
        try:
            result =  self.collection.find_one(
                {'level_required': {'$lte': current_level}},
                sort=[('level_required', -1)]
            )

            if result:
                return LevelRewardsModel(**result)
            return None

        except Exception as e:
            logger.error(f'Erro ao buscar recompensa de nível: {e}', exc_info=True)

    async def get_all_reward_role_ids(self) -> List[int]:
        """
        Retorna uma lista com APENAS os IDs de todos os cargos de recompensa.
        """
        try:
            cursor = self.collection.find_one(
                {},
                {'role_id':1, 'id': 0}


            )
            return [id['role_id'] async for doc in cursor]

        except Exception as e:
            logger.error(f"Erro ao listar cargos de recompensa: {e}", exc_info=True)
            return []

    async def create_reward(self, model: LevelRewardsModel) -> bool:
        """
        Cria uma nova regra de recompensa (Para Admin/Seed).
        """
        try:
            data = model.model_dump(by_alias=True, exclude_none=True)
            await self.collection.insert_one(data)
            return True
        except DuplicateKeyError:
            return False
        except Exception as e:
            logger.error(f"Erro ao criar recompensa: {e}", exc_info=True)
            return False