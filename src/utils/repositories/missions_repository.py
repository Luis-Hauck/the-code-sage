from pymongo.database import Database
import logging
from src.database.models.mission import MissionModel, MissionStatus, EvaluationRank
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MissionRepository:

    def __init__(self, db:Database):
        # Cria a conexão com a coleção missions
        self.collection = db.missions

    async def create(self, mission_model:MissionModel) -> bool:
        """
        Cria uma nova missão
        :param mission_model: modelo da missão a ser criado
        :return: True se a missão foi criada, False caso contrário
        """

        try:
            mission_data = mission_model.model_dump(by_alias=True)
            await self.collection.insert_one(mission_data)

            logger.info(f'Missão com o id:{mission_model.mission_id} criada pelo user {mission_model.creator_id}')

            return True

        except DuplicateKeyError:
            logger.warning(f"Erro, tentativa de criar uma nova missão")
            return False

        except Exception as e:
            logger.error(f'Erro ao criar a missão de id{mission_model.mission_id}: {e}')
            return False

    async def get_by_id(self, mission_id: int):
        """
        Busca uma missão pelo ID.
        :param mission_id: ID da missão.
        :return: MissionModel se encontrado, None se não encontrado ou em caso de erro.
        """
        try:
            mission_data = await self.collection.find_one({'_id':mission_id})

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

            result = await self.collection.update_one(
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


    async def register_evaluation(self,
                                  user_id:int,
                                  mission_id:int,
                                  score:int,
                                  rank:EvaluationRank,
                                  level_at_time:int,
                                  xp:int,
                                  coins:int
                                  ) -> bool:
        """
        Registra uma avaliação com base no ID da missão
        :param user_id: Usuário a receber a avaliação.
        :param mission_id: Missão que o usuário foi avaliado;
        :param level_at_time: level do usuário ao receber a avaliação;
        :param rank: Rank de S a E da missão.
        :param score: Nota de 0-5 da missão
        :param coins: Moedas ganhas.
        :param xp: XP ganho.
        :return: True caso tenha conseguido registrar, e False caso o contrário.
        """
        try:
            result = await self.collection.update_one(
                {'_id':mission_id,
                 'evaluators.user_id': user_id
                 },
            {
                '$set':{
                    'evaluators.$.user_id':user_id,
                    'evaluators.$.level_at_time': level_at_time,
                    'evaluators.$.rank': rank,
                    'evaluators.$.score': score,
                    'evaluators.$.coins': coins,
                    'evaluators.$.xp': xp,

                    }
                }
            )

            if result.matched_count > 0:
                logger.info(f'O usuário {user_id} foi avaliado com sucesso na missão {mission_id}, recebendo {xp}xp e {coins} moedas')
                return True

            logger.warning(f'Falha ao avaliar o usuário {user_id} na missão {mission_id}')
            return False

        except Exception as e:
            logger.error(f'Erro ao tentar avaliar o usuário {user_id} na missão {mission_id}: {e}')
            return False
