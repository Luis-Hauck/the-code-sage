
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

    async def get_by_id(self, user_id:int):
        """
        Busca um um usuário pelo id

        Args:
        user_id: ID do usuário a ser buscado
        Returns:

        UserModel se encontrado, None se não encontrado ou em caso de erro
        """
        try:
            user_data = await self.collection.find_one({'_id': user_id})

            if not user_data:
                logger.info(f'Usuário {user_id} não encontrado')
                return None
            return UserModel(**user_data)

        except ValidationError as e:
            logger.error(f'Dados inválidos para o usuário {user_id}: {e}')
            return None

        except Exception as e:
            logger.error(f'Erro ao buscar usuário {user_id}: {e}', exc_info=True)
            return None

    async def equip_item(self, user_id: int, item_id: int) -> bool:
        """
        Equipa um item no usuário.

        Args:
            user_id: ID do usuário
            item_id: ID do item a ser equipado

        Returns:
            bool: True se equipou com sucesso, False caso contrário
        """
        try:
            # Verifica se o usuário existe
            user = await self.get_by_id(user_id)

            if not user:
                logger.warning(f'Usuário {user_id} não encontrado ao tentar equipar item')
                return False

            # Verifica se o item está no inventário
            if item_id not in user.inventory:
                logger.warning(f'Item {item_id} não está no inventário do usuário {user_id}')
                return False

            # Verifica se o item já está equipado (opcional, mas recomendado)
            if user.equipped_item_id == item_id:
                logger.info(f'Item {item_id} já está equipado no usuário {user_id}')
                return True

            # Atualiza o item equipado
            result = await self.collection.update_one(
                {'_id': user_id},
                {'$set': {'equipped_item_id': item_id}}
            )

            if result.modified_count > 0:
                previous_item = user.equipped_item_id
                logger.info(
                    f'Usuário {user_id} equipou item {item_id} '
                    f'(anterior: {previous_item or "nenhum"})'
                )
                return True

            logger.warning(f'Falha ao equipar item {item_id} para usuário {user_id}')
            return False

        except Exception as e:
            logger.error(
                f'Erro inesperado ao equipar item {item_id} para usuário {user_id}: {e}',
                exc_info=True
            )
            return False

    async def unequip_item(self, user_id: int) -> bool:
        """
        Remove o item equipado do usuário.

        Args:
            user_id: ID do usuário
        Returns:
            bool: True se desequipou com sucesso, False caso contrário
        """

        try:
            # Verifica se o usuário existe e tem item equipado
            user = await self.get_by_id(user_id)

            if not user:
                logger.warning(f'Usuário {user_id} não encontrado ao tentar desequipar item')
                return False

            if user.equipped_item_id is None:
                logger.info(f'Usuário {user_id} já não tem item equipado')
                return True

            # Salva o ID do item que será desequipado para o log
            item_id = user.equipped_item_id

            # Remove o item equipado
            result = await self.collection.update_one(
                {'_id': user_id},
                {'$set': {'equipped_item_id': None}}
            )

            if result.modified_count > 0:
                logger.info(f'Usuário {user_id} desequipou item {item_id}')
                return True

            logger.warning(f'Nenhum item para desequipar para o usuário {user_id}')
            return False

        except Exception as e:
            logger.error(f'Erro ao desequipar item de {user_id}: {e}', exc_info=True)
            return False

    async def add_item_to_inventory(self, user_id: int, item_id: int, quantity: int = 1) -> bool:
        """
        Adiciona item(s) ao inventário do usuário.

        Args:
            user_id: ID do usuário
            item_id: ID do item a ser adicionado
            quantity: Quantidade a adicionar (deve ser positivo)

        Returns:
            bool: True se adicionou com sucesso, False caso contrário
        """
        try:
            # Valida quantidade positiva
            if quantity <= 0:
                logger.warning(f'Tentativa de adicionar quantidade inválida ({quantity}) ao usuário {user_id}')
                return False

            # Verifica se o usuário existe
            user = await self.get_by_id(user_id)

            if not user:
                logger.warning(f'Usuário {user_id} não encontrado ao tentar adicionar item')
                return False

            # Adiciona ao inventário
            result = await self.collection.update_one(
                {'_id': user_id},
                {'$inc': {f'inventory.{item_id}': quantity}}
            )

            if result.modified_count > 0:
                logger.info(f'Usuário {user_id} recebeu {quantity}x item {item_id}')
                return True

            logger.warning(f'Falha ao adicionar item ao inventário do usuário {user_id}')
            return False

        except Exception as e:
            logger.error(f'Erro ao adicionar item {item_id} ao inventário do usuário {user_id}: {e}', exc_info=True)
            return False

    async def remove_item_from_inventory(self, user_id: int, item_id: int, quantity: int = 1) -> bool:
        """
        Remove item(s) do inventário do usuário.

        Args:
            user_id: ID do usuário
            item_id: ID do item a ser removido
            quantity: Quantidade a remover (deve ser positivo)

        Returns:
            bool: True se removeu com sucesso, False caso contrário
        """
        try:
            # Valida quantidade positiva
            if quantity <= 0:
                logger.warning(f'Tentativa de remover quantidade inválida ({quantity}) do usuário {user_id}')
                return False

            # Verifica se o usuário existe
            user = await self.get_by_id(user_id)

            if not user:
                logger.warning(f'Usuário {user_id} não encontrado ao tentar remover item')
                return False

            # Verifica se o item está no inventário
            current_quantity = user.inventory.get(item_id, 0)

            if current_quantity <= 0:
                logger.warning(f'Usuário {user_id} não possui o item {item_id} no inventário')
                return False

            # Verifica se tem quantidade suficiente
            if current_quantity < quantity:
                logger.warning(
                    f'Usuário {user_id} não tem {quantity}x item {item_id} '
                    f'(possui apenas {current_quantity})'
                )
                return False

            # Se vai remover tudo, remove a chave do dicionário
            if current_quantity == quantity:
                result = await self.collection.update_one(
                    {'_id': user_id},
                    {'$unset': {f'inventory.{item_id}': ''}}
                )
                action = 'removido completamente'
            else:
                # Senão, apenas decrementa
                result = await self.collection.update_one(
                    {'_id': user_id},
                    {'$inc': {f'inventory.{item_id}': -quantity}}
                )
                action = f'decrementado de {current_quantity} para {current_quantity - quantity}'

            if result.modified_count > 0:
                logger.info(f'Usuário {user_id}: {quantity}x item {item_id} {action}')
                return True

            logger.warning(f'Falha ao remover item do inventário do usuário {user_id}')
            return False

        except Exception as e:
            logger.error(f'Erro ao remover item {item_id} do inventário do usuário {user_id}: {e}', exc_info=True)
            return False


