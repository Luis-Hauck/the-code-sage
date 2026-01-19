import asyncio
from pymongo import AsyncMongoClient

from src.database.connection import connect_to_database
from src.repositories.user_repository import UserRepository


async def start():
    db = await connect_to_database()

    item_repo = UserRepository(db)

    await item_repo.add_xp_coins(user_id=593837748566097931, xp=0, coins=1000)

asyncio.run(start())