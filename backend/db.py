import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from dotenv import load_dotenv

from backend.models import User, OrchestrationRun

load_dotenv()

logger = logging.getLogger(__name__)

MONGO_URL = os.getenv("MONGO_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

if not MONGO_URL:
    raise ValueError("MONGO_URL missing in .env")

if not DATABASE_NAME:
    raise ValueError("DATABASE_NAME missing in .env")

client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]


async def init_db():
    logger.info("Initializing MongoDB...")
    await init_beanie(
        database=db,
        document_models=[User, OrchestrationRun]
    )
    logger.info("MongoDB initialized successfully")
