import asyncio
from pymongo import AsyncMongoClient
import os

MONGO_URI = os.getenv('MONGO_URI')

async def main():
    try:
        print(f"Connecting to {MONGO_URI}...")
        client = AsyncMongoClient(MONGO_URI)
        await client.admin.command('ping')
        print("Connected and pinged!")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == '__main__':
    asyncio.run(main())
