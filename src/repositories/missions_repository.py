from pymongo.database import Database
import logging
from src.database.models.mission import MissionModel, MissionStatus, EvaluationRank, EvaluatorModel
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

    async def add_participant(self, mission_id:int, evaluator_model: EvaluatorModel) -> bool:
        """
        Adciona um participante a missão caso ele ainda não esteja lá.
        :param mission_id: ID da missão que o usuário vai participar.
        :param evaluator_model: Usuário que vai ser avaldiado, sendo um objeto do tipo EvaluatorModel.
        :return: True caso o participante seja adicioando/já esatva adcioando a missão, e False caso contrário
        """
        try:
            evaluator_data = evaluator_model.model_dump()
            result = await self.collection.update_one(
                {
                    '_id': mission_id,
                    'evaluators.user_id': {'$ne': evaluator_model.user_id}
                },
                {
                    '$push':{'evaluators': evaluator_data}
                }

            )

            if result.modified_count > 0:
                logger.info(f'O participante {evaluator_model.user_id} foi adicionado a missão {mission_id}')
                return True

            mission_exists = await self.collection.count_documents({'_id':mission_id}, limit=1)

            if mission_exists:
                logger.info(f'O participante {evaluator_model.user_id} já estava participando da missão.')
                return True

            logging.warning(f'Tentativa de adicionar um participante a uma missão inexistente')
            return False

        except Exception as e:
            logger.error(f'Falha ao adcionar o participante {evaluator_model.user_id} a missão {mission_id}: {e}')
            return False


    async def update_evaluator(self,
                                  mission_id:int,
                               evaluator_model: EvaluatorModel,


                                  ) -> bool:
        """
        ATUALIZA os dados de alguém que já foi avaliado
        :param mission_id: Missão que o usuário foi avaliado;
        :param evaluator_model: Usuário que vai ser atualizado na missão, sendo um objeto do tipo EvaluatorModel.
        :return: True caso tenha conseguido registrar, e False caso o contrário.
        """
        try:

            result = await self.collection.update_one(
                {'_id':mission_id,
                 'evaluators.user_id': evaluator_model.user_id
                 },
            {
                '$set':{
                    'evaluators.$.level_at_time':evaluator_model.user_level_at_time,
                    'evaluators.$.rank': evaluator_model.rank,
                    'evaluators.$.coins_earned': evaluator_model.coins_earned,
                    'evaluators.$.xp_earned': evaluator_model.xp_earned,
                    'evaluators.$.evaluate_at': evaluator_model.evaluate_at

                    }
                }
            )

            if result.matched_count > 0:
                logger.info(f'O usuário {evaluator_model.user_id} foi avaliado com sucesso na missão {mission_id}, recebendo {evaluator_model.xp_earned}xp e {evaluator_model.coins_earned} moedas')
                return True

            logger.warning(f'Falha ao avaliar o usuário {evaluator_model.user_id} na missão {mission_id}')
            return False

        except Exception as e:
            logger.error(f'Erro ao tentar avaliar o usuário {evaluator_model.user_id} na missão {mission_id}: {e}')
            return False
