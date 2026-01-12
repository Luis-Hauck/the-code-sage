from pymongo.database import Database
import logging
from pymongo.errors import DuplicateKeyError
from typing import List

from src.database.models.item import ItemModel


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

    async def get_all(self) -> List[ItemModel]:
        """
        Busca todos os itens cadastrados
        :return: Retorna uma lista com 100 itens cadastrados
        """
        try:
            logger.info(f'Buscando todos os itens cadastrados')
            result= await self.collection.find({})
            items_data = await result.to_list(length=100)

            # Converte cada dicionário do Mongo em um objeto ItemModel
            return [ItemModel(**item) for item in items_data]

        except Exception as e:
            logger.error(f'Erro ao buscar todos os itens: {e}', exc_info=True)
            return []

    async def upsert(self, item_model: ItemModel):
        """
        Cria ou Atualiza um item (Se o ID já existe, atualiza os dados).
        :param item_model: Modelo de item a ser criado
        :return: True se criou com sucesso, False caso contrário
        """
        try:

            item_data = item_model.model_dump(by_alias=True)

            # Procura pelo _id. Se achar, substitui. Se não achar, cria.
            await self.collection.replace_one(
                {'_id': item_model.item_id},
                item_data,
                upsert=True)
            logger.info(f'Sucesso no upsert do item {item_model.name}!')
            return True

        except Exception as e:
            logger.error(f'Erro no upsert do item{item_model.name} item: {e}', exc_info=True)
            return False




