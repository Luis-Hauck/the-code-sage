
from pymongo.synchronous.database import Database
from pydantic import ValidationError
import logging

from src.database.models.user import UserModel, UserStatus

logger = logging.getLogger('__name__')

class UserRepository:
    def __init__(self, db: Database):
        # Conexão com a coleção User
        self.collection = db.users

    async def create(self, user_model:UserModel) -> bool:
        """
        Cria um novo usuário no banco de dados.

        Args:
            user_model: Modelo do usuário a ser criado

        Returns:
            bool: True se criou com sucesso, False caso contrário
        """

        try:
            user_data = user_model.model_dump(by_alias=True)
            result = await self.collection.insert_one(user_data)

            if result.inserted_id:
                logger.info('Usuário cadastrado')
                return True

        except Exception as e:
            logger.error(f'Erro inesperado ao criar o usuário: {e}', exc_info=True)
            return False

    async def update_status(self, user_id: int, status: UserStatus) -> bool:
        """
        Atualiza o status de um usuário.

        Args:
            user_id: ID do usuário
            status: Novo status (ACTIVE, INACTIVE, BANNED, MUTED)

        Returns:
            bool: True se atualizou com sucesso, False caso contrário
        """

        try:
            result = await self.collection.update_one(
                {'_id': user_id},
                {'$set': {'status': status}}
            )

            if result.modified_count > 0:
                logger.info(f'Status do user {user_id} atualizado!')
                return True

        except Exception as e:
            logger.error(f'Falha ao atualizar os status do user {user_id}: {e}')
            return False

    async def add_xp_coins(self, user_id:int, xp:float, coins:float):
        try:
            result = await self.collection.update_one(
                {'_id': user_id},
                {
                    '$inc': {
                    'xp':xp,
                    'coins':coins
                    }
                }
            )
            if result.modified_count > 0:
                logger.info(f'XP e moedas incrementadas para user {user_id}')
                return True

        except Exception as e:
            logger.error(f'Falha ao incremenatar xp e moedas ao user {user_id}: {e}')
            return False





