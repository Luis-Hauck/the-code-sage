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
        """Busca a maior recompensa aplicável para o nível atual.

        Args:
            current_level (int): Nível atual.

        Returns:
            Optional[LevelRewardsModel]: O modelo encontrado ou None se não houver recompensa aplicável.
        """
        try:
            result = await self.collection.find_one(
                {'level_required': {'$lte': current_level}},
                sort=[('level_required', -1)]
            )

            if result:
                logger.info(f"Nível atual: {current_level}, Maior recompensa {result['role_name']}")
                return LevelRewardsModel(**result)

            logger.warning(f'Não foi possível identificar o modelo para o nível {current_level}.')
            return None

        except Exception as e:
            logger.error(f'Erro ao buscar recompensa de nível: {e}', exc_info=True)

    async def get_all_reward_role_ids(self) -> List[int]:
        """Obtém apenas os IDs de todos os cargos de recompensa.

        Returns:
            List[int]: Lista contendo somente os role IDs de recompensa.
        """
        try:
            cursor = self.collection.find(
                {},
                {'role_id': 1, '_id': 0}


            )
            docs = await cursor.to_list(length=None)

            # Extraímos os IDs da lista de dicionários
            return [doc['role_id'] for doc in docs]

        except Exception as e:
            logger.error(f"Erro ao listar cargos de recompensa: {e}", exc_info=True)
            return []

    async def create(self, reward_model: LevelRewardsModel) -> bool:
        """
        Cria uma nova regra de recompensa (Para Admin/Seed).

        Args:
            reward_model (LevelRewardsModel): Modelo da regra de recompensa a ser criada.
        Returns:
            bool: True caso tenha criado, False caso contrário
        """
        try:
            data = reward_model.model_dump(by_alias=True, exclude_none=True)
            await self.collection.insert_one(data)
            logger.info(f'Sucesso ao criar recompensa {reward_model.role_name}.')
            return True
        except DuplicateKeyError:
            logger.error(f'Erro ao criar a recompensa, pois ela já existe')
            return False
        except Exception as e:
            logger.error(f"Erro ao criar recompensa: {e}", exc_info=True)
            return False