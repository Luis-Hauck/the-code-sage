from pymongo.database import Database
import logging
from src.database.models.user import UserModel, UserStatus
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

class UserRepository:
    """
    Repositório de operações com a coleção de usuários.
    """
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
            await self.collection.insert_one(user_data)


            logger.info(f'Usuário cadastrado: {user_model.username} | ID: {user_model.user_id}')
            return True

        except DuplicateKeyError:
            logger.warning(f"Tentativa de criar um usuário duplicado")
            return False

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
            if result.matched_count >0:
                logger.info(f'Status do user {user_id} atualizado para {status}')
                return True

            # Se chegou aqui, o usuário não existe.
            logger.warning(f'Tentativa de atualizar status de usuário inexistente: {user_id}')
            return False

        except Exception as e:
            logger.error(f'Falha ao atualizar os status do user {user_id}: {e}')
            return False

    async def add_xp_coins(self, user_id:int, xp:float, coins:float) -> bool:
        """
        Adicona XP e moedas ao usuário pelo ID.

        Args:
            user_id: ID do usuário
            xp: Valor de XP a ser adicionado
            coins: Valor de moedas a ser adicionado

        Returns:
            bool: True se atualizou com sucesso ou se não tiver dados a serem atualizados, False caso contrário
        """
        # Se o xp e moedas forem 0 não prosseguimos
        if not xp and not coins:
            return True
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

            logger.warning(f'Falha ao incrementar: Usuário {user_id} não encontrado.')
            return False


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

        except Exception as e:
            logger.error(f'Erro ao buscar usuário {user_id}: {e}', exc_info=True)
            return None

    async def equip_item(self, user_id: int, item_id: str) -> bool:
        """
        Equipa um item no usuário.
        Args:
            user_id: ID do usuário
            item_id: ID do item a ser equipado
        Returns:
            bool: True se ocorreu sucesso na operação,
                  False caso contrário.
        """

        try:
            result = await self.collection.update_one(
                {
                    '_id': user_id,
                    f'inventory.{item_id}': {'$gt': 0}  #
                },
                {'$set': {'equipped_item_id': item_id}}
            )

            if result.matched_count == 0:
                logger.info(f'Falha: Usuário {user_id} não possui o item {item_id} ou não existe.')
                return False

            # Se encontrou (matched > 0), é sucesso, mesmo que já estivesse equipado.
            if result.modified_count > 0:
                logger.info(
                    f'Usuário {user_id} equipou item {item_id}' )
            else:
                logger.info(f"Usuário {user_id} já estava com o item {item_id} equipado.")

            return True

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
            bool: True se a operação foi bem-sucedida. False em caso de erro.
        """

        try:
            # Remove o item equipado
            result = await self.collection.update_one(
                {'_id': user_id},
                {'$unset': {'equipped_item_id': ""}}
            )

            # Se matched_count == 0, o usuário não existe.
            if result.matched_count == 0:
                logger.info(f'Falha usuário {user_id} não encontrado para desequipar.')
                return False

            if result.modified_count > 0:
                logger.info(f'Usuário {user_id} desequipou o item com sucesso.')

            else:
                # Se modified_count == 0, ele já não tinha nada equipado.
                logger.info(f'Usuário {user_id} já não tinha item equipados.')

            return True

        except Exception as e:
            logger.error(f'Erro ao desequipar item de {user_id}: {e}', exc_info=True)
            return False

    async def add_item_to_inventory(self, user_id: int, item_id: str, quantity: int) -> bool:
        """
        Adiciona item(s) ao inventário do usuário.

        Args:
            user_id: ID do usuário
            item_id: ID do item a ser adicionado
            quantity: Quantidade a adicionar (deve ser positivo)

        Returns:
            bool: True se a operação foi bem-sucedida ou se a quantidade era zero. False em caso de erro.
        """
        if not quantity:
            return True

        # Valida quantidade positiva
        if quantity < 0:
            logger.warning(f'Tentativa de adicionar quantidade inválida ({quantity}) ao usuário {user_id}')
            return False
        try:
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

    async def remove_item_from_inventory(self, user_id: int, item_id: str, quantity: int = 1) -> bool:
        """
        Remove item(s) do inventário do usuário.

        Args:
            user_id: ID do usuário
            item_id: ID do item a ser removido
            quantity: Quantidade a remover (deve ser positivo)

        Returns:
            bool: True se removeu com sucesso, False caso contrário
        """
        if  quantity <= 0:
            logger.warning(f'Tentativa de remover quantidade inválida ({quantity}) do usuário {user_id}')
            return False
        try:
            # Pegamos os dados do usuário
            user = await self.get_by_id(user_id)

            if not user:
                logger.warning(f'Usuário {user_id} não encontrado ao tentar remover item')
                return False

            current_quantity = user.inventory.get(item_id, 0)

            # Verifica se tem quantidade suficiente
            if current_quantity < quantity:
                logger.warning(
                    f'Usuário {user_id} não tem {quantity}x item {item_id} '
                    f'(possui apenas {current_quantity})'
                )
                return False

            if current_quantity == quantity:
                # Se vai remover tudo, remove a chave do dicionário
                operation = {'$unset': {f'inventory.{item_id}': ''}}
            else:
                # Senão, apenas decrementa
                operation = {'$inc': {f'inventory.{item_id}': -quantity}}

            # Executamos a operação escolhida
            result = await self.collection.update_one({'_id': user_id}, operation)

            if result.modified_count > 0:
                logger.info(f'Usuário {user_id}:removeu {quantity}x o item {item_id} ')
                return True

            logger.warning(f'Falha ao remover item do inventário do usuário {user_id}')
            return False

        except Exception as e:
            logger.error(f'Erro ao remover item {item_id} do inventário do usuário {user_id}: {e}', exc_info=True)
            return False

    async def add_role(self, user_id: int, role_id: int) -> bool:
        """
        Adiciona role ao usuário
        Args:
            user_id: ID do usuário
            role_id: ID do item a ser removido
        Returns:
            bool: True se adcionou com sucesso, False caso contrário
        """
        try:
            # Adciona o role caso o usuário não tenha
            result = await self.collection.update_one(
                {'_id': user_id},
                {'$addToSet': {'role_ids': role_id}}
            )
            # Se a operação foi realizada
            if result.modified_count > 0:
                logger.info(f'O cargo {role_id} foi adcionado ao usuário {user_id}')
            else:
                # Se não modificou o cargo existia
                logger.info(f'Usuário {user_id} já possuia o cargo {role_id} ')

            # Retorna True se o comando foi processado com sucesso pelo banco
            return result.acknowledged

        except Exception as e:
            logger.error(f'Erro ao adicionar role: {e} ao usuário {user_id}', exc_info=True)
            return False

    async def remove_role(self, user_id: int, role_id: int) -> bool:
        """
        Remove a role do usuário

        Args:
            user_id:ID do usuário
            role_id:ID do cargo a ser removido
        Returns:
            bool: True se removeu com sucesso, False caso contrário

        """

        try:
            # Remove a role
            result =  await self.collection.update_one(
                {'_id': user_id},
                {'$pull': {'role_ids': role_id}}
            )

            if result.modified_count > 0:
                logger.info(f'Role {role_id} removida com sucesso do usuário {user_id}')
                return True

            logger.info(f'Usuário {user_id} não possuia o cargo {role_id} para ser removido!')
            return False

        except Exception as e:
            logger.error(f'Erro aoremover role: {e} ao usuário {user_id}', exc_info=True)
            return False

