import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load from backend/.env
load_dotenv(dotenv_path="backend/.env")

async def test_mongo():
    uri = os.getenv("MONGODB_URL")
    db_name = os.getenv("DATABASE_NAME", "acrosome_db")
    print(f"Testing connection to: {uri}")
    
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth.
        await client.admin.command('ismaster')
        print("[SUCCESS] Successfully connected to MongoDB Atlas!")
        
        db = client[db_name]
        collections = await db.list_collection_names()
        print(f"[SUCCESS] Access to database '{db_name}' verified.")
        print(f"Existing collections: {collections}")
        
    except Exception as e:
        print(f"[ERROR] Connection failed: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(test_mongo())
