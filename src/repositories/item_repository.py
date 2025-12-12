from pymongo.database import Database
import logging
from src.database.models.item import ItemModel
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

class ItemRepository:
    """Repositório de ações coma coleçaõ de items"""

    def __init__(self, db:Database):
        # Conexão com a a coleção de itens
        self.collection = db.items

    async def create(self, item_model:ItemModel) -> bool:
        """
        Cria um novo item no banco de dados.

        Args:
            item_model: Modelo de item a ser criado

        Returns:
            bool: True se criou com sucesso, False caso contrário
        """

        try:
            item_data = item_model.model_dump(by_alias=True)
            await self.collection.insert_one(item_data)

            logging.info(f'Item: {item_model.name} | ID:{item_model.item_id} cadastrado com sucesso')
            return True

        except DuplicateKeyError:
            logger.warning(f"Erro, tentativa de criar um usuário duplicado")
            return False

        except Exception as e:
            logger.error(f'Erro inesperado ao criar o item: {e}')
            return False

    async def get_by_id(self, item_id:int):
        """
        Busca um item pelo ID.
        :param item_id: ID do item a ser buscado.
        :return: ItemModel se encontrado, None se não encontrado ou em caso de erro.
        """

        try:
            item_data = await self.collection.find_one({'_id':item_id})

            if not item_data:
                logging.info('Usuário não encontrado')
                return None

            return ItemModel(**item_data)

        except Exception as e:
            logger.error(f'Erro ao buscar o ID {item_id}: {e}', exc_info=True)
            return None

    async def update_price(self, item_id: int, new_price: int) -> bool:
        """
        Atualiza o preço d eum item
        :param item_id: ID do item.
        :param new_price: Novo preço do item.
        :return: True se a operação foi realizada e False caso contrário.
        """

        try:
            result = await self.collection.update_one(
                {'_id': item_id},
                {'$set':{'price':new_price}}
            )

            if result.matched_count >  0:
                logger.info(f'Preço do item {item_id} alterado para {new_price}')
                return True

            logger.warning(f'Tentativa de atualizar o preço de item inexistente: {item_id}')
            return False


        except Exception as e:
            logger.warning(f'Falha ao atualizar o preço do item: {item_id}: {e}')
            return False

    async def delete(self, item_id: int) -> bool:
        """
        Deleta um item
        :param item_id: ID do item
        :return: True se a operação foi realizada e False caso contrário.
        """
        try:
            result = await self.collection.delete_one({'_id': item_id})

            if result.deleted_count >0:
                logger.info(f'item com id{item_id} excluído com sucesso.')
                return True

            logger.warning(f'Item {item_id} não encontrado para deletar')
            return False

        except Exception as e:
            logger.error(f'Erro ao deletar item {item_id}: {e}', exc_info=True)
            return False
