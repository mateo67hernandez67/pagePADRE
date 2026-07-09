import asyncio
from database import db

async def test():
    await db.command("ping")
    print("✅ Conectado a MongoDB Atlas")

asyncio.run(test())