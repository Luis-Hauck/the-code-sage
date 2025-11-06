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
            result  = await self.collection.insert_one(item_data)

            logging.info('Item cadastrado com sucesso')
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