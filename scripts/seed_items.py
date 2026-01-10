import asyncio
from pymongo import AsyncMongoClient
import logging

from src.database.models.item import ItemModel, ItemType
from src.database.models.effects import AddXpEffect, CoinBoostPassive, AddCoinsEffect, XpBoostPassive, GiveRoleEffect
from src.database.connection import connect_to_database
from src.repositories.item_repository import ItemRepository

logger = logging.getLogger(__name__)

async def seed_items():
    logger.info("Iniciando seed de itens")
    db = await connect_to_database()

    item_repo = ItemRepository(db)

    items_data = [
        ItemModel(
            _id=1,
            name='Café Expresso Compilado',
            description='Um café forte que te mantém acordado para codar mais. Recupera energia mental.',
            price=100,
            item_type=ItemType.CONSUMABLE,
            effect=AddXpEffect(type='add_xp', amount=100),
            passive_effects=[]
        ),
        ItemModel(
            _id=4,
            name='Teclado Mecânico RGB',
            description='O barulho dos switches azuis aumenta sua produtividade (e irrita os vizinhos).',
            price=500,
            item_type=ItemType.EQUIPPABLE,
            effect=None,
            passive_effects=[CoinBoostPassive(type='coin_boost', multiplier=0.1)]
        ),
        ItemModel(
            _id=10,
            name='Certificado "Na Minha Máquina Funciona"',
            description='O selo de garantia de todo programador.',
            price=2000,
            item_type=ItemType.ROLE,
            effect=GiveRoleEffect(type='role_effect', role_id=1459606476636160172),
            passive_effects=[]
        )


    ]

    for item in items_data:
        logger.info(f"Criando item {item.name}")
        await item_repo.create(item)

if __name__ == "__main__":
    # Roda o loop async
    asyncio.run(seed_items())