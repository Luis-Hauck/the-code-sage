from pymongo.database import Database
import logging
from src.database.models.item import ItemsModel

logger = logging.getLogger(__name__)

class ItemsRepository:
    """Repositório de ações coma coleçaõ de items"""

    def __init__(self, db:Database):
        # Conexão com a a coleção de itens
        self.collection = db.items

    def create(self):
