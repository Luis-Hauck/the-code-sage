from pymongo.database import Database
import logging
from src.database.models.mission import MissionModel, MissionStatus
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MissionRepository:

    def __init__(self, db:Database):
        # Cria a conexão com a coleção missions
        self.collection = db.missions

    def create(self, mission_model:MissionModel) -> bool:
        """
        Cria uma nova missão
        :param mission_model: modelo da missão a ser criado
        :return: True se a missão foi criada, False caso contrário
        """

        try:
            mission_data = mission_model.model_dump(by_alias=True)
            self.collection.insert_one(mission_data)

            logger.info(f'Missão com o id:{mission_model.mission_id} criada pelo user {mission_model.creator_id}')

            return True

        except DuplicateKeyError:
            logger.warning(f"Erro, tentativa de criar uma nova missão")
            return False

        except Exception as e:
            logger.error(f'Erro ao criar a missão de id{mission_model.id}: {e}')
            return False

    async def get_by_id(self, mission_id: int):
        """
        Busca uma missão pelo ID.
        :param mission_id: ID da missão.
        :return: MissionModel se encontrado, None se não encontrado ou em caso de erro.
        """
        try:
            mission_data = self.collection.find_one({'_id':mission_id})

            if not mission_data:
                logger.info('Item não encontrado')
                return None

            return MissionModel(**mission_data)

        except Exception as e:
            logger.error(f'Erro ao buscar a missão de ID {mission_id}: {e}', exc_info=True)
            return None

    async def update_status(self, mission_id:int, new_status: MissionStatus, completed_at: Optional[datetime] = None) -> bool:
        """
        Atualiza os status da missão.
        :param mission_id: ID da missão.
        :param new_status: Status da missão.
        :param completed_at: data que a missão foi concluída.
        :return: True se atualizou com sucesso, False caso contrário.
        """

        try:
            update_data: Dict[str, Any] = {'status': new_status}

            if completed_at:
                update_data['completed_at'] = completed_at

            result = self.collection.update_one(
                {'_id':mission_id},
                {'$set': update_data}
            )

            if result.matched_count > 0:
                logger.info(f'A missão com ID: {mission_id} foi definida como {update_data['status']}.')
                return True

            logger.warning(f'Tentativa de atualizar uma missão inexistente: {mission_id}.')
            return False

        except Exception as e:
            logger.info(f'Erro ao atualizar a missão com ID:{mission_id}: {e}')
            return False
            





